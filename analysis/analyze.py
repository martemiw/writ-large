#!/usr/bin/env python3
"""Keystroke timing analysis — produces a markdown report."""

import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

# ── I/O paths ─────────────────────────────────────────────────────────────────
INPUT_FILE = Path(__file__).parent / "input" / "2026-03-08.keys.json"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "2026-03-08-analysis.md"

OUTPUT_DIR.mkdir(exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
with open(INPUT_FILE) as f:
    data = json.load(f)

start_ts = data["start"]
keys = data["keys"]  # list of {"k": str, "d": int}

# ── Helper stats ──────────────────────────────────────────────────────────────
def stats(values):
    """Return dict of count/mean/median/stddev/min/max/p10/p90."""
    if not values:
        return {}
    s = sorted(values)
    n = len(s)
    mean = sum(s) / n
    variance = sum((x - mean) ** 2 for x in s) / n
    stddev = math.sqrt(variance)

    def pct(p):
        idx = (n - 1) * p / 100
        lo, hi = int(idx), min(int(idx) + 1, n - 1)
        return s[lo] + (s[hi] - s[lo]) * (idx - lo)

    return {
        "n": n,
        "mean": mean,
        "median": pct(50),
        "stddev": stddev,
        "min": s[0],
        "max": s[-1],
        "p10": pct(10),
        "p90": pct(90),
    }


def fmt(v, decimals=0):
    return f"{v:.{decimals}f}"


def stats_row(label, s, unit="ms"):
    if not s:
        return f"| {label} | — | — | — | — | — | — | — |"
    return (
        f"| {label} "
        f"| {fmt(s['mean'])} "
        f"| {fmt(s['median'])} "
        f"| {fmt(s['stddev'])} "
        f"| {fmt(s['min'])} "
        f"| {fmt(s['max'])} "
        f"| {fmt(s['p10'])} "
        f"| {fmt(s['p90'])} |"
    )


# ── Categorise keys ───────────────────────────────────────────────────────────
LETTERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITS = set("0123456789")
PUNCT = set(".,;:!?-—'\"()[]{}…")
SPACE = {" "}
NEWLINE = {"\n", "\r", "Enter", "Return"}

all_delays = [e["d"] for e in keys if e["d"] > 0]  # skip first keystroke (d=0)

# Per-key delays
per_key = defaultdict(list)
for e in keys:
    if e["d"] > 0:
        per_key[e["k"]].append(e["d"])

# Category buckets
cat_delays = defaultdict(list)
for e in keys:
    k, d = e["k"], e["d"]
    if d == 0:
        continue
    if k in LETTERS:
        cat_delays["letters"].append(d)
        cat_delays[("lower" if k.islower() else "upper")].append(d)
    elif k in SPACE:
        cat_delays["space"].append(d)
    elif k in NEWLINE:
        cat_delays["newline"].append(d)
    elif k in DIGITS:
        cat_delays["digits"].append(d)
    elif k in PUNCT:
        cat_delays["punctuation"].append(d)
    else:
        cat_delays["other"].append(d)

# ── Doublet analysis ──────────────────────────────────────────────────────────
# For each bigram AB, record delay of B (d of B, given preceding key was A)
doublet_delays = defaultdict(list)  # bigram str → [d]
first_key_delays = defaultdict(list)  # first key char → [d of second key]

for i in range(1, len(keys)):
    prev_k = keys[i - 1]["k"]
    curr = keys[i]
    if curr["d"] == 0:
        continue
    bigram = prev_k + curr["k"]
    doublet_delays[bigram].append(curr["d"])
    first_key_delays[prev_k].append(curr["d"])

# ── Rhythm / burst analysis ────────────────────────────────────────────────────
PAUSE_THRESHOLD = 1000  # ms — considered a "thinking pause"
BURST_GAP = 300          # ms — within a burst

bursts = []
current_burst = [keys[0]]
for e in keys[1:]:
    if e["d"] > BURST_GAP:
        if len(current_burst) > 1:
            bursts.append(current_burst)
        current_burst = [e]
    else:
        current_burst.append(e)
if len(current_burst) > 1:
    bursts.append(current_burst)

burst_lengths = [len(b) for b in bursts]
burst_speeds = []  # avg delay within burst (excluding first)
for b in bursts:
    ds = [x["d"] for x in b if x["d"] > 0]
    if ds:
        burst_speeds.append(sum(ds) / len(ds))

pauses = [e["d"] for e in keys if e["d"] > PAUSE_THRESHOLD]

# ── Session overview ──────────────────────────────────────────────────────────
total_keys = len(keys)
total_ms = sum(e["d"] for e in keys)
total_sec = total_ms / 1000
total_min = total_sec / 60

# Word count estimate (spaces + newlines + 1)
word_count = sum(1 for e in keys if e["k"] in SPACE | NEWLINE) + 1

# Effective WPM (total time / word count)
wpm = word_count / total_min if total_min > 0 else 0

# ── Top-50 most common keys ───────────────────────────────────────────────────
key_freq = defaultdict(int)
for e in keys:
    key_freq[e["k"]] += 1
top_keys = sorted(key_freq.items(), key=lambda x: -x[1])[:50]

# ── Doublet table: top 30 by count, min 5 occurrences ────────────────────────
doublet_stats = {}
for bigram, delays in doublet_delays.items():
    if len(delays) >= 5:
        doublet_stats[bigram] = stats(delays)

top_doublets_by_count = sorted(doublet_stats.items(), key=lambda x: -x[1]["n"])[:40]
top_doublets_fastest = sorted(doublet_stats.items(), key=lambda x: x[1]["median"])[:20]
top_doublets_slowest = sorted(doublet_stats.items(), key=lambda x: -x[1]["median"])[:20]

# ── First-key: after which key is the next fastest/slowest? ──────────────────
fk_stats = {}
for k, ds in first_key_delays.items():
    if len(ds) >= 10:
        fk_stats[k] = stats(ds)

fk_fastest = sorted(fk_stats.items(), key=lambda x: x[1]["median"])[:15]
fk_slowest = sorted(fk_stats.items(), key=lambda x: -x[1]["median"])[:15]

# ── Letter-pair heatmap data (letter→letter only, median delay) ───────────────
letter_pair_med = {}
for bigram, delays in doublet_delays.items():
    a, b = bigram[0], bigram[1]
    if a.lower() in "abcdefghijklmnopqrstuvwxyz" and b.lower() in "abcdefghijklmnopqrstuvwxyz":
        if len(delays) >= 3:
            s2 = stats(delays)
            letter_pair_med[bigram.lower()] = s2["median"]

# ── Speed over time (decile buckets) ─────────────────────────────────────────
bucket_count = 10
bucket_size = total_keys // bucket_count
speed_over_time = []
for i in range(bucket_count):
    chunk = keys[i * bucket_size: (i + 1) * bucket_size]
    ds = [e["d"] for e in chunk if e["d"] > 0]
    if ds:
        speed_over_time.append((i + 1, stats(ds)))

# ─────────────────────────────────────────────────────────────────────────────
# Build report
# ─────────────────────────────────────────────────────────────────────────────
lines = []
W = lines.append

W("# Keystroke Timing Analysis — 2026-03-08")
W("")
W("> **File:** `2026-03-08.keys.json`  ")
W(f"> **Total keystrokes:** {total_keys:,}  ")
W(f"> **Session duration:** {total_min:.1f} min ({total_sec:.0f} s)  ")
W(f"> **Estimated word count:** {word_count:,}  ")
W(f"> **Effective WPM:** {wpm:.1f}")
W("")

# ── 1. Overall Stats ──────────────────────────────────────────────────────────
W("---")
W("")
W("## 1. Overall Delay Statistics")
W("")
W("Delay = milliseconds between consecutive keystrokes.  ")
W("First keystroke has d=0 and is excluded from all stats.")
W("")
W("| Category | Mean | Median | StdDev | Min | Max | P10 | P90 |")
W("|----------|-----:|-------:|-------:|----:|----:|----:|----:|")
W(stats_row("All keys", stats(all_delays)))
for cat in ["letters", "lower", "upper", "space", "newline", "punctuation", "digits"]:
    if cat_delays[cat]:
        W(stats_row(cat.capitalize(), stats(cat_delays[cat])))
W("")

# ── 2. Per-key stats (frequent keys) ─────────────────────────────────────────
W("---")
W("")
W("## 2. Per-Key Statistics (keys with ≥ 20 occurrences)")
W("")
W("Delays are for **arriving at** that key (time since previous keystroke).")
W("")
W("| Key | Count | Mean | Median | StdDev | P10 | P90 |")
W("|-----|------:|-----:|-------:|-------:|----:|----:|")

eligible = {k: v for k, v in per_key.items() if len(v) >= 20}
for k, delays in sorted(eligible.items(), key=lambda x: stats(x[1])["median"]):
    s = stats(delays)
    label = repr(k) if k in (" ", "\n", "\r") else k
    W(f"| `{label}` | {s['n']} | {fmt(s['mean'])} | {fmt(s['median'])} | {fmt(s['stddev'])} | {fmt(s['p10'])} | {fmt(s['p90'])} |")
W("")

# ── 3. Key Frequency ─────────────────────────────────────────────────────────
W("---")
W("")
W("## 3. Key Frequency (top 30)")
W("")
W("| Rank | Key | Count | % of total |")
W("|-----:|-----|------:|-----------:|")
for rank, (k, cnt) in enumerate(top_keys[:30], 1):
    label = repr(k) if k in (" ", "\n", "\r") else k
    pct = 100 * cnt / total_keys
    W(f"| {rank} | `{label}` | {cnt:,} | {pct:.1f}% |")
W("")

# ── 4. Doublet analysis ───────────────────────────────────────────────────────
W("---")
W("")
W("## 4. Doublet (Bigram) Analysis")
W("")
W("A *doublet* AB records the delay of keystroke B given that A was the immediately preceding keystroke.")
W("Only bigrams with ≥ 5 observations are included.")
W("")

W("### 4a. Most Common Doublets (top 40, sorted by count)")
W("")
W("| Bigram | Count | Mean | Median | StdDev | P10 | P90 |")
W("|--------|------:|-----:|-------:|-------:|----:|----:|")
for bigram, s in top_doublets_by_count:
    disp = bigram.replace("|", "\\|").replace(" ", "·").replace("\n", "↵")
    W(f"| `{disp}` | {s['n']} | {fmt(s['mean'])} | {fmt(s['median'])} | {fmt(s['stddev'])} | {fmt(s['p10'])} | {fmt(s['p90'])} |")
W("")

W("### 4b. Fastest Doublets (lowest median delay, top 20)")
W("")
W("| Bigram | Count | Median | Mean | StdDev |")
W("|--------|------:|-------:|-----:|-------:|")
for bigram, s in top_doublets_fastest:
    disp = bigram.replace("|", "\\|").replace(" ", "·").replace("\n", "↵")
    W(f"| `{disp}` | {s['n']} | {fmt(s['median'])} | {fmt(s['mean'])} | {fmt(s['stddev'])} |")
W("")

W("### 4c. Slowest Doublets (highest median delay, top 20)")
W("")
W("| Bigram | Count | Median | Mean | StdDev |")
W("|--------|------:|-------:|-----:|-------:|")
for bigram, s in top_doublets_slowest:
    disp = bigram.replace("|", "\\|").replace(" ", "·").replace("\n", "↵")
    W(f"| `{disp}` | {s['n']} | {fmt(s['median'])} | {fmt(s['mean'])} | {fmt(s['stddev'])} |")
W("")

# ── 5. First-key effect ───────────────────────────────────────────────────────
W("---")
W("")
W("## 5. Preceding-Key Effect")
W("")
W("After typing key X, how quickly does the *next* key tend to arrive?  ")
W("(Median of all delays where X was the preceding key, ≥ 10 observations.)")
W("")
W("### Fastest successors (after these keys, the next key comes quickly)")
W("")
W("| Preceding key | Count | Median next-delay |")
W("|---------------|------:|------------------:|")
for k, s in fk_fastest:
    label = repr(k) if k in (" ", "\n", "\r") else k
    W(f"| `{label}` | {s['n']} | {fmt(s['median'])} ms |")
W("")

W("### Slowest successors (after these keys, the next key is delayed)")
W("")
W("| Preceding key | Count | Median next-delay |")
W("|---------------|------:|------------------:|")
for k, s in fk_slowest:
    label = repr(k) if k in (" ", "\n", "\r") else k
    W(f"| `{label}` | {s['n']} | {fmt(s['median'])} ms |")
W("")

# ── 6. Pause analysis ─────────────────────────────────────────────────────────
W("---")
W("")
W("## 6. Pause Analysis (gaps > 1 s)")
W("")
pause_s = stats(pauses)
W(f"- **Pause count (>1 s):** {pause_s.get('n', 0):,}")
W(f"- **Pause share of total keys:** {100*pause_s.get('n',0)/total_keys:.1f}%")
if pause_s:
    W(f"- **Mean pause:** {pause_s['mean']:.0f} ms")
    W(f"- **Median pause:** {pause_s['median']:.0f} ms")
    W(f"- **Longest pause:** {pause_s['max']:.0f} ms ({pause_s['max']/1000:.1f} s)")
    W(f"- **Total time in pauses:** {sum(pauses)/1000:.1f} s ({100*sum(pauses)/total_ms:.1f}% of session)")
W("")

# Pause context: what key precedes the longest pauses?
pause_contexts = [(keys[i]["k"], keys[i]["d"]) for i in range(1, len(keys)) if keys[i]["d"] > PAUSE_THRESHOLD]
pause_by_trigger = defaultdict(list)
for k, d in pause_contexts:
    pause_by_trigger[k].append(d)

W("### Keys that tend to precede long pauses")
W("")
W("| Key | # pauses | Median pause |")
W("|-----|--------:|-------------:|")
pb_sorted = sorted(pause_by_trigger.items(), key=lambda x: -len(x[1]))[:15]
for k, ds in pb_sorted:
    label = repr(k) if k in (" ", "\n", "\r") else k
    med = sorted(ds)[len(ds) // 2]
    W(f"| `{label}` | {len(ds)} | {med:.0f} ms |")
W("")

# ── 7. Speed over time ────────────────────────────────────────────────────────
W("---")
W("")
W("## 7. Speed Over Time (session deciles)")
W("")
W("Session split into 10 equal chunks by keystroke count.")
W("")
W("| Decile | Key range | Mean delay | Median delay | StdDev |")
W("|-------:|----------:|-----------:|-------------:|-------:|")
for decile, s in speed_over_time:
    lo = (decile - 1) * bucket_size + 1
    hi = decile * bucket_size
    W(f"| {decile} | {lo}–{hi} | {fmt(s['mean'])} ms | {fmt(s['median'])} ms | {fmt(s['stddev'])} ms |")
W("")

# ── 8. Burst analysis ─────────────────────────────────────────────────────────
W("---")
W("")
W("## 8. Typing Burst Analysis")
W("")
W(f"A *burst* is a run of keystrokes each separated by ≤ {BURST_GAP} ms.  ")
W(f"Bursts of length ≥ 2 only.")
W("")
bs = stats(burst_lengths)
bsp = stats(burst_speeds)
W(f"- **Total bursts:** {bs.get('n', 0):,}")
if bs:
    W(f"- **Median burst length:** {bs['median']:.0f} keys")
    W(f"- **Mean burst length:** {bs['mean']:.1f} keys")
    W(f"- **Longest burst:** {bs['max']:.0f} keys")
    W(f"- **Median within-burst speed:** {bsp['median']:.0f} ms/key")
    W(f"- **Mean within-burst speed:** {bsp['mean']:.1f} ms/key")
W("")

# Burst length distribution
length_dist = defaultdict(int)
for bl in burst_lengths:
    bucket = min(bl // 5 * 5, 50)  # bucket by 5, cap at 50+
    length_dist[bucket] += 1

W("### Burst length distribution")
W("")
W("| Length bucket | Count |")
W("|---------------|------:|")
for lb in sorted(length_dist):
    label = f"{lb}–{lb+4}" if lb < 50 else "50+"
    W(f"| {label} keys | {length_dist[lb]} |")
W("")

# ── 9. Notable patterns ───────────────────────────────────────────────────────
W("---")
W("")
W("## 9. Notable Patterns & Observations")
W("")

# Rhythmic regularity: CV of all delays
all_s = stats(all_delays)
cv = all_s["stddev"] / all_s["mean"] * 100 if all_s["mean"] else 0

# Speed warmup: compare first vs last decile
first_dec = speed_over_time[0][1] if speed_over_time else None
last_dec = speed_over_time[-1][1] if speed_over_time else None
warmup_delta = (last_dec["median"] - first_dec["median"]) if first_dec and last_dec else 0

# Most consistent doublets (low CV)
consistent_doublets = []
for bigram, s in doublet_stats.items():
    if s["n"] >= 10 and s["mean"] > 0:
        dcv = s["stddev"] / s["mean"] * 100
        consistent_doublets.append((bigram, dcv, s))
consistent_doublets.sort(key=lambda x: x[1])

# High-variance doublets
inconsistent_doublets = sorted(consistent_doublets, key=lambda x: -x[1])

W(f"- **Typing rhythm (CoV of all delays):** {cv:.1f}%  ")
W(f"  A low CoV indicates metronomic typing; higher values reflect bursts and pauses.")
W("")
if warmup_delta:
    direction = "faster" if warmup_delta < 0 else "slower"
    W(f"- **Warmup effect:** Median delay shifted by {abs(warmup_delta):.0f} ms from decile 1 → 10 ({direction} over session).")
W("")

W("- **Top 10 most consistent doublets** (lowest delay coefficient of variation):")
W("")
W("  | Bigram | Median | StdDev | CoV |")
W("  |--------|-------:|-------:|----:|")
for bigram, dcv, s in consistent_doublets[:10]:
    disp = bigram.replace("|", "\\|").replace(" ", "·").replace("\n", "↵")
    W(f"  | `{disp}` | {fmt(s['median'])} ms | {fmt(s['stddev'])} ms | {dcv:.0f}% |")
W("")

W("- **Top 10 most variable doublets** (highest CoV, potential hesitation points):")
W("")
W("  | Bigram | Median | StdDev | CoV |")
W("  |--------|-------:|-------:|----:|")
for bigram, dcv, s in inconsistent_doublets[:10]:
    disp = bigram.replace("|", "\\|").replace(" ", "·").replace("\n", "↵")
    W(f"  | `{disp}` | {fmt(s['median'])} ms | {fmt(s['stddev'])} ms | {dcv:.0f}% |")
W("")

# Space-key pattern: space is often the "reset" between words
space_s = stats(cat_delays["space"])
letter_s = stats(cat_delays["letters"])
if space_s and letter_s:
    ratio = space_s["median"] / letter_s["median"]
    W(f"- **Space vs letter speed ratio:** Space key median = {space_s['median']:.0f} ms vs letter median = {letter_s['median']:.0f} ms (ratio {ratio:.2f}x).  ")
    if ratio > 1.2:
        W("  Space tends to arrive **slower** than letters, suggesting word-boundary micro-pauses.")
    elif ratio < 0.85:
        W("  Space tends to arrive **faster** than letters, suggesting eager word separation.")
    else:
        W("  Space and letter speeds are broadly similar.")
W("")

# Repeated-letter doublets
W("- **Same-key doublets** (e.g. `ll`, `tt`, `ss`):")
W("")
W("  | Bigram | Count | Median |")
W("  |--------|------:|-------:|")
same_key = [(b, s) for b, s in doublet_stats.items() if len(b) == 2 and b[0].lower() == b[1].lower()]
same_key.sort(key=lambda x: -x[1]["n"])
for bigram, s in same_key[:10]:
    disp = bigram.replace("|", "\\|")
    W(f"  | `{disp}` | {s['n']} | {fmt(s['median'])} ms |")
W("")

W("---")
W("")
W("*Generated by `analysis/analyze.py`*")

# ── Write file ────────────────────────────────────────────────────────────────
report = "\n".join(lines)
OUTPUT_FILE.write_text(report)
print(f"Report written to {OUTPUT_FILE}")
print(f"Total keystrokes: {total_keys:,}")
print(f"Unique keys seen: {len(per_key)}")
print(f"Unique bigrams (≥5): {len(doublet_stats)}")
