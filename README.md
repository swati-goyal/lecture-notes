# Lecture notes → this repo (+ Notion)

Paste a YouTube lecture link, get a Markdown page in this repo's `photonics/` folder (ready to commit and push) and, if you set it up, a Notion page, with:

- the video embedded at the top and a short summary
- **Key concepts**, each with a clickable timestamp that jumps to that moment
- a section-by-section **walkthrough**
- **your own notes woven in** (optional), each placed next to what the lecturer was saying
- **review questions** as checkboxes, for retrieval practice later
- a **to look up** list of things mentioned but not fully explained
- notes always written in English (changeable), whatever language the lecture is in

## Setup (once, ~10 minutes)

1. **Python 3.9+** (check with `python3 --version`), then:
   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Claude API key** — create one at https://console.anthropic.com (API usage is billed separately from a Claude.ai subscription).

3. **Notion integration** (optional; skip if you only want the Markdown page)
   - Go to https://www.notion.so/profile/integrations → *New integration* → type *Internal*, give it a name like "Lecture notes" → copy the secret.
   - In Notion, create a page called e.g. **Lecture Notes**. Open its `•••` menu → *Connections* → add your integration. (Without this step the script gets a "could not find page" error.)
   - Copy that page's ID: the 32-character string at the end of its URL.

4. Copy `.env.example` to `.env` and fill in the values. Add `.env` to your `.gitignore` so your keys never get pushed.

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
| `--lang de en` | Prefer German captions, then English. If neither exists, it uses YouTube's auto-translation into your first choice, then whatever captions exist |
| `--notes-lang German` | Write the notes in another language (default: English) |
| `--dry-run` | Print the notes as JSON without publishing anywhere; good for a first test |
| `--folder optics` | Save the page to a different folder in the repo this time (default: `photonics`) |
| `--no-notion` / `--no-markdown` | Skip one destination for this run |
| `--with-transcript` | Also attach the full transcript in a collapsed toggle (off by default) |
| `--model …` | Use a different Claude model |
| `--next PLAYLIST_URL` | Instead of a video link: take the next lecture in a playlist that has no notes yet (see below) |

### Next lecture in a playlist

```bash
python lecture_notes.py --next "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

Add `--start 2` to ignore the videos before position 2 in the playlist, such as a course intro video. This picks the first remaining video that has no page in the folder yet (a page counts if it links to that video), so running it again moves on to the following lecture. Run it once a day, then commit and push the new page. When every lecture has notes, it says so and does nothing.

## Good to know

- It works from the video's **captions**, so it needs a video with captions (most lectures have at least auto-generated ones). It doesn't "see" slides or board work; if a lecture is very visual, your own notes fill that gap.
- A 1-hour lecture costs roughly a few cents to tens of cents in API usage, depending on the model.
- If YouTube blocks the transcript request (it sometimes does for cloud servers or VPNs), run it from your home network.
- Pages are saved as `photonics/<date>-lec<number>-<topic>.md` at the root of the git repo the script is in, e.g. `photonics/2026-10-22-lec03-einstein-coefficients.md`. The lecture number comes from the video title (`mod01lec03`, `Lecture 3`, …); with `--next`, if the title has none, it's the video's position in the playlist counted from `--start`. Without a number the name is just `<date>-<topic>.md`. Claude is asked for a short, precise title (2-6 words, no subtitle), and the file name drops anything after a `:` or ` — ` and is cut at a whole word (max 50 characters). Re-running the same lecture on the same day overwrites that file instead of creating a duplicate. Then just `git add`, commit and push.
- If one destination fails, the other still goes through, and the notes are saved locally as `notes-<video id>.json` so nothing is lost.

## Tests

The tests need no API keys or network: YouTube, Claude and Notion are replaced with fakes.

```bash
pip install -r requirements-dev.txt
python -m pytest
```

They cover parsing YouTube links, the transcript chunking, how page names are made, the Claude request and its error handling, the Markdown and Notion output, and the command-line options.
