"""Tests for lecture_notes.py. No network or API keys needed: YouTube, Claude and
Notion calls are either avoided or replaced with fakes."""

import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lecture_notes as ln  # noqa: E402

VIDEO_ID = "WgWozOgMXKo"

NOTES = {
    "title": "Introduction to Lasers",
    "summary": "What a laser is and why its light is special.",
    "key_concepts": [
        {"term": "Monochromaticity", "explanation": "Very narrow spectral width.", "timestamp_seconds": 125},
    ],
    "sections": [
        {"heading": "Course scope", "timestamp_seconds": 0, "points": ["Topics covered", "Prerequisites"]},
        {"heading": "Properties of laser light", "timestamp_seconds": 3725, "points": ["Coherence"]},
    ],
    "my_notes_woven_in": [{"my_note": "confused about coherence", "context": "Explained at 12:00."}],
    "review_questions": ["What makes laser light monochromatic?"],
    "open_threads": ["Einstein coefficients"],
}

SNIPPETS = [
    {"text": "hello", "start": 0.0, "duration": 2.0},
    {"text": "and\nwelcome", "start": 10.0, "duration": 2.0},
    {"text": "to lasers", "start": 31.0, "duration": 2.0},
    {"text": "part two", "start": 40.0, "duration": 2.0},
]


# --- page name -------------------------------------------------------------


@pytest.mark.parametrize("title, slug", [
    ("Introduction to Lasers", "introduction-to-lasers"),
    ("Introduction to Lasers: Course Scope, What a Laser Is, and Monochromaticity", "introduction-to-lasers"),
    ("Fabry-Perot Resonators — Lecture 4", "fabry-perot-resonators"),
    ("Gaussian Beams - ABCD matrices", "gaussian-beams"),
    ("  Snell's Law & Total Internal Reflection!  ", "snells-law-total-internal-reflection"),
    ("???", "lecture"),
    ("", "lecture"),
])
def test_slugify(title, slug):
    assert ln.slugify(title) == slug


def test_slugify_keeps_hyphenated_words():
    assert ln.slugify("Fabry-Perot interferometer") == "fabry-perot-interferometer"


def test_slugify_cuts_at_word_boundary():
    slug = ln.slugify("Stimulated emission and population inversion in three level and four level systems")
    assert len(slug) <= 50
    assert slug == "stimulated-emission-and-population-inversion-in"


def test_slugify_long_single_word_is_hard_cut():
    assert ln.slugify("a" * 80) == "a" * 50


def test_title_schema_asks_for_precise_title():
    desc = ln.NOTES_SCHEMA["properties"]["title"]["description"]
    assert "2-6 words" in desc and "No subtitle" in desc


# --- YouTube helpers -------------------------------------------------------


@pytest.mark.parametrize("url", [
    VIDEO_ID,
    f"https://www.youtube.com/watch?v={VIDEO_ID}",
    f"https://www.youtube.com/watch?v={VIDEO_ID}&t=42s&list=PL123",
    f"https://youtu.be/{VIDEO_ID}?si=abc",
    f"https://m.youtube.com/watch?v={VIDEO_ID}",
    f"https://www.youtube.com/shorts/{VIDEO_ID}",
    f"https://www.youtube.com/live/{VIDEO_ID}",
    f"https://www.youtube.com/embed/{VIDEO_ID}",
    f"  {VIDEO_ID}  ",
])
def test_extract_video_id(url):
    assert ln.extract_video_id(url) == VIDEO_ID


@pytest.mark.parametrize("bad", ["https://vimeo.com/123", "not a url", "https://www.youtube.com/"])
def test_extract_video_id_rejects_non_youtube(bad):
    with pytest.raises(ValueError):
        ln.extract_video_id(bad)


@pytest.mark.parametrize("seconds, text", [(0, "0:00"), (65, "1:05"), (3599.9, "59:59"), (3725, "1:02:05")])
def test_fmt_ts(seconds, text):
    assert ln.fmt_ts(seconds) == text


def test_compact_transcript_chunks_and_flattens_newlines():
    assert ln.compact_transcript(SNIPPETS, every=30).splitlines() == [
        "[0:00] hello and welcome to lasers",
        "[0:40] part two",
    ]


def test_compact_transcript_empty():
    assert ln.compact_transcript([]) == ""


# --- Claude request --------------------------------------------------------


def test_strict_schema_closes_every_object():
    strict = ln.strict_schema(ln.NOTES_SCHEMA)
    assert strict["additionalProperties"] is False
    assert strict["properties"]["key_concepts"]["items"]["additionalProperties"] is False
    assert strict["properties"]["sections"]["items"]["additionalProperties"] is False
    assert "additionalProperties" not in ln.NOTES_SCHEMA  # original untouched


class FakeAnthropic:
    """Stands in for anthropic.Anthropic, recording the request and returning `reply`."""

    def __init__(self, reply, stop_reason="end_turn"):
        self.reply, self.stop_reason, self.request = reply, stop_reason, None
        self.messages = self

    def __call__(self):
        return self

    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(stop_reason=self.stop_reason,
                               content=[SimpleNamespace(type="text", text=self.reply)])


@pytest.fixture
def fake_claude(monkeypatch):
    def install(reply, stop_reason="end_turn"):
        fake = FakeAnthropic(reply, stop_reason)
        monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=fake))
        return fake
    return install


def test_make_notes_parses_reply_and_builds_prompt(fake_claude):
    fake = fake_claude(json.dumps(NOTES))
    notes = ln.make_notes("[0:00] hi", "Lasers — NPTEL", "my note", "some-model", notes_lang="German")
    assert notes == NOTES
    req = fake.request
    assert req["model"] == "some-model"
    assert "in German" in req["system"]
    content = req["messages"][0]["content"]
    assert "Lecture: Lasers — NPTEL" in content and "<my_notes>\nmy note\n</my_notes>" in content
    assert req["output_config"]["format"]["schema"]["additionalProperties"] is False


def test_make_notes_without_my_notes(fake_claude):
    fake = fake_claude(json.dumps(NOTES))
    ln.make_notes("[0:00] hi", None, None, "m")
    content = fake.request["messages"][0]["content"]
    assert "Untitled YouTube lecture" in content and "<my_notes>" not in content


def test_make_notes_truncated_reply(fake_claude):
    fake_claude("{", stop_reason="max_tokens")
    with pytest.raises(RuntimeError, match="cut off"):
        ln.make_notes("t", None, None, "m")


def test_make_notes_invalid_json(fake_claude):
    fake_claude("not json")
    with pytest.raises(RuntimeError, match="valid JSON"):
        ln.make_notes("t", None, None, "m")


# --- Markdown page ---------------------------------------------------------


def test_build_markdown_sections_and_links():
    md = ln.build_markdown(NOTES, VIDEO_ID, "mod01lec01 — NPTEL", SNIPPETS, include_transcript=False)
    assert md.startswith("# Introduction to Lasers\n")
    assert f"[mod01lec01 — NPTEL](https://www.youtube.com/watch?v={VIDEO_ID})" in md
    assert f"**Notes taken:** {date.today().isoformat()}" in md
    assert f"https://img.youtube.com/vi/{VIDEO_ID}/hqdefault.jpg" in md
    assert "> What a laser is" in md
    assert f"- **Monochromaticity** — Very narrow spectral width. [2:05](https://www.youtube.com/watch?v={VIDEO_ID}&t=125s)" in md
    assert f"### Properties of laser light [1:02:05](https://www.youtube.com/watch?v={VIDEO_ID}&t=3725s)" in md
    assert "> confused about coherence" in md
    assert "- [ ] What makes laser light monochromatic?" in md
    assert "## To look up" in md
    assert "Full transcript" not in md


def test_build_markdown_minimal_notes_and_transcript():
    notes = {"title": "T", "summary": "S", "key_concepts": [], "sections": [], "review_questions": []}
    md = ln.build_markdown(notes, VIDEO_ID, None, SNIPPETS, include_transcript=True)
    assert f"[https://www.youtube.com/watch?v={VIDEO_ID}]" in md  # falls back to the URL
    for heading in ("## Key concepts", "## Walkthrough", "## My notes", "## Review questions", "## To look up"):
        assert heading not in md
    assert "<details><summary>Full transcript</summary>" in md and "[0:00] hello" in md


def test_save_markdown_uses_precise_name_and_overwrites(tmp_path, monkeypatch):
    monkeypatch.setattr(ln, "repo_root", lambda: tmp_path)
    title = "Introduction to Lasers: Course Scope, What a Laser Is, and Monochromaticity"
    path = ln.save_markdown("first", title, "/photonics/")
    assert path == tmp_path / "photonics" / f"{date.today().isoformat()}-introduction-to-lasers.md"
    assert ln.save_markdown("second", title, "photonics") == path
    assert path.read_text(encoding="utf-8") == "second"
    assert len(list((tmp_path / "photonics").iterdir())) == 1


# --- Notion blocks ---------------------------------------------------------


def test_rt_splits_long_text():
    pieces = ln.rt("x" * 4500, link="https://e.com", bold=True)
    assert [len(p["text"]["content"]) for p in pieces] == [2000, 2000, 500]
    assert all(p["text"]["link"] == {"url": "https://e.com"} and p["annotations"]["bold"] for p in pieces)
    assert ln.rt("") == [{"type": "text", "text": {"content": ""}}]


def test_build_blocks_structure():
    blocks = ln.build_blocks(NOTES, VIDEO_ID, SNIPPETS, include_transcript=False)
    types = [b["type"] for b in blocks]
    assert types[:2] == ["video", "callout"]
    assert types.count("heading_2") == 5
    assert types.count("to_do") == 1 and types.count("quote") == 1
    assert "toggle" not in types


def test_build_blocks_transcript_overflow():
    snippets = [{"text": f"line {i}", "start": i * 60.0, "duration": 1.0} for i in range(300)]
    toggle = ln.build_blocks(NOTES, VIDEO_ID, snippets, include_transcript=True)[-1]
    assert toggle["type"] == "toggle"
    assert len(toggle["toggle"]["children"]) == 100 and len(toggle["_overflow"]) == 50


class FakeNotion:
    def __init__(self):
        self.created, self.appended = None, []
        self.pages = SimpleNamespace(create=self._create)
        self.blocks = SimpleNamespace(children=SimpleNamespace(append=self._append))

    def _create(self, **kwargs):
        self.created = kwargs
        return {"id": "page-id", "url": "https://notion.so/page"}

    def _append(self, block_id, children):
        self.appended.append((block_id, len(children)))
        return {"results": [{"id": f"block-{len(self.appended)}"}]}


def test_create_notion_page_batches_requests(monkeypatch):
    fake = FakeNotion()
    monkeypatch.setitem(sys.modules, "notion_client", SimpleNamespace(Client=lambda auth: fake))
    monkeypatch.setenv("NOTION_TOKEN", "secret")
    body = [ln.block("paragraph", ln.rt(str(i))) for i in range(230)]
    toggle = ln.block("toggle", ln.rt("Full transcript"), children=[])
    toggle["_overflow"] = [ln.block("paragraph", ln.rt("p"))] * 150

    url = ln.create_notion_page({"title": "T"}, body + [toggle], "parent", VIDEO_ID)

    assert url == "https://notion.so/page"
    assert len(fake.created["children"]) == 100
    assert fake.appended == [("page-id", 100), ("page-id", 30), ("page-id", 1), ("block-3", 100), ("block-3", 50)]


# --- config ----------------------------------------------------------------


def test_load_dotenv(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('# comment\nA_KEY="quoted"\nB_KEY = plain\nnot a pair\nEXISTING=new\n', encoding="utf-8")
    monkeypatch.delenv("A_KEY", raising=False)
    monkeypatch.delenv("B_KEY", raising=False)
    monkeypatch.setenv("EXISTING", "old")
    ln.load_dotenv(env)
    assert (ln.os.environ["A_KEY"], ln.os.environ["B_KEY"], ln.os.environ["EXISTING"]) == ("quoted", "plain", "old")
    ln.load_dotenv(tmp_path / "missing.env")  # no error


# --- CLI -------------------------------------------------------------------


@pytest.fixture
def cli(monkeypatch, tmp_path):
    """Runs main() with YouTube and Claude faked out and the repo root in tmp_path."""
    monkeypatch.setattr(ln, "load_dotenv", lambda path: None)
    monkeypatch.setattr(ln, "fetch_transcript", lambda vid, langs: SNIPPETS)
    monkeypatch.setattr(ln, "fetch_title", lambda vid: "mod01lec01 — NPTEL")
    monkeypatch.setattr(ln, "make_notes", lambda *a, **k: dict(NOTES))
    monkeypatch.setattr(ln, "repo_root", lambda: tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.delenv("NOTION_TOKEN", raising=False)

    def run(*argv):
        monkeypatch.setattr(sys, "argv", ["lecture_notes.py", *argv])
        ln.main()
    return run


def test_cli_writes_markdown_page(cli, tmp_path, capsys):
    cli(VIDEO_ID)
    page = tmp_path / "photonics" / f"{date.today().isoformat()}-introduction-to-lasers.md"
    assert page.exists()
    assert "✓ Markdown page" in capsys.readouterr().out


def test_cli_dry_run_publishes_nothing(cli, tmp_path, capsys):
    cli(VIDEO_ID, "--dry-run")
    assert json.loads(capsys.readouterr().out) == NOTES
    assert not (tmp_path / "photonics").exists()


def test_cli_requires_api_key(cli, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY"):
        cli(VIDEO_ID)


def test_cli_nothing_to_do(cli):
    with pytest.raises(SystemExit, match="Nothing to do"):
        cli(VIDEO_ID, "--no-markdown")
