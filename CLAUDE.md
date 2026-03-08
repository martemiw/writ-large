# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Desktop (packages/desktop/)
```bash
npm run dev        # Vite dev server (localhost:5173) + Electron with HMR
npm start          # Run Electron against built dist/ (no HMR)
npm run build      # Vite build only → dist/
npm run dist       # Full build: Vite + electron-builder → release/
./scripts/build-mac.sh  # Build + install to ~/Applications/WritLarge.app
```

### CLI (packages/cli/)
```bash
python3 packages/cli/writlarge.py
```

There are no linters or test suites configured.

## Architecture

### Packages
- `packages/desktop/` — Electron 28 + React 18 + Vite 5; no UI framework, all styles in `src/App.css`
- `packages/cli/` — Standalone Python 3 curses TUI; zero pip dependencies

Both packages share the same file formats and config location — sessions written by one are readable by the other.

### Desktop: Electron + React

The app uses Electron's context isolation model. The renderer has no Node access; all file I/O goes through a narrow IPC bridge:

**`electron/preload.js`** exposes `window.writlarge` to the renderer:
- `getConfig()` — Returns merged config (defaults + `~/Library/Application Support/writlarge/config.json`)
- `checkToday()` — Returns bool: does today's `.txt` file already exist?
- `saveSession(text, meta)` — Writes all 3 output files; returns `{ success, path|error }`
- `quit()` — Calls `app.quit()`

**`electron/main.js`** handles these IPC calls and all file I/O. In dev mode (`ELECTRON_DEV=1`) it loads from `http://localhost:5173`; in prod it loads from `dist/index.html`.

### React App Flow

`src/App.jsx` is a simple state machine over screen names: `title → loading → writing | blocked`.

- Config is fetched once on mount and passed down.
- `WritingCanvas.jsx` — Core editor. Intercepts `keydown`, hard-blocks Backspace/Delete. Records every keystroke as `{ k: char, d: delta_ms }` in a ref. When `wordCount >= target`, fires `saveSession` once (guarded by a `saveAttempted` ref) and transitions to DoneScreen.
- `FadeText.jsx` — Renders the last 40 words of the buffer; CSS `mask-image` gradient in App.css fades older words to black.
- `HUD.jsx` — Fixed-position overlay: elapsed time (bottom-left), word count / target (bottom-right).

### Output Files

All files go to `config.outputDir` (default `~/WritLarge/`):

| File | Description |
|------|-------------|
| `YYYY-MM-DD.txt` | Plain text of the session |
| `YYYY-MM-DD.keys.json` | `{ start: epoch_ms, keys: [{k, d}, …] }` — per-keystroke timing |
| `stats.jsonl` | Appended line per session: `{ date, time_of_day, words, median_ms, duration_s }` |

If `YYYY-MM-DD.txt` already exists, the app shows the BlockedScreen — one session per calendar day, no appending.

### Config

`~/Library/Application Support/writlarge/config.json` — user values merge over defaults:
```json
{ "wordTarget": 750, "outputDir": "~/WritLarge" }
```

### CLI parity

`packages/cli/writlarge.py` is a self-contained rewrite of the desktop app in curses. It reads the same config file and writes identical file formats. Keep the two in sync when changing file formats or config keys.
