#!/usr/bin/env python3
"""
lecture_notes.py — turn a YouTube lecture into study notes on a Notion page.

Pipeline:
  1. Fetch the video's transcript (captions) from YouTube.
  2. Ask Claude to write structured notes, optionally weaving in your own notes.
  3. Create a Notion page with the notes, every timestamp linking back to
     that moment in the video.

Usage:
  python lecture_notes.py "https://www.youtube.com/watch?v=VIDEO_ID"
  python lecture_notes.py URL --my-notes my_notes.txt     # merge your own notes
  python lecture_notes.py URL --lang de en                # prefer German captions
  python lecture_notes.py URL --dry-run                   # print notes, skip Notion

Environment (put these in a .env file next to this script, or export them):
  ANTHROPIC_API_KEY       your Claude API key
  NOTION_TOKEN            your Notion integration secret
  NOTION_PARENT_PAGE_ID   the Notion page the notes are created under
  CLAUDE_MODEL            optional; defaults to claude-sonnet-5-5
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

    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=languages)
    except Exception:
        # Preferred languages missing: take whatever exists (manual first, then auto).
        transcripts = list(api.list(video_id))
        if not transcripts:
            raise
        transcripts.sort(key=lambda t: t.is_generated)
        fetched = transcripts[0].fetch()
        print(f"  (no {languages} captions; using {fetched.language})", file=sys.stderr)
    return [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]


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
        "title": {"type": "string", "description": "Short, clear title for the notes page."},
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


def make_notes(transcript: str, video_title: str | None, my_notes: str | None, model: str) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    user_msg = f"Lecture: {video_title or 'Untitled YouTube lecture'}\n\n<transcript>\n{transcript}\n</transcript>"
    if my_notes:
        user_msg += f"\n\n<my_notes>\n{my_notes}\n</my_notes>"

    resp = client.messages.create(
        model=model,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        tools=[{
            "name": "save_lecture_notes",
            "description": "Save the structured notes for this lecture.",
            "input_schema": NOTES_SCHEMA,
        }],
        tool_choice={"type": "tool", "name": "save_lecture_notes"},
        messages=[{"role": "user", "content": user_msg}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError("Claude didn't return notes; try again.")


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
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    load_dotenv(Path(__file__).with_name(".env"))

    ap = argparse.ArgumentParser(description="YouTube lecture → study notes → Notion page")
    ap.add_argument("url", help="YouTube URL or video ID")
    ap.add_argument("--my-notes", type=Path, help="text file with your own notes to weave in")
    ap.add_argument("--lang", nargs="+", default=["en"], help="preferred caption languages, in order")
    ap.add_argument("--parent", default=os.environ.get("NOTION_PARENT_PAGE_ID"), help="Notion parent page ID")
    ap.add_argument("--no-transcript", action="store_true", help="don't attach the full transcript")
    ap.add_argument("--dry-run", action="store_true", help="print the notes as JSON; don't touch Notion")
    ap.add_argument("--model", default=os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL))
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY (see .env.example).")
    if not args.dry_run and not (os.environ.get("NOTION_TOKEN") and args.parent):
        sys.exit("Set NOTION_TOKEN and NOTION_PARENT_PAGE_ID, or use --dry-run.")

    video_id = extract_video_id(args.url)
    print("→ Fetching transcript…", file=sys.stderr)
    snippets = fetch_transcript(video_id, args.lang)
    title = fetch_title(video_id)
    my_notes = args.my_notes.read_text(encoding="utf-8") if args.my_notes else None

    print(f"→ Writing notes with {args.model}…", file=sys.stderr)
    notes = make_notes(compact_transcript(snippets), title, my_notes, args.model)

    if args.dry_run:
        print(json.dumps(notes, indent=2, ensure_ascii=False))
        return

    print("→ Creating Notion page…", file=sys.stderr)
    blocks = build_blocks(notes, video_id, snippets, include_transcript=not args.no_transcript)
    url = create_notion_page(notes, blocks, args.parent.replace("-", ""), video_id)
    print(f"✓ Done: {url}")


if __name__ == "__main__":
    main()
