# WritLarge

A forward-only freewriting tool. Type until you're done — no editing, no distractions, no going back.

## What it does

WritLarge opens a full-screen black canvas and asks you to write 750 words. You cannot delete anything. Older text fades into the background so only the last few words are visible. When you hit the target, the session is saved and the app closes.

One session per day. If you've already written today, the app tells you so and exits.

## Packages

| Package | Description |
|---------|-------------|
| `packages/desktop/` | Electron + React desktop app (macOS) |
| `packages/cli/` | Terminal app (Python, no dependencies) |

Both read the same config and write the same file formats.

## Getting started

### Desktop

```bash
cd packages/desktop
npm install
npm run dev
```

To build and install to `~/Applications`:

```bash
./scripts/build-mac.sh
```

### CLI

```bash
python3 packages/cli/writlarge.py
```

Requires Python 3 and a terminal with color support. No pip installs needed.

## Configuration

Edit `~/Library/Application Support/writlarge/config.json`:

```json
{
  "wordTarget": 750,
  "outputDir": "~/WritLarge"
}
```

## Output

Each session writes to `~/WritLarge/` (or your configured `outputDir`):

- `YYYY-MM-DD.txt` — the text you wrote
- `YYYY-MM-DD.keys.json` — per-keystroke timing data
- `stats.jsonl` — one summary line appended per session

## Design decisions

- **No backspace.** Backspace and Delete are disabled. Words cannot be taken back.
- **Fade window.** Only the last ~40 words are visible. The rest fades to black.
- **Save on target.** The file is not written until the word count target is reached. Quitting early saves nothing.
- **One session per day.** If today's file exists, the app is blocked until tomorrow.
