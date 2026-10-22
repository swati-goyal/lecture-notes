#!/usr/bin/env python3
"""
lecture_notes.py — turn a YouTube lecture into study notes: a Markdown page in this repo, plus a Notion page.

Pipeline:
  1. Fetch the video's transcript (captions) from YouTube.
  2. Ask Claude to write structured notes, optionally weaving in your own notes.
  3. Save them as photonics/<date>-<title>.md in this repo (ready to commit and push),
     and create a Notion page if Notion is set up. Every timestamp links back to that
     moment in the video. No transcript unless you ask.

Usage:
  python lecture_notes.py "https://www.youtube.com/watch?v=VIDEO_ID"
  python lecture_notes.py URL --my-notes my_notes.txt     # merge your own notes
  python lecture_notes.py URL --lang de en                # prefer German captions (notes stay English)
  python lecture_notes.py URL --notes-lang German         # write the notes in German
  python lecture_notes.py URL --with-transcript           # also attach the full transcript
  python lecture_notes.py URL --folder optics             # repo folder for this run
  python lecture_notes.py URL --no-notion                 # Markdown page only this time
  python lecture_notes.py URL --dry-run                   # print notes, publish nowhere
  python lecture_notes.py --next PLAYLIST_URL             # next playlist video without notes yet
  python lecture_notes.py --next PLAYLIST_URL --start 2   # ...ignoring videos before position 2

Environment (put these in a .env file next to this script, or export them):
  ANTHROPIC_API_KEY       your Claude API key
  NOTION_TOKEN            your Notion integration secret
  NOTION_PARENT_PAGE_ID   the Notion page the notes are created under
  CLAUDE_MODEL            optional; defaults to claude-sonnet-5-5
  YT_PROXY_URL            optional; proxy for YouTube transcript requests (needed on cloud servers
                          such as GitHub Actions, which YouTube often blocks)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def load_dotenv(path: Path) -> None:
    """Minimal .env loader so you don't need python-dotenv."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


DEFAULT_MODEL = "claude-sonnet-5-5"

# ---------------------------------------------------------------------------
# 1. YouTube transcript
# ---------------------------------------------------------------------------


def extract_video_id(url_or_id: str) -> str:
    """Accepts watch URLs, youtu.be links, /shorts/, /live/, /embed/ or a bare ID."""
    s = url_or_id.strip()
    if re.fullmatch(r"[\w-]{11}", s):
        return s
    u = urlparse(s)
    host = (u.hostname or "").lower()
    if host.endswith("youtu.be"):
        return u.path.lstrip("/")[:11]
    if "youtube" in host:
        qs = parse_qs(u.query)
        if "v" in qs:
            return qs["v"][0][:11]
        m = re.match(r"^/(shorts|live|embed|v)/([\w-]{11})", u.path)
        if m:
            return m.group(2)
    raise ValueError(f"Couldn't find a YouTube video ID in: {url_or_id}")


def fetch_transcript(video_id: str, languages: list[str]) -> list[dict]:
    """Returns [{'text', 'start', 'duration'}, ...]. Falls back to any available language."""
    from youtube_transcript_api import YouTubeTranscriptApi

    proxy = os.environ.get("YT_PROXY_URL")
    if proxy:
        from youtube_transcript_api.proxies import GenericProxyConfig

        api = YouTubeTranscriptApi(proxy_config=GenericProxyConfig(http_url=proxy, https_url=proxy))
    else:
        api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=languages)
    except Exception:
        # Preferred languages missing: take whatever exists (manual first, then auto),
        # asking YouTube to translate it to the first preferred language when it can.
        transcripts = list(api.list(video_id))
        if not transcripts:
            raise
        transcripts.sort(key=lambda t: t.is_generated)
        original = transcripts[0]
        target = languages[0]
        try:
            if not original.is_translatable:
                raise ValueError
            fetched = original.translate(target).fetch()
            print(f"  (no {target} captions; using YouTube's {target} translation of {original.language})",
                  file=sys.stderr)
        except Exception:
            fetched = original.fetch()
            print(f"  (no {target} captions; using {fetched.language}; notes are still written in your notes language)",
                  file=sys.stderr)
    return [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]


def playlist_video_ids(playlist_url: str) -> list[str]:
    """Video IDs of a YouTube playlist, in playlist order (via yt-dlp, no API key)."""
    import yt_dlp

    opts = {"extract_flat": True, "quiet": True, "no_warnings": True}
    proxy = os.environ.get("YT_PROXY_URL")
    if proxy:
        opts["proxy"] = proxy
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
    return [e["id"] for e in info.get("entries") or [] if e and e.get("id")]


def has_notes(video_id: str, folder: Path) -> bool:
    """True if a page in `folder` already links to this video (every page links to its lecture)."""
    needle = f"watch?v={video_id}"
    return folder.is_dir() and any(needle in p.read_text(encoding="utf-8") for p in folder.glob("*.md"))


def next_video_id(video_ids: list[str], folder: Path) -> str | None:
    """First video without a notes page yet, or None when the whole playlist is done."""
    return next((v for v in video_ids if not has_notes(v, folder)), None)


def fmt_ts(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def compact_transcript(snippets: list[dict], every: int = 30) -> str:
    """Merge caption fragments into ~30-second chunks, each prefixed with [mm:ss].
    Keeps timestamps for the model while cutting tokens."""
    lines, buf, chunk_start = [], [], None
    for snip in snippets:
        if chunk_start is None:
            chunk_start = snip["start"]
        buf.append(snip["text"].replace("\n", " ").strip())
        if snip["start"] - chunk_start >= every:
            lines.append(f"[{fmt_ts(chunk_start)}] {' '.join(buf)}")
            buf, chunk_start = [], None
    if buf:
        lines.append(f"[{fmt_ts(chunk_start)}] {' '.join(buf)}")
    return "\n".join(lines)


def fetch_title(video_id: str) -> str | None:
    """Best-effort video title via YouTube's public oEmbed endpoint (no API key)."""
    import urllib.request

    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.load(r)
        return f"{data.get('title')} — {data.get('author_name')}"
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 2. Notes from Claude (structured output via a forced tool call)
# ---------------------------------------------------------------------------

NOTES_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": (
            "Precise title naming the lecture's main topic in 2-6 words, e.g. 'Introduction to Lasers' "
            "or 'Fabry-Perot Resonators'. No subtitle, no list of subtopics, no colon, no course or "
            "lecture number. It also becomes the page's file name.")},
        "summary": {"type": "string", "description": "2-4 sentence overview of what the lecture covers and its central idea."},
        "key_concepts": {
            "type": "array",
            "description": "The 5-10 most important ideas, definitions or results.",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "explanation": {"type": "string", "description": "Plain-language explanation; include formulas in LaTeX-free plain text."},
                    "timestamp_seconds": {"type": "integer"},
                },
                "required": ["term", "explanation", "timestamp_seconds"],
            },
        },
        "sections": {
            "type": "array",
            "description": "The lecture broken into its natural parts, in order.",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "timestamp_seconds": {"type": "integer"},
                    "points": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["heading", "timestamp_seconds", "points"],
            },
        },
        "my_notes_woven_in": {
            "type": "array",
            "description": "Each of the learner's own notes, paired with what the lecture said at that point. Empty if none were given.",
            "items": {
                "type": "object",
                "properties": {"my_note": {"type": "string"}, "context": {"type": "string"}},
                "required": ["my_note", "context"],
            },
        },
        "review_questions": {
            "type": "array",
            "description": "4-6 questions to test understanding later (retrieval practice).",
            "items": {"type": "string"},
        },
        "open_threads": {
            "type": "array",
            "description": "Things the lecture mentioned but didn't fully explain, worth looking up.",
            "items": {"type": "string"},
        },
    },
    "required": ["title", "summary", "key_concepts", "sections", "review_questions"],
}

SYSTEM_PROMPT = """You are a careful note-taker for someone studying from recorded lectures.
Write notes that help them understand and remember, not a transcript rewrite.
- Be faithful to what the lecturer actually said; don't invent claims or examples.
- Timestamps must come from the [mm:ss] markers in the transcript (convert to seconds).
- Prefer clear explanations and the 'why' over lists of jargon.
- If the learner supplied their own notes, treat them as signals of what they found
  important or confusing, and connect each one to the relevant part of the lecture."""


def make_notes(transcript: str, video_title: str | None, my_notes: str | None, model: str,
               notes_lang: str = "English") -> dict:
    import anthropic

    client = anthropic.Anthropic()
    system = SYSTEM_PROMPT + (
        f"\n- Write every part of the notes in {notes_lang}, even if the transcript or the "
        f"learner's notes are in another language. Keep technical terms recognisable; if a key "
        f"term was said in another language, give the {notes_lang} term with the original in brackets."
    )
    user_msg = f"Lecture: {video_title or 'Untitled YouTube lecture'}\n\n<transcript>\n{transcript}\n</transcript>"
    if my_notes:
        user_msg += f"\n\n<my_notes>\n{my_notes}\n</my_notes>"

    # Structured outputs: the reply is JSON guaranteed to match NOTES_SCHEMA.
    resp = client.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        output_config={"format": {"type": "json_schema", "schema": strict_schema(NOTES_SCHEMA)}},
        messages=[{"role": "user", "content": user_msg}],
    )
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("Notes were cut off before finishing; raise max_tokens in make_notes() and retry.")
    text = "".join(b.text for b in resp.content if b.type == "text")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(f"Claude's reply wasn't valid JSON (stop_reason={resp.stop_reason}):\n{text[:500]}")


def strict_schema(schema: dict) -> dict:
    """Structured outputs require additionalProperties: false on every object."""
    s = dict(schema)
    if s.get("type") == "object":
        s["additionalProperties"] = False
        s["properties"] = {k: strict_schema(v) for k, v in s.get("properties", {}).items()}
    if s.get("type") == "array" and "items" in s:
        s["items"] = strict_schema(s["items"])
    return s


# ---------------------------------------------------------------------------
# 3. Notion page
# ---------------------------------------------------------------------------

MAX_TEXT = 2000  # Notion's per-text-object limit


def rt(text: str, link: str | None = None, bold: bool = False) -> list[dict]:
    """Rich text, split into <=2000-char pieces."""
    out = []
    for i in range(0, max(len(text), 1), MAX_TEXT):
        piece = {"type": "text", "text": {"content": text[i:i + MAX_TEXT]}}
        if link:
            piece["text"]["link"] = {"url": link}
        if bold:
            piece["annotations"] = {"bold": True}
        out.append(piece)
    return out


def ts_link(video_id: str, seconds: int) -> list[dict]:
    url = f"https://www.youtube.com/watch?v={video_id}&t={int(seconds)}s"
    return rt(f"[{fmt_ts(seconds)}]", link=url)


def block(kind: str, rich: list[dict], **extra) -> dict:
    return {"object": "block", "type": kind, kind: {"rich_text": rich, **extra}}


def build_blocks(notes: dict, video_id: str, snippets: list[dict], include_transcript: bool) -> list[dict]:
    b: list[dict] = [
        {"object": "block", "type": "video",
         "video": {"type": "external", "external": {"url": f"https://www.youtube.com/watch?v={video_id}"}}},
        block("callout", rt(notes["summary"]), icon={"type": "emoji", "emoji": "💡"}),
    ]

    if notes.get("key_concepts"):
        b.append(block("heading_2", rt("Key concepts")))
        for c in notes["key_concepts"]:
            b.append(block("bulleted_list_item",
                           rt(c["term"], bold=True) + rt(" — " + c["explanation"] + " ")
                           + ts_link(video_id, c["timestamp_seconds"])))

    if notes.get("sections"):
        b.append(block("heading_2", rt("Walkthrough")))
        for s in notes["sections"]:
            b.append(block("heading_3", rt(s["heading"] + " ") + ts_link(video_id, s["timestamp_seconds"])))
            for p in s["points"]:
                b.append(block("bulleted_list_item", rt(p)))

    if notes.get("my_notes_woven_in"):
        b.append(block("heading_2", rt("My notes, in context")))
        for n in notes["my_notes_woven_in"]:
            b.append(block("quote", rt(n["my_note"])))
            b.append(block("paragraph", rt(n["context"])))

    if notes.get("review_questions"):
        b.append(block("heading_2", rt("Review questions")))
        for q in notes["review_questions"]:
            b.append(block("to_do", rt(q), checked=False))

    if notes.get("open_threads"):
        b.append(block("heading_2", rt("To look up")))
        for t in notes["open_threads"]:
            b.append(block("bulleted_list_item", rt(t)))

    if include_transcript:
        # Full transcript inside a collapsed toggle, in ~1-minute paragraphs.
        paras = compact_transcript(snippets, every=60).splitlines()
        b.append(block("toggle", rt("Full transcript"),
                       children=[block("paragraph", rt(p)) for p in paras[:100]]))
        # (toggles accept max 100 children on create; the rest are appended later)
        b[-1]["_overflow"] = [block("paragraph", rt(p)) for p in paras[100:]]
    return b


def create_notion_page(notes: dict, blocks: list[dict], parent_id: str, video_id: str) -> str:
    from notion_client import Client

    notion = Client(auth=os.environ["NOTION_TOKEN"])

    # Transcript toggles are appended on their own so we get their IDs back
    # and can fill in captions beyond Notion's 100-children-per-request limit.
    body = [blk for blk in blocks if "_overflow" not in blk]
    toggles = [blk for blk in blocks if "_overflow" in blk]

    page = notion.pages.create(
        parent={"page_id": parent_id},
        icon={"type": "emoji", "emoji": "🎓"},
        properties={"title": {"title": rt(notes["title"])}},
        children=body[:100],
    )
    # Notion allows 100 blocks per request; append any remainder in batches.
    for i in range(100, len(body), 100):
        notion.blocks.children.append(block_id=page["id"], children=body[i:i + 100])

    for toggle in toggles:
        extra = toggle.pop("_overflow")
        res = notion.blocks.children.append(block_id=page["id"], children=[toggle])
        toggle_id = res["results"][0]["id"]
        for j in range(0, len(extra), 100):
            notion.blocks.children.append(block_id=toggle_id, children=extra[j:j + 100])

    return page.get("url", page["id"])


# ---------------------------------------------------------------------------
# 4. Markdown page in the repo (commit and push it yourself)
# ---------------------------------------------------------------------------


def ts_md(video_id: str, seconds: int) -> str:
    return f"[{fmt_ts(seconds)}](https://www.youtube.com/watch?v={video_id}&t={int(seconds)}s)"


def build_markdown(notes: dict, video_id: str, video_title: str | None, snippets: list[dict],
                   include_transcript: bool) -> str:
    from datetime import date

    url = f"https://www.youtube.com/watch?v={video_id}"
    md = [f"# {notes['title']}", ""]
    md += [f"**Lecture:** [{video_title or url}]({url})  ", f"**Notes taken:** {date.today().isoformat()}", ""]
    md += [f"[![Watch on YouTube](https://img.youtube.com/vi/{video_id}/hqdefault.jpg)]({url})", ""]
    md += [f"> {notes['summary']}", ""]

    if notes.get("key_concepts"):
        md += ["## Key concepts", ""]
        md += [f"- **{c['term']}** — {c['explanation']} {ts_md(video_id, c['timestamp_seconds'])}"
               for c in notes["key_concepts"]]
        md.append("")

    if notes.get("sections"):
        md += ["## Walkthrough", ""]
        for s in notes["sections"]:
            md += [f"### {s['heading']} {ts_md(video_id, s['timestamp_seconds'])}", ""]
            md += [f"- {p}" for p in s["points"]]
            md.append("")

    if notes.get("my_notes_woven_in"):
        md += ["## My notes, in context", ""]
        for n in notes["my_notes_woven_in"]:
            md += [f"> {n['my_note']}", "", n["context"], ""]

    if notes.get("review_questions"):
        md += ["## Review questions", ""]
        md += [f"- [ ] {q}" for q in notes["review_questions"]]
        md.append("")

    if notes.get("open_threads"):
        md += ["## To look up", ""]
        md += [f"- {t}" for t in notes["open_threads"]]
        md.append("")

    if include_transcript:
        md += ["<details><summary>Full transcript</summary>", "", compact_transcript(snippets, every=60), "", "</details>", ""]
    return "\n".join(md)


def slugify(text: str, max_len: int = 50) -> str:
    """File-name slug from a title: drops any subtitle (after ':' or a dash) and
    cuts at a word boundary, so names stay precise and never end mid-word."""
    text = re.split(r"\s*(?::|\s[—–-]\s)\s*", text.strip(), maxsplit=1)[0] or text
    s = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.ASCII)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    if len(s) > max_len:
        cut = s[:max_len + 1]
        s = cut[:cut.rfind("-")] if "-" in cut else s[:max_len]
    return s.strip("-") or "lecture"


def repo_root() -> Path:
    """Root of the git repo this script lives in (falls back to the current folder)."""
    import subprocess

    for where in (Path(__file__).resolve().parent, Path.cwd()):
        try:
            out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=where,
                                 capture_output=True, text=True, check=True)
            return Path(out.stdout.strip())
        except Exception:
            continue
    return Path.cwd()


def save_markdown(markdown: str, title: str, folder: str) -> Path:
    """Write <repo>/<folder>/<date>-<title>.md. Re-running the same lecture the same day overwrites it."""
    from datetime import date

    target = repo_root() / folder.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{date.today().isoformat()}-{slugify(title)}.md"
    path.write_text(markdown, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    load_dotenv(Path(__file__).with_name(".env"))

    ap = argparse.ArgumentParser(description="YouTube lecture → study notes → Markdown page in this repo (+ Notion)")
    ap.add_argument("url", nargs="?", help="YouTube URL or video ID")
    ap.add_argument("--next", metavar="PLAYLIST_URL", default=os.environ.get("PLAYLIST_URL") or None,
                    help="instead of URL: take the first video in this playlist without notes yet")
    ap.add_argument("--start", type=int, default=int(os.environ.get("PLAYLIST_START") or 1), metavar="N",
                    help="with --next: ignore videos before position N in the playlist, e.g. an intro (default: 1)")
    ap.add_argument("--my-notes", type=Path, help="text file with your own notes to weave in")
    ap.add_argument("--lang", nargs="+", default=["en"], help="preferred caption languages, in order (default: en)")
    ap.add_argument("--parent", default=os.environ.get("NOTION_PARENT_PAGE_ID"), help="Notion parent page ID")
    ap.add_argument("--folder", default=os.environ.get("NOTES_FOLDER", "photonics"),
                    help="folder in this repo for the Markdown page (default: photonics)")
    ap.add_argument("--no-notion", action="store_true", help="skip Notion this time")
    ap.add_argument("--no-markdown", action="store_true", help="skip the Markdown page this time")
    ap.add_argument("--with-transcript", action="store_true", help="also attach the full transcript (collapsed)")
    ap.add_argument("--notes-lang", default="English", help="language the notes are written in (default: English)")
    ap.add_argument("--dry-run", action="store_true", help="print the notes as JSON; publish nowhere")
    ap.add_argument("--model", default=os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL))
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY (see .env.example).")

    # Each destination is used when it's configured in .env and not switched off.
    to_notion = not args.no_notion and bool(os.environ.get("NOTION_TOKEN") and args.parent)
    to_markdown = not args.no_markdown
    if not args.dry_run and not (to_notion or to_markdown):
        sys.exit("Nothing to do: --no-markdown was given and Notion isn't set up in .env.")

    if args.url:
        video_id = extract_video_id(args.url)
    elif args.next:
        print("→ Looking for the next lecture in the playlist…", file=sys.stderr)
        video_ids = playlist_video_ids(args.next)[max(args.start, 1) - 1:]
        video_id = next_video_id(video_ids, repo_root() / args.folder.strip("/"))
        if video_id is None:
            print("✓ Every lecture in the playlist already has notes; nothing to do.")
            if os.environ.get("GITHUB_OUTPUT"):  # tells the GitHub workflow to switch itself off
                with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
                    f.write("playlist_done=true\n")
            return
        print(f"  next lecture: https://www.youtube.com/watch?v={video_id}", file=sys.stderr)
    else:
        ap.error("give a YouTube URL, or --next PLAYLIST_URL")
    print("→ Fetching transcript…", file=sys.stderr)
    snippets = fetch_transcript(video_id, args.lang)
    title = fetch_title(video_id)
    my_notes = args.my_notes.read_text(encoding="utf-8") if args.my_notes else None

    print(f"→ Writing notes with {args.model}…", file=sys.stderr)
    notes = make_notes(compact_transcript(snippets), title, my_notes, args.model, args.notes_lang)

    if args.dry_run:
        print(json.dumps(notes, indent=2, ensure_ascii=False))
        return

    # Publish to each destination independently, so one failing doesn't lose the other.
    failed = False
    if to_notion:
        print("→ Creating Notion page…", file=sys.stderr)
        try:
            blocks = build_blocks(notes, video_id, snippets, include_transcript=args.with_transcript)
            print(f"✓ Notion: {create_notion_page(notes, blocks, args.parent.replace('-', ''), video_id)}")
        except Exception as e:
            failed = True
            print(f"✗ Notion failed: {e}", file=sys.stderr)

    if to_markdown:
        try:
            md = build_markdown(notes, video_id, title, snippets, include_transcript=args.with_transcript)
            path = save_markdown(md, notes["title"], args.folder)
            print(f"✓ Markdown page: {path}")
        except Exception as e:
            failed = True
            print(f"✗ Markdown page failed: {e}", file=sys.stderr)

    if failed:
        # Keep the notes so nothing is lost; they can be re-published or pasted in by hand.
        backup = Path(__file__).with_name(f"notes-{video_id}.json")
        backup.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Notes saved to {backup.name} so nothing is lost.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
    