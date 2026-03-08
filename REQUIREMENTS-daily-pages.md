# Software Requirements — Daily Pages

---

## 1. Overview

**Product Name:** WritLarge
**Feature Name:** Daily Pages
**Author:** —
**Date:** 2026-03-01
**Status:** `Done`

### Problem Statement
Writers who practice daily freewriting (e.g. "Morning Pages") need a distraction-free environment that enforces commitment. Conventional editors tempt the user to edit, save prematurely, or check word count anxiously. The act of saving — of "completing" the file — should be a reward gated on finishing the work, not an idle reflex.

### Goal
A minimal, full-screen writing environment where the only visible feedback is the trailing words on screen, a live word count toward a target, and a clock. The session is not persisted until the word-count target is reached.

### Non-Goals
- No editing of previously written text (no cursor navigation, no selection)
- No formatting or markdown rendering
- No multiple files, tabs, or sessions open simultaneously
- No cloud sync, export, or sharing (v1)
- No spell-check, autocorrect, or suggestions
- No settings UI (v1 — values are configured elsewhere)

---

## 2. User & Context

**Primary User:** A writer doing a daily freewriting practice.

**User Context:** Morning or any fixed writing ritual. The user opens the app with intention. They are in a flow state or trying to reach one. They want zero friction, zero distraction. Every UI element is a potential interruption.

**Success Looks Like:**
- User opens the app, sees a dark screen with a clock and word target
- They begin typing; only the trailing few words are visible
- When they hit the target, the file is saved and they receive a quiet completion signal
- The experience feels like writing into a void — committed, forward-only

---

## 3. Functional Requirements

| # | Requirement | Priority | Notes |
|---|-------------|----------|-------|
| F-01 | Full-screen, dark background writing canvas | MUST | No OS chrome if possible |
| F-02 | Live text input — forward-only; backspace is fully disabled | MUST | No take-backs. Resolved: Q-01 |
| F-03 | Only the last 5–6 words are visible; older text fades to black | MUST | Trailing fade effect |
| F-04 | Word count displayed against a configurable daily target (e.g. 750) | MUST | e.g. "312 / 750" |
| F-05 | Clock displayed on screen (current time) | MUST | No timer/countdown — just time of day |
| F-06 | File is NOT saved until word-count target is reached | MUST | Data lives in memory until then |
| F-07 | On target reached: file is saved, quiet completion state shown | MUST | Subtle signal — no fanfare |
| F-08 | Session file named by date (e.g. `2026-03-01.txt`) | MUST | Written to a configurable output directory |
| F-09 | If today's session is already complete (file exists), block the app with a "done for today" screen | MUST | One session per day, no append. Resolved: Q-02 |
| F-10 | Configurable word target | SHOULD | Default 750 |
| F-11 | Configurable output directory | SHOULD | Default `~/WritLarge/` |
| F-12 | Elapsed time display (time spent in current session) | COULD | Distinct from clock |
| F-13 | Words-per-minute (WPM) display | COULD | Live rolling average |

---

## 4. UX & Design

### Layout / Wireframe

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                                                         │
│                                                         │
│                                                         │
│                                                         │
│                                                         │
│                    ░░░░░░ love the  [visible words]     │
│                                                         │
│                                                         │
│                                                         │
│                                                         │
│  06:42                                    312 / 750     │
└─────────────────────────────────────────────────────────┘
```

- Clock: bottom-left
- Word count: bottom-right
- Text: centered vertically and horizontally; only trailing words visible
- Everything else: pure black

### Interaction Model

1. App launches directly into writing mode — no splash, no menu
2. User types; characters appear in a single line (or wrapped short block) of trailing text
3. Older words fade progressively from visible → dim → invisible (black)
4. Backspace is fully disabled — all keypresses are ignored except printable characters, space, and Enter
5. On reaching word target:
   - File is written to disk
   - Subtle color or text change signals completion (e.g. word count turns green, brief message)
   - App may stay open for continued writing or allow graceful exit
6. Closing the app before target: data is lost (by design — this is the commitment mechanic)

### Visual Design Principles

- **Aesthetic:** monastic, austere, almost brutalist — writing as discipline
- **Background:** pure black (`#000000`)
- **Text:** white or off-white, monospace font (e.g. iA Writer Mono, Courier, or system mono)
- **Fade:** words graduate from full opacity → 0 over a window of ~5–6 words
- **HUD elements** (clock, count): small, dim — present but not demanding attention
- **Completion state:** minimal — a color shift, not a modal or sound

---

## 5. Technical Considerations

**Platform / Target:** macOS desktop (primary); cross-platform possible later

**Language / Framework:** Electron + React. Resolved: Q-03.
- Main process: Node.js / Electron for file system access and window management
- Renderer process: React for UI; no UI framework (no MUI, no Tailwind) — custom CSS only to keep the interface honest

**Key Dependencies:**
- File system access (read/write dated text files)
- System clock
- Word count logic (whitespace tokenization)

**Data Model:**
- Session: plain `.txt` file, named `YYYY-MM-DD.txt`
- In-memory buffer holds text until target reached, then flushed to disk
- No database, no metadata file (v1)

**Persistence Strategy:**
- Write-once-on-completion model
- Buffer in memory (string) during session
- On target reached: `fs.writeFile` (or equivalent) to output dir

**Performance Constraints:**
- Text input must have zero perceptible latency
- Fade/opacity calculation must not block the input thread
- Should handle sessions up to ~10,000 words without degradation

**Security Considerations:**
- Output directory should be user-owned; no network access
- No telemetry, no external calls

---

## 6. Architecture

```
┌──────────────────────────────────────────┐
│               App Shell                  │
│  (full-screen window, keyboard capture)  │
└───────────────┬──────────────────────────┘
                │
       ┌────────▼─────────┐
       │   Writing Engine  │
       │  - keystroke handler
       │  - in-memory buffer
       │  - word tokenizer │
       └────────┬─────────┘
                │
    ┌───────────┼──────────────┐
    │           │              │
┌───▼───┐  ┌───▼───┐  ┌───────▼──────┐
│  HUD  │  │ Fade  │  │ Persistence  │
│ Layer │  │Renderer│  │   Manager   │
│clock  │  │(canvas │  │(write on    │
│wcount │  │ or CSS)│  │ target hit) │
└───────┘  └───────┘  └─────────────┘
```

### Key Modules / Components

| Module | Responsibility |
|--------|---------------|
| App Shell | Full-screen window, OS integration, keyboard capture |
| Writing Engine | Receives keystrokes, maintains in-memory text buffer, tokenizes words |
| Fade Renderer | Displays only the trailing N words with opacity gradient |
| HUD Layer | Renders clock (time of day) and word count / target |
| Persistence Manager | Monitors word count; writes file to disk on target reached |

---

## 7. Implementation Plan

### Milestones

| # | Milestone | Deliverable | Depends On |
|---|-----------|-------------|------------|
| M-1 | Project scaffold | Electron + React project, full-screen window boots | — |
| M-2 | Core writing loop | Typing input → in-memory buffer, raw text visible | M-1 |
| M-3 | Fade effect | Trailing-words-only display with opacity gradient | M-2 |
| M-4 | HUD | Clock and word count on screen | M-2 |
| M-5 | Persistence | Save on target; date-named file | M-4 |
| M-6 | Completion state | Visual signal on save | M-5 |
| M-7 | Polish & config | Target/dir config, "done for today" screen, edge cases | M-6 |

### Tasks — M-2 (Core writing loop)

- [ ] Scaffold project (package.json / Xcode project / etc.)
- [ ] Full-screen window, black background, no chrome
- [ ] Capture all keyboard input, suppress default OS behaviors
- [ ] Append printable characters to in-memory string buffer
- [ ] Render buffer text to screen (raw, unformatted)

### Tasks — M-3 (Fade effect)

- [ ] Tokenize buffer into words
- [ ] Determine last N words (configurable, default 6)
- [ ] Render each word with opacity proportional to recency
- [ ] Hide all text before the fade window

---

## 8. Open Questions

| # | Question | Owner | Resolution |
|---|----------|-------|------------|
| Q-01 | Should backspace be allowed? If so, scope: current word only, or free? Or disabled entirely? | — | **Resolved: Disabled entirely.** |
| Q-02 | If today's file already exists (user already hit target): re-open for append? Block session? Prompt? | — | **Resolved: Block. One session per day, no append.** |
| Q-03 | Tech stack: Electron, Swift/SwiftUI, or Tauri? macOS-only or cross-platform target? | — | **Resolved: Electron + React.** |
| Q-04 | Should the fade window be fixed (6 words) or dynamic (fade over a fixed pixel/character width)? | — | — |
| Q-05 | Should elapsed session time be shown in v1, or deferred? | — | — |
| Q-06 | What happens if the user force-quits mid-session — is partial work recoverable? | — | — |

---

## 9. Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-01 | File not saved until target hit | Core commitment mechanic — the save is the reward |
| 2026-03-01 | No editing / backward navigation | Enforces forward-only flow; editing breaks the freewrite state |
| 2026-03-01 | Plain `.txt` output | Future-proof, portable, no lock-in |
| 2026-03-01 | Backspace fully disabled | Enforces the freewrite contract — what is written cannot be unwritten |
| 2026-03-01 | One session per day; block if file exists | The daily page is a singular commitment, not a scratchpad |
| 2026-03-01 | Electron + React | Cross-platform, faster to build, sufficient for this workload |

---

## 10. Running the App

```bash
# Development (Electron loads from Vite dev server with HMR)
npm run dev

# Production build then run
npm run build && npm start
```

Output files are written to `~/WritLarge/YYYY-MM-DD.txt`.
Config can be customised by editing `~/Library/Application Support/writlarge/config.json`:
```json
{
  "wordTarget": 750,
  "outputDir": "/Users/you/WritLarge"
}
```

---

## 11. Appendix

### Prior Art / Inspiration
- [750words.com](https://750words.com) — web-based daily writing, 750-word target (Morning Pages)
- [iA Writer](https://ia.net/writer) — focus mode, minimal UI
- [OmmWriter](https://www.ommwriter.com) — immersive, full-screen writing
- [Write or Die](https://writeordie.com) — commitment mechanic (consequences for stopping)
- Julia Cameron's *The Artist's Way* — origin of "Morning Pages" practice (750 words ~ 3 pages longhand)

### Word Count Target Rationale
750 words ≈ 3 handwritten pages, the canonical Morning Pages length. Configurable to suit other practices (e.g. NaNoWriMo daily targets).
