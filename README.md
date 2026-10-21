# Lecture → Notion notes

Paste a YouTube lecture link, get a Notion page with:

- the video embedded at the top and a short summary
- **Key concepts**, each with a clickable timestamp that jumps to that moment
- a section-by-section **walkthrough**
- **your own notes woven in** (optional), each placed next to what the lecturer was saying
- **review questions** as checkboxes, for retrieval practice later
- a **to look up** list of things mentioned but not fully explained
- the full transcript tucked into a collapsed toggle

## Setup (once, ~10 minutes)

1. **Python 3.10+**, then:
   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Claude API key** — create one at https://console.anthropic.com (API usage is billed separately from a Claude.ai subscription).

3. **Notion integration**
   - Go to https://www.notion.so/profile/integrations → *New integration* → type *Internal*, give it a name like "Lecture notes" → copy the secret.
   - In Notion, create a page called e.g. **Lecture Notes**. Open its `•••` menu → *Connections* → add your integration. (Without this step the script gets a "could not find page" error.)
   - Copy that page's ID: the 32-character string at the end of its URL.

4. Copy `.env.example` to `.env` and fill in the three values.

## Use

```bash
python lecture_notes.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

While watching, jot thoughts in a plain text file (any format: questions, "confused here", "~12:30 the key bit"), then:

```bash
python lecture_notes.py URL --my-notes notes.txt
```

Other options:

| Flag | What it does |
|---|---|
| `--lang de en` | Prefer German captions, fall back to English (then anything available) |
| `--dry-run` | Print the notes as JSON without touching Notion; good for a first test |
| `--no-transcript` | Skip the transcript toggle |
| `--model …` | Use a different Claude model |

## Good to know

- It works from the video's **captions**, so it needs a video with captions (most lectures have at least auto-generated ones). It doesn't "see" slides or board work; if a lecture is very visual, your own notes fill that gap.
- A 1-hour lecture costs roughly a few cents to tens of cents in API usage, depending on the model.
- If YouTube blocks the transcript request (it sometimes does for cloud servers or VPNs), run it from your home network.
