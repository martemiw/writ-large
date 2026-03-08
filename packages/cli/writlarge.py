#!/usr/bin/env python3
"""
WritLarge CLI — daily writing practice, forward only.

Mirrors the desktop Electron app exactly:
  • Reads config from ~/Library/Application Support/writlarge/config.json
  • Writes YYYY-MM-DD.txt, YYYY-MM-DD.keys.json, stats.jsonl
    to the same output directory as the desktop app

Usage:
  python3 writlarge.py
  chmod +x writlarge.py && ./writlarge.py
"""

import curses
import json
import os
import time
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

def get_config():
    config_path = Path.home() / 'Library' / 'Application Support' / 'writlarge' / 'config.json'
    defaults = {
        'wordTarget': 750,
        'outputDir': str(Path.home() / 'WritLarge'),
    }
    try:
        if config_path.exists():
            return {**defaults, **json.loads(config_path.read_text())}
    except Exception:
        pass
    return defaults

def get_output_dir(config):
    d = config['outputDir']
    return Path(d.replace('~', str(Path.home()), 1) if d.startswith('~') else d)

def today_date():
    return time.strftime('%Y-%m-%d')

def now_time():
    return time.strftime('%H:%M:%S')

def get_today_path(config):
    return get_output_dir(config) / f'{today_date()}.txt'

# ── Text helpers ──────────────────────────────────────────────────────────────

def count_words(text):
    return len(text.split())

def format_elapsed(s):
    return f'{s // 60:02d}:{s % 60:02d}'

def calc_median(keystrokes):
    deltas = sorted(k['d'] for k in keystrokes if k['d'] > 0)
    if not deltas:
        return 0
    mid = len(deltas) // 2
    if len(deltas) % 2 == 0:
        return round((deltas[mid - 1] + deltas[mid]) / 2)
    return deltas[mid]

# ── File I/O ──────────────────────────────────────────────────────────────────

def save_session(text, keystrokes, start_ms, median_ms, elapsed_s, config):
    out = get_output_dir(config)
    out.mkdir(parents=True, exist_ok=True)
    date = today_date()

    # 1. Plain text (matches desktop exactly)
    text_path = out / f'{date}.txt'
    text_path.write_text(text, encoding='utf-8')

    # 2. Keystroke timing
    if keystrokes:
        keys_path = out / f'{date}.keys.json'
        keys_path.write_text(
            json.dumps({'start': start_ms, 'keys': keystrokes}),
            encoding='utf-8'
        )

    # 3. Session stats log
    stats_path = out / 'stats.jsonl'
    entry = json.dumps({
        'date': date,
        'time_of_day': now_time(),
        'words': count_words(text),
        'median_ms': median_ms,
        'duration_s': elapsed_s,
    })
    with open(stats_path, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

    return text_path

# ── Color pairs ───────────────────────────────────────────────────────────────
# Initialised once in setup_colors(); used throughout.

C_BASE   = 1   # normal white on black
C_DIM    = 2   # dimmed (old words, HUD, secondary text)
C_BRIGHT = 3   # bold white (newest words, headings)
C_MENU   = 4   # selected menu item

def setup_colors():
    curses.start_color()
    try:
        curses.use_default_colors()
        bg = -1
    except Exception:
        bg = curses.COLOR_BLACK

    curses.init_pair(C_BASE,   curses.COLOR_WHITE, bg)
    curses.init_pair(C_DIM,    curses.COLOR_WHITE, bg)
    curses.init_pair(C_BRIGHT, curses.COLOR_WHITE, bg)
    curses.init_pair(C_MENU,   curses.COLOR_WHITE, bg)

def base():   return curses.color_pair(C_BASE)
def dim():    return curses.color_pair(C_DIM)  | curses.A_DIM
def bright(): return curses.color_pair(C_BRIGHT) | curses.A_BOLD

def word_attr(i, n):
    """Return curses attribute for word at position i of n (i=0 is oldest)."""
    frac = i / max(n - 1, 1)
    if frac < 0.30:
        return dim()
    elif frac < 0.65:
        return base()
    else:
        return bright()

# ── Safe draw helper ──────────────────────────────────────────────────────────

def put(scr, y, x, text, attr=0):
    """addstr that silently ignores out-of-bounds errors."""
    h, w = scr.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    text = text[:w - x]
    if text:
        try:
            scr.addstr(y, x, text, attr)
        except curses.error:
            pass

# ── Title screen ──────────────────────────────────────────────────────────────

TITLE_ITEMS = ['MORNING PAGES', 'EXIT']

def run_title(scr):
    """Returns 'write' or 'quit'."""
    curses.curs_set(0)
    scr.timeout(50)
    selected = 0

    while True:
        scr.erase()
        h, w = scr.getmaxyx()
        cx = w // 2

        # Wordmark block — left-aligned around centre, 34 chars wide
        lx = cx - 17
        wordmark = 'W R I T L A R G E'
        sub      = 'DAILY  WRITING  PRACTICE'
        rule     = '─' * max(len(wordmark), len(sub))

        base_y = h // 2 - 6
        put(scr, base_y,     lx, wordmark, bright())
        put(scr, base_y + 1, lx, rule,     dim())
        put(scr, base_y + 2, lx, sub,      dim())
        put(scr, base_y + 3, lx, rule,     dim())

        # Menu
        for i, label in enumerate(TITLE_ITEMS):
            y = base_y + 5 + i * 2
            if i == selected:
                put(scr, y, lx,     '▸', bright())
                put(scr, y, lx + 2, label, bright())
            else:
                put(scr, y, lx,     ' ', dim())
                put(scr, y, lx + 2, label, dim())

        put(scr, base_y + 5 + len(TITLE_ITEMS) * 2 + 1,
            lx, 'ARROW KEYS  ·  ENTER', dim())

        scr.refresh()

        ch = scr.getch()
        if ch in (curses.KEY_UP, ord('k')):
            selected = (selected - 1) % len(TITLE_ITEMS)
        elif ch in (curses.KEY_DOWN, ord('j')):
            selected = (selected + 1) % len(TITLE_ITEMS)
        elif ch in (10, 13):  # Enter
            return 'quit' if selected == 1 else 'write'
        elif ch in (ord('q'), ord('Q'), 27):
            return 'quit'

# ── Blocked screen ────────────────────────────────────────────────────────────

def run_blocked(scr):
    curses.curs_set(0)
    scr.timeout(-1)

    scr.erase()
    h, w = scr.getmaxyx()
    date_str = today_date().upper()
    msg = 'done.'

    put(scr, h // 2 - 1, (w - len(date_str)) // 2, date_str, dim())
    put(scr, h // 2 + 1, (w - len(msg))      // 2, msg,      bright())
    put(scr, h // 2 + 4, (w - 18)            // 2, 'Q TO CLOSE', dim())
    scr.refresh()

    while True:
        ch = scr.getch()
        if ch in (ord('q'), ord('Q'), 27, 10):
            return

# ── Writing screen ────────────────────────────────────────────────────────────

VISIBLE_WORDS = 40    # match FadeText.jsx BUFFER_SIZE
BLINK_HALF   = 0.55   # seconds per half-blink cycle

def render_writing(scr, buffer, cursor_on, elapsed_s, word_count, target):
    scr.erase()
    h, w = scr.getmaxyx()
    mid_y     = h // 2
    cursor_x  = int(w * 0.70)   # right-third, matches desktop

    # ── Text row ──────────────────────────────────────────────────────────────
    words   = buffer.split()
    visible = words[-VISIBLE_WORDS:] if len(words) > VISIBLE_WORDS else words
    n       = len(visible)

    # Build list of (text, attr) segments right-to-left
    # We render from the cursor leftward
    x = cursor_x - 1   # one space gap before cursor
    for i in range(n - 1, -1, -1):
        word = visible[i]
        attr = word_attr(i, n)
        # draw space separator (not before the rightmost word)
        if i < n - 1:
            x -= 1
            if 0 <= x < w:
                put(scr, mid_y, x, ' ', attr)
        # draw word right-to-left character by character
        for ch in reversed(word):
            x -= 1
            if x < 0:
                break
            put(scr, mid_y, x, ch, attr)
        if x < 0:
            break

    # ── Cursor ────────────────────────────────────────────────────────────────
    cursor_char = '_' if cursor_on else ' '
    put(scr, mid_y, cursor_x, cursor_char, base())

    # ── HUD ───────────────────────────────────────────────────────────────────
    hud_y     = h - 3
    time_str  = format_elapsed(elapsed_s)
    count_str = f'{word_count} / {target}'
    count_attr = bright() if word_count >= target else dim()
    put(scr, hud_y, 3,              time_str,  dim())
    put(scr, hud_y, w - len(count_str) - 3, count_str, count_attr)

    scr.refresh()

def run_writing(scr, config):
    """Returns result dict on completion, None if user quit."""
    curses.curs_set(0)
    scr.timeout(50)   # ms; drives blink and timer refresh

    buffer       = ''
    keystrokes   = []
    last_key_ms  = None
    start_ms     = int(time.time() * 1000)
    start_mono   = time.monotonic()
    target       = config.get('wordTarget', 750)
    cursor_on    = True
    last_blink   = time.monotonic()

    while True:
        now = time.monotonic()
        elapsed_s  = int(now - start_mono)
        word_count = count_words(buffer)

        # Blink
        if now - last_blink >= BLINK_HALF:
            cursor_on  = not cursor_on
            last_blink = now

        render_writing(scr, buffer, cursor_on, elapsed_s, word_count, target)

        ch = scr.getch()
        if ch == -1:
            continue   # timeout — just redraw

        # Quit without saving
        if ch in (3, 4, 27):    # Ctrl-C, Ctrl-D, Escape
            return None

        # Backspace / Delete — blocked (forward only)
        if ch in (127, curses.KEY_BACKSPACE, curses.KEY_DC):
            continue

        # Enter
        if ch in (10, 13):
            char = '\n'
        elif 32 <= ch <= 126:
            char = chr(ch)
        else:
            continue   # ignore function keys, arrows, etc.

        # No more input past target
        if word_count >= target:
            continue

        buffer += char

        # Record keystroke timing
        now_ms  = int(time.time() * 1000)
        delta   = 0 if last_key_ms is None else now_ms - last_key_ms
        last_key_ms = now_ms
        keystrokes.append({'k': char, 'd': delta})

        # Check target
        if count_words(buffer) >= target:
            final_s    = int(time.monotonic() - start_mono)
            median_ms  = calc_median(keystrokes)
            text_path  = save_session(buffer, keystrokes, start_ms, median_ms, final_s, config)
            return {
                'word_count': count_words(buffer),
                'elapsed':    final_s,
                'median_ms':  median_ms,
                'path':       str(text_path),
            }

# ── Done screen ───────────────────────────────────────────────────────────────

def run_done(scr, result):
    curses.curs_set(0)
    scr.timeout(-1)

    h, w  = scr.getmaxyx()
    s     = result['elapsed']
    m, s2 = divmod(s, 60)
    time_str = (f'{m} minutes {s2} seconds' if m > 0 else f'{s2} seconds')
    display_path = result['path'].replace(str(Path.home()), '~')

    lines = [
        ('done.',                               bright()),
        ('',                                    0),
        (f"{result['word_count']} words",       base()),
        (time_str,                              base()),
        (f"{result['median_ms']}ms median keystroke", base()),
        ('',                                    0),
        (f'saved to {display_path}',            dim()),
        ('',                                    0),
        ('Q TO CLOSE',                          dim()),
    ]

    scr.erase()
    start_y = max(0, (h - len(lines)) // 2)
    for i, (text, attr) in enumerate(lines):
        put(scr, start_y + i, (w - len(text)) // 2, text, attr)
    scr.refresh()

    while True:
        ch = scr.getch()
        if ch in (ord('q'), ord('Q'), 27, 10):
            return

# ── Entry point ───────────────────────────────────────────────────────────────

def main(scr):
    setup_colors()
    scr.bkgd(' ', curses.color_pair(C_BASE))
    config = get_config()

    action = run_title(scr)
    if action == 'quit':
        return

    if get_today_path(config).exists():
        run_blocked(scr)
        return

    result = run_writing(scr, config)
    if result is None:
        return   # quit mid-session without saving

    run_done(scr, result)


if __name__ == '__main__':
    curses.wrapper(main)
