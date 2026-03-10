# Software Requirements — Edit Mode

---

## 1. Overview

**Product Name:** WritLarge
**Feature Name:** Edit Mode
**Date:** 2026-03-09
**Status:** `Draft`

### Problem Statement
Morning Pages sessions produce plain-text artifacts. Right now there is no way to return to them inside WritLarge — you have to leave the app. Writers need a focused, distraction-free way to read and navigate their own writing without reaching for a general-purpose editor.

### Goal
Provide a read/navigate mode inside WritLarge where the writer can select a previous session and move through it with keyboard-driven cursor navigation, in the same aesthetic as the rest of the app.

### Non-Goals
- Text editing (insertion, deletion, undo) — not in v1
- Saving any changes — not in v1
- Access to Free Write files or external files — not in v1 (morning pages only)
- Search, find/replace, annotations — future
- Mouse interaction in the editor — future

---

## 2. User & Context

**Primary User:** The writer, after a session or on a later day, wanting to revisit what they wrote.
**User Context:** Quiet reading/reflection; same focused, full-screen environment as writing.
**Success Looks Like:** Writer selects a file, is immersed in the text with no chrome, and can comfortably read through it using only the keyboard.

---

## 3. Functional Requirements

| # | Requirement | Priority | Notes |
|---|-------------|----------|-------|
| F-01 | EDIT item appears in the title screen menu, below FREE WRITE | MUST | |
| F-02 | File picker lists all `YYYY-MM-DD.txt` morning pages files, newest first | MUST | Files from `config.outputDir` |
| F-03 | Picker shows filename (date) only — no word count | MUST | |
| F-04 | Selecting a file opens the editor | MUST | |
| F-05 | Document is rendered at a fixed novel-width column (≈ 65 ch) horizontally centered | MUST | |
| F-06 | Active cursor line is fixed at the vertical midpoint of the screen (typewriter scroll) | MUST | Document scrolls, cursor row stays fixed |
| F-07 | Text above the cursor is visible, scrolling upward as cursor moves down | MUST | |
| F-08 | Text below the cursor fades to black | MUST | Same fade-to-black aesthetic as writing mode |
| F-09 | Arrow Up / Arrow Down moves the cursor one visual row at a time; the document scrolls accordingly | MUST | |
| F-10 | Arrow Left / Arrow Right moves the cursor one character at a time | MUST | |
| F-11 | Pressing `w` toggles **Word Mode**; pressing `w` again (or `Escape`) returns to Character Mode | MUST | Mode persists until explicitly toggled off |
| F-12 | In Word Mode, `←` / `→` moves the cursor one word at a time | MUST | |
| F-13 | In Word Mode, `↓` moves to the start of the word closest horizontally on the next visual row | MUST | Not straight-column — nearest word boundary |
| F-14 | In Word Mode, `↑` moves to the start of the word closest horizontally on the previous visual row | MUST | Symmetric with F-13 |
| F-15 | A mode indicator bar is permanently visible at the bottom of the screen | MUST | Shows current mode and the key to toggle |
| F-16 | `←` / `→` wrap across visual row boundaries (end of row → start of next, and vice versa) | MUST | |
| F-17 | Navigation at the first or last row of the document is a no-op | MUST | |
| F-18 | `Escape` exits the editor and returns to the title screen (and exits Word Mode if active) | MUST | No save prompt (read-only) |
| F-19 | Cursor position (line, char) shown in HUD | SHOULD | Bottom of screen, same HUD style |

---

## 4. UX & Design

### Layout / Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                                                                 │
│         ...text above cursor scrolls up and fades...           │
│                                                                 │
│         I woke up thinking about the conversation we           │
│         had last Tuesday, and how strange it felt to           │
│─ ─ ─ ─ [cursor here, mid-screen] ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
│         admit that I had been wrong the whole time.            │  ← fades
│         The light was doing something odd through              │  ← fades more
│         the curtain, and I remember thinking—                  │  ← fades more
│                                                                 │  ← black (~8 lines out)
│                                                                 │
│  YYYY-MM-DD                             line 12 / 48           │  ← HUD
│  char  ·  w → word                                             │  ← mode bar
└─────────────────────────────────────────────────────────────────┘

Word Mode active:
│  word  ·  w → char                                             │  ← mode bar (brighter)
```

The cursor line is always at `50vh`. Text above it is fully visible. Text below it fades to black progressively over ~8 lines.

### Interaction Model

**File picker:**
- Arrow Up/Down to move highlight; Enter to open; Escape to go back to title.
- Shows a numbered list of available morning pages, newest at top.

**Editor navigation:**
- All navigation is cursor-relative; the viewport is locked — only the document moves.
- Two modes: **Character Mode** (default) and **Word Mode**.
- `w` — toggle between Character Mode and Word Mode.
- **Character Mode:** `←` `→` move one character; wrap across visual row boundaries. `↑` `↓` move one visual row with sticky column.
- **Word Mode:** `←` `→` jump to start of previous/next word. `↑` `↓` jump to the start of the word nearest horizontally on the previous/next visual row.
- Navigation past the first or last row is a no-op.
- `Escape` — exit Word Mode if active, otherwise exit to title screen.

**Mode indicator bar:**
- Always visible at the very bottom of the screen, below the HUD.
- In Character Mode: shows `char  ·  w → word`
- In Word Mode: shows `word  ·  w → char` (or similar, visually distinct — e.g. highlighted or brighter)

### Visual Design Principles
- Full-screen black background; same font (Courier New) and color palette as the rest of the app.
- Novel width: ≈ 65 ch, centered. This matches a standard paperback line length.
- Cursor: blinking underscore or block, same blink timing as writing mode.
- Fade below: the same `mask-image` gradient approach used in writing mode, applied vertically to the lines below the cursor row.
- No scrollbars, no line numbers visible in the text area.

---

## 5. Technical Considerations

**Platform / Target:** Desktop (Electron + React) first; CLI parity to follow
**Language / Framework:** React 18, same component patterns as existing screens
**Key Dependencies:** None new
**Data Model:** Reads existing `YYYY-MM-DD.txt` files from `config.outputDir`; read-only
**Persistence Strategy:** None — no writes in v1
**Performance Constraints:** Files are ≤ 1,500 words / ~8 KB; no pagination needed

### Word wrapping
Text must be word-wrapped at the novel width (65 ch) client-side to determine visual rows. All cursor movement and row calculations operate on visual (wrapped) rows, not logical (newline) lines.

---

## 6. Architecture

```
TitleScreen  →  FilePickerScreen  →  EditorScreen
                    |                     |
              lists *.txt files     EditorCanvas
              from outputDir           FadeBelow
                                       HUD (line / total)
```

### Key Modules / Components

| Module | Responsibility |
|--------|----------------|
| `FilePickerScreen` | List and select morning pages files |
| `EditorCanvas` | Render document at novel width; typewriter scroll; cursor |
| `FadeBelow` | CSS/DOM fade applied to lines below the cursor row |
| `useEditorNav` | Hook encapsulating cursor position, word-wrap layout, all key handlers |
| `wrapText(text, cols)` | Pure function: splits text into visual rows of ≤ cols chars |
| `App.jsx` | New `'picker'` and `'editing'` screen states |
| `electron/main.js` | New `list-pages` IPC: returns sorted list of `{filename, date, words}` |

---

## 7. Implementation Plan

### Milestones

| # | Milestone | Deliverable | Depends On |
|---|-----------|-------------|------------|
| M-1 | IPC + file listing | `list-pages` handler; FilePickerScreen renders list | — |
| M-2 | Text layout engine | `wrapText`, visual row model, cursor address type | M-1 |
| M-3 | EditorCanvas render | Document at novel width, cursor at mid-screen, static | M-2 |
| M-4 | Basic navigation | Arrow keys scroll document; sticky-column ↑↓; char ←→ | M-3 |
| M-5 | Word navigation | Alt+←→ word jump; Alt+↑↓ nearest-word-on-row | M-4 |
| M-6 | Fade below + HUD | CSS fade on lines below cursor; line/total counter | M-5 |

---

## 8. Open Questions

| # | Question | Owner | Resolution |
|---|----------|-------|------------|
| Q-01 | Modifier key approach | — | Resolved: `w` key toggles Word Mode (no held modifier needed) |
| Q-02 | Should the cursor wrap left/right across line boundaries? | — | Resolved: yes, wraps |
| Q-03 | What should Up/Down do at the very first / very last row? | — | Resolved: no-op |
| Q-04 | Should the file picker also show free-write files? | — | Resolved: morning pages only for now |
| Q-05 | CLI parity: include in v1 or defer? | — | Resolved: defer |
| Q-06 | Should word count in the picker come from stats.jsonl (fast) or be recomputed (accurate)? | — | Resolved: no word counts in picker |
| Q-07 | Fade below: how many lines until fully black? | — | Resolved: ~8 lines |
| Q-08 | Does `Escape` first exit Word Mode (if active) then require a second press to exit editor? | — | Resolved: yes — first Escape exits Word Mode, second exits to title |

---

## 9. Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-09 | v1 is read-only — no editing | Complexity of undo/redo and conflict with the forward-only philosophy; get navigation right first |
| 2026-03-09 | Morning pages files only in file picker | User explicitly scoped it this way; free write and other files deferred |
| 2026-03-09 | CLI parity deferred | Desktop first; cursor/navigation model is complex enough to validate on one platform |
| 2026-03-09 | Typewriter scroll (cursor fixed at mid-screen) | Consistent with the rest of WritLarge's "focus on the present" aesthetic |
| 2026-03-09 | Word navigation via `w` mode toggle, not a held modifier | Held modifiers are awkward for extended navigation; a modal approach lets the user relax and use arrow keys naturally |
| 2026-03-09 | `←`/`→` wrap across visual row boundaries | Feels natural; no hard stop at line end |
| 2026-03-09 | `↑`/`↓` at document boundaries are no-ops | Prevents confusion; silent failure is cleaner than a bell or flash |
| 2026-03-09 | Fade below spans ~8 lines | Enough to suggest depth without cutting off too much readable context |
| 2026-03-09 | First `Escape` exits Word Mode; second exits editor | Makes `Escape` always feel safe — it undoes the most recent modal change first |

---

## 10. Appendix

**Novel width reference:** Industry standard for body text is 55–75 characters per line; 65 ch is the midpoint and matches many ebook and paperback formats.

**Prior art within WritLarge:** `FadeText.jsx` uses a horizontal `mask-image` gradient to fade old words left-to-right. The editor will apply a vertical equivalent for lines below the cursor.
