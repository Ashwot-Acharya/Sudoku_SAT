"""
plot_results.py
───────────────
Reads benchmark_results.csv and produces:
  - One bar chart per Sudoku type  (SAT vs Backtracking, per puzzle)
  - One overview bar chart         (mean times, all types side-by-side)
  - One scaling line chart         (how time grows with puzzle size)

Usage:
    python plot_results.py                              # auto-finds CSV
    python plot_results.py --csv path/to/results.csv
    python plot_results.py --csv results.csv --out ./plots/
"""

import os, sys, csv, math, argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── colours & style ────────────────────────────────────────────
C_SAT     = "#4C72B0"   # compact blue
C_NAIVE   = "#8172B2"   # purple
C_LOG     = "#55A868"   # green
C_BT      = "#DD8452"   # orange
C_TIMEOUT = "#CC3333"   # red  (hatched)
TIMEOUT_SECONDS = 120.0 # 2 min
TIMEOUT_LABEL = ">2 min"

plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.facecolor":    "#F9F9F9",
    "figure.facecolor":  "#FFFFFF",
    "grid.color":        "#DDDDDD",
    "grid.linewidth":    0.8,
})

# ── group display order & titles ───────────────────────────────
GROUP_ORDER  = ["4x4", "17-clue", "9x9-generated", "5-clue", "16x16", "25x25", "36x36"]
GROUP_TITLES = {
    "4x4":          "4×4 Sudoku",
    "17-clue":      "9×9 Sudoku — 17-Clue (Royle)",
    "9x9-generated": "9×9 Sudoku — Generated",
    "5-clue":       "9×9 Sudoku — 5-Clue",
    "16x16":        "16×16 Sudoku",
    "25x25":        "25×25 Sudoku",
    "36x36":        "36×36 Sudoku",
}
GROUP_SHORT = {
    "4x4":          "4×4",
    "17-clue":      "9×9\n17-clue",
    "9x9-generated": "9×9\ngenerated",
    "5-clue":       "9×9\n5-clue",
    "16x16":        "16×16",
    "25x25":        "25×25",
    "36x36":        "36×36",
}


# ══════════════════════════════════════════════════════════════
# Load CSV
# ══════════════════════════════════════════════════════════════
def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            row = {k.strip(): v.strip() for k, v in raw.items()}

            def parse_float(col):
                v = row.get(col, "nan").strip()
                if v in ("inf", "Infinity", "infinity"): return float("inf")
                if v in ("", "nan", "NaN"): return float("nan")
                try: return float(v)
                except: return float("nan")

            def parse_int(col):
                v = row.get(col, "0").strip()
                try: return int(v)
                except: return 0

            # Support both old and new schema
            sat_compact = parse_float("sat_compact_time")
            if math.isnan(sat_compact):
                sat_compact = parse_float("sat_time")

            sat_naive = parse_float("sat_naive_time")
            sat_log = parse_float("sat_log_time")

            compact_v = parse_int("compact_vars")
            if compact_v == 0:
                compact_v = parse_int("cnf_vars")

            compact_c = parse_int("compact_clauses")
            if compact_c == 0:
                compact_c = parse_int("cnf_clauses")

            puzzle_name = row.get("puzzle", "") or row.get("puzzle_name", "")

            rows.append({
                "group":            row.get("group", ""),
                "generator":        row.get("generator", ""),
                "size":             int(row.get("size", 0)),
                "puzzle":           puzzle_name,
                "num_clues":        parse_int("num_clues"),
                "cnf_vars":         compact_v,
                "cnf_clauses":      compact_c,
                "compact_vars":     compact_v,
                "compact_clauses":  compact_c,
                "naive_vars":       parse_int("naive_vars"),
                "naive_clauses":    parse_int("naive_clauses"),
                "log_vars":         parse_int("log_vars"),
                "log_clauses":      parse_int("log_clauses"),
                "enc_time":         parse_float("compact_enc_time") if not math.isnan(parse_float("compact_enc_time")) else parse_float("enc_time"),
                "compact_enc_time": parse_float("compact_enc_time"),
                "naive_enc_time":   parse_float("naive_enc_time"),
                "sat_time":         sat_compact,
                "sat_compact_time": sat_compact,
                "sat_naive_time":   sat_naive,
                "sat_log_time":     sat_log,
                "bt_time":          parse_float("bt_time"),
                "sat_status":       row.get("sat_compact_status", "") or row.get("sat_status", ""),
                "sat_compact_status": row.get("sat_compact_status", "") or row.get("sat_status", ""),
                "sat_naive_status": row.get("sat_naive_status", ""),
                "sat_log_status":   row.get("sat_log_status", ""),
                "bt_status":        row.get("bt_status", ""),
                "validator_passed": row.get("validator_passed", "True").lower() == "true",
            })
    return aggregate_repeats(rows)


_TIME_FIELDS = (
    "sat_time", "sat_compact_time", "sat_naive_time", "sat_log_time",
    "bt_time", "enc_time", "compact_enc_time", "naive_enc_time",
)


def aggregate_repeats(rows):
    """Collapse repeated runs of the same puzzle into one row (mean time).

    Any timeout among the repeats makes the aggregate a timeout (inf).
    Repeated rows otherwise share the same puzzle/CNF data, so the mean is
    only applied to timing fields; all other fields are taken from the first
    occurrence.  Row order follows first appearance.
    """
    merged = {}
    order = []
    for r in rows:
        key = (r["group"], r["puzzle"])
        if key not in merged:
            merged[key] = dict(r)
            order.append(key)
            continue
        agg = merged[key]
        for field in _TIME_FIELDS:
            vals = [agg[field], r[field]]
            if any(is_timeout(v) for v in vals):
                agg[field] = float("inf")
            else:
                finite = [v for v in vals if is_valid(v)]
                agg[field] = sum(finite) / len(finite) if finite else float("nan")
    return [merged[k] for k in order]



def is_timeout(v): return math.isinf(v)
def is_valid(v):   return not math.isnan(v) and not math.isinf(v)


# ══════════════════════════════════════════════════════════════
# Shared helpers
# ══════════════════════════════════════════════════════════════

def puzzle_num(name):
    """Extract trailing number from puzzle name for x-axis label."""
    parts = name.replace("-", "_").split("_")
    for p in reversed(parts):
        if p.isdigit():
            return f"#{int(p)}"
    return name


def timeout_bar_height(all_rows):
    """Height to draw timeout bars: 3× the largest finite solve time."""
    finite = [v for r in all_rows
              for v in (r["sat_compact_time"], r["sat_naive_time"], r["sat_log_time"], r["bt_time"])
              if is_valid(v)]
    return max(finite) * 3 if finite else TIMEOUT_SECONDS


def add_bar(ax, x, height, width, color, timeout=False, label_val=None):
    """Draw one bar, hatched if timeout."""
    hatch = "//" if timeout else None
    alpha = 0.70 if timeout else 0.88
    ax.bar(x, height, width, color=color, alpha=alpha,
           hatch=hatch, edgecolor="white", linewidth=0.6, zorder=3)
    if timeout:
        ax.text(x, height * 1.04, TIMEOUT_LABEL,
                ha="center", va="bottom", fontsize=7.5,
                color=C_TIMEOUT, fontweight="bold")


def standard_legend(ax, has_sat=True, has_timeout=False):
    patches = []
    if has_sat:
        patches.extend((
            mpatches.Patch(color=C_SAT, label="SAT Compact (CaDiCaL)"),
            mpatches.Patch(color=C_NAIVE, label="SAT Naive (CaDiCaL)"),
            mpatches.Patch(color=C_LOG, label="SAT Logarithmic (CaDiCaL)"),
        ))
    patches.append(mpatches.Patch(color=C_BT, label="Backtracking (MRV + FC)"))
    if has_timeout:
        patches.append(mpatches.Patch(color=C_TIMEOUT, label=TIMEOUT_LABEL,
                                      hatch="//", alpha=0.70))
    ax.legend(handles=patches, fontsize=9, loc="upper right",
              framealpha=0.9, edgecolor="#cccccc")


def use_log(group_rows):
    """Use log scale if max/min ratio > 50."""
    vals = [v for r in group_rows
            for v in (r["sat_time"], r["bt_time"]) if is_valid(v)]
    if len(vals) < 2: return False
    return max(vals) / max(min(vals), 1e-12) > 50


# ══════════════════════════════════════════════════════════════
# Plot 1 – per-group bar chart
# ══════════════════════════════════════════════════════════════

def plot_group(group, rows, out_dir, tb_h):
    n      = len(rows)
    x      = np.arange(n)
    w      = 0.19
    title  = GROUP_TITLES.get(group, group)
    labels = [puzzle_num(r["puzzle"]) for r in rows]

    compact_times = [r["sat_compact_time"] for r in rows]
    naive_times = [r["sat_naive_time"] for r in rows]
    log_times = [r["sat_log_time"] for r in rows]
    bt_times = [r["bt_time"] for r in rows]
    all_times = compact_times + naive_times + log_times + bt_times
    has_sat = any(is_valid(v) or is_timeout(v) for v in compact_times + naive_times + log_times)
    any_to = any(is_timeout(v) for v in all_times)

    log = use_log(rows)

    fig, ax = plt.subplots(figsize=(max(7, n * 1.6 + 1.5), 5.5))
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)

    for i in range(n):
        for offset, value, color in (
            (-1.5 * w, compact_times[i], C_SAT),
            (-0.5 * w, naive_times[i], C_NAIVE),
            (0.5 * w, log_times[i], C_LOG),
            (1.5 * w, bt_times[i], C_BT),
        ):
            if is_timeout(value):
                add_bar(ax, x[i] + offset, tb_h, w, C_TIMEOUT, timeout=True)
            elif is_valid(value):
                add_bar(ax, x[i] + offset, value, w, color, label_val=value)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_xlabel("Puzzle", fontsize=12)
    ax.set_ylabel("Solve Time (seconds)" + (" — log scale" if log else ""),
                  fontsize=12)
    ax.grid(axis="y", zorder=0)

    if log:
        ax.set_yscale("log")
        finite = [v for v in all_times if is_valid(v)]
        ax.set_ylim(bottom=min(finite) * 0.3 if finite else 1e-5)
    else:
        ax.set_ylim(bottom=0)

    standard_legend(ax, has_sat=has_sat, has_timeout=any_to)
    plt.tight_layout()

    safe  = group.replace("/", "_").replace(" ", "_")
    fname = os.path.join(out_dir, f"plot_{safe}.png")
    plt.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close()
    return fname



# ══════════════════════════════════════════════════════════════
# Plot 1b – per-group LINE chart (SAT vs BT across puzzles)
# ══════════════════════════════════════════════════════════════

def plot_group_line(group, rows, out_dir, tb_h):
    """
    Line graph for a single puzzle group: x = puzzle index,
    y = solve time (log scale). One line per solver.
    Timeout points are plotted as triangle markers at tb_h with annotation.
    """
    title  = GROUP_TITLES.get(group, group)
    labels = [puzzle_num(r["puzzle"]) for r in rows]
    n      = len(rows)
    xs     = list(range(1, n + 1))   # 1-indexed for cleaner display

    compact_times = [r["sat_compact_time"] for r in rows]
    naive_times = [r["sat_naive_time"] for r in rows]
    log_times = [r["sat_log_time"] for r in rows]
    bt_times = [r["bt_time"] for r in rows]
    has_sat = any(is_valid(v) or is_timeout(v) for v in compact_times + naive_times + log_times)

    fig, ax = plt.subplots(figsize=(max(7, n * 1.4 + 2), 5.5))
    ax.set_title(title + " — Line Chart", fontsize=14, fontweight="bold", pad=14)

    def draw_line(times, color, label, marker):
        good_x, good_y = [], []
        to_x           = []
        for xi, v in zip(xs, times):
            if is_valid(v):
                good_x.append(xi); good_y.append(v)
            elif is_timeout(v):
                to_x.append(xi)

        if good_x:
            ax.plot(good_x, good_y, marker + "-", color=color,
                    lw=2.2, ms=9, label=label, zorder=4)
        if to_x:
            ax.plot(to_x, [tb_h] * len(to_x), "v",
                    color=C_TIMEOUT, ms=14, zorder=5,
                    label=f"{label} — {TIMEOUT_LABEL}")
            for xi in to_x:
                ax.annotate(TIMEOUT_LABEL,
                            xy=(xi, tb_h),
                            xytext=(xi, tb_h * 1.15),
                            ha="center", fontsize=8,
                            color=C_TIMEOUT, fontweight="bold")

    if has_sat:
        draw_line(compact_times, C_SAT, "SAT Compact (CaDiCaL)", "o")
        draw_line(naive_times, C_NAIVE, "SAT Naive (CaDiCaL)", "^")
        draw_line(log_times, C_LOG, "SAT Logarithmic (CaDiCaL)", "D")
    draw_line(bt_times, C_BT, "Backtracking (MRV + FC)", "s")

    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_xlabel("Puzzle", fontsize=12)
    ax.set_ylabel("Solve Time (seconds — log scale)", fontsize=12)
    ax.set_yscale("log")

    all_finite = [v for v in compact_times + naive_times + log_times + bt_times if is_valid(v)]
    if all_finite:
        ax.set_ylim(bottom=min(all_finite) * 0.3)

    ax.grid(True, which="both", linestyle="--", alpha=0.5, zorder=0)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9, edgecolor="#cccccc")
    plt.tight_layout()

    safe  = group.replace("/", "_").replace(" ", "_")
    fname = os.path.join(out_dir, f"line_{safe}.png")
    plt.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close()
    return fname


# ══════════════════════════════════════════════════════════════
# Plot 2 – overview (mean per group, all groups side-by-side)
# ══════════════════════════════════════════════════════════════

def plot_overview(all_rows, out_dir, tb_h):
    from collections import defaultdict
    methods = (("compact", "sat_compact_time"), ("naive", "sat_naive_time"),
               ("log", "sat_log_time"), ("bt", "bt_time"))
    agg = defaultdict(lambda: {name: [] for name, _ in methods})
    for r in all_rows:
        g = r["group"]
        for name, field in methods:
            value = r[field]
            if is_valid(value):
                agg[g][name].append(value)
            elif is_timeout(value):
                agg[g][name].append(tb_h)

    def mean_or_timeout(lst):
        if not lst: return float("nan")
        if tb_h in lst: return float("inf")   # any timeout → timeout
        return sum(lst) / len(lst)

    groups  = [g for g in GROUP_ORDER if g in agg]
    groups += sorted(g for g in agg if g not in GROUP_ORDER)
    xlabels = [GROUP_SHORT.get(g, g) for g in groups]
    x       = np.arange(len(groups))
    w       = 0.19

    compact_m = [mean_or_timeout(agg[g]["compact"]) for g in groups]
    naive_m = [mean_or_timeout(agg[g]["naive"]) for g in groups]
    log_m = [mean_or_timeout(agg[g]["log"]) for g in groups]
    bt_m = [mean_or_timeout(agg[g]["bt"]) for g in groups]
    all_means = compact_m + naive_m + log_m + bt_m
    has_sat = any(is_valid(v) or is_timeout(v) for v in compact_m + naive_m + log_m)
    any_to = any(is_timeout(v) for v in all_means)

    fig, ax = plt.subplots(figsize=(max(9, len(groups) * 1.6 + 1.5), 5.5))
    ax.set_title("Benchmark Overview: SAT vs Backtracking (mean per type)",
                 fontsize=14, fontweight="bold", pad=14)

    for i in range(len(groups)):
        for offset, value, color in (
            (-1.5 * w, compact_m[i], C_SAT),
            (-0.5 * w, naive_m[i], C_NAIVE),
            (0.5 * w, log_m[i], C_LOG),
            (1.5 * w, bt_m[i], C_BT),
        ):
            if is_timeout(value):
                add_bar(ax, x[i] + offset, tb_h, w, C_TIMEOUT, timeout=True)
            elif is_valid(value):
                add_bar(ax, x[i] + offset, value, w, color, label_val=value)

    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=11)
    ax.set_xlabel("Puzzle Type", fontsize=12)
    ax.set_ylabel("Mean Solve Time (seconds — log scale)", fontsize=12)
    ax.set_yscale("log")
    finite = [v for v in all_means if is_valid(v)]
    ax.set_ylim(bottom=min(finite) * 0.2 if finite else 1e-5)
    ax.grid(axis="y", which="both", zorder=0)
    standard_legend(ax, has_sat=has_sat, has_timeout=any_to)
    plt.tight_layout()

    fname = os.path.join(out_dir, "plot_overview.png")
    plt.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close()
    return fname


# ══════════════════════════════════════════════════════════════
# Plot 3 – scaling line chart
# ══════════════════════════════════════════════════════════════

def plot_scaling(all_rows, out_dir, tb_h):
    from collections import defaultdict
    agg = defaultdict(lambda: {"compact": [], "naive": [], "log": [], "bt": []})
    for r in all_rows:
        g = r["group"]
        for name in ("compact", "naive", "log"):
            v = r[f"sat_{name}_time"]
            if is_valid(v):     agg[g][name].append(v)
            elif is_timeout(v): agg[g][name].append(float("inf"))
        if is_valid(r["bt_time"]):     agg[g]["bt"].append(r["bt_time"])
        elif is_timeout(r["bt_time"]): agg[g]["bt"].append(float("inf"))

    def mean_or_inf(lst):
        if not lst: return float("nan")
        if float("inf") in lst: return float("inf")
        return sum(lst) / len(lst)

    groups  = [g for g in GROUP_ORDER if g in agg]
    groups += sorted(g for g in agg if g not in GROUP_ORDER)
    xlabels = [GROUP_SHORT.get(g, g).replace("\n", " ") for g in groups]
    compact_m = [mean_or_inf(agg[g]["compact"]) for g in groups]
    naive_m   = [mean_or_inf(agg[g]["naive"])   for g in groups]
    log_m     = [mean_or_inf(agg[g]["log"])     for g in groups]
    bt_m      = [mean_or_inf(agg[g]["bt"])      for g in groups]
    has_sat = any(is_valid(v) or is_timeout(v) for v in compact_m + naive_m + log_m)

    fig, ax = plt.subplots(figsize=(max(9, len(groups) * 1.5 + 1.5), 5.5))
    ax.set_title("Solve Time Scaling Across Puzzle Types",
                 fontsize=14, fontweight="bold", pad=14)

    def draw_line(means, color, label, marker):
        xs_good, ys_good, xs_to = [], [], []
        for xl, v in zip(xlabels, means):
            if is_valid(v):        xs_good.append(xl); ys_good.append(v)
            elif is_timeout(v):    xs_to.append(xl)
        if xs_good:
            ax.plot(xs_good, ys_good, marker + "-", color=color,
                    lw=2.2, ms=9, label=label, zorder=4)
        if xs_to:
            ax.plot(xs_to, [tb_h] * len(xs_to), "v",
                    color=C_TIMEOUT, ms=14, zorder=5,
                    label=f"{label} — {TIMEOUT_LABEL}")

    if has_sat:
        draw_line(compact_m, C_SAT,   "SAT Compact (CaDiCaL)", "o")
        draw_line(naive_m,   C_NAIVE, "SAT Naive (CaDiCaL)",   "^")
        draw_line(log_m,     C_LOG,   "SAT Log (CaDiCaL)",     "D")
    draw_line(bt_m, C_BT, "Backtracking (MRV + FC)", "s")

    ax.set_xlabel("Puzzle Type", fontsize=12)
    ax.set_ylabel("Mean Solve Time (seconds — log scale)", fontsize=12)
    ax.set_yscale("log")
    finite = [v for v in compact_m + naive_m + log_m + bt_m if is_valid(v)]
    ax.set_ylim(bottom=min(finite) * 0.2 if finite else 1e-5)
    ax.grid(True, which="both", zorder=0)
    ax.legend(fontsize=9, loc="upper left", framealpha=0.9, edgecolor="#cccccc")
    plt.tight_layout()

    fname = os.path.join(out_dir, "plot_scaling.png")
    plt.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close()
    return fname



# ══════════════════════════════════════════════════════════════
# Plot 4 – direct comparison: average per grid size
# ══════════════════════════════════════════════════════════════

def plot_size_comparison(all_rows, out_dir, tb_h):
    """
    Groups ALL puzzles by grid SIZE (4, 9, 16, 25, 36),
    averages SAT and BT times, and plots side-by-side.
    If ANY puzzle in a size group timed out -> shows >2 min bar.
    """
    from collections import defaultdict
    size_data = defaultdict(lambda: {"compact": [], "naive": [], "log": [], "bt": []})
    for r in all_rows:
        size_data[r["size"]]["compact"].append(r["sat_compact_time"])
        size_data[r["size"]]["naive"].append(r["sat_naive_time"])
        size_data[r["size"]]["log"].append(r["sat_log_time"])
        size_data[r["size"]]["bt"].append(r["bt_time"])

    sizes = sorted(size_data.keys())

    def avg(lst):
        if any(is_timeout(v) for v in lst): return float("inf")
        finite = [v for v in lst if is_valid(v)]
        return sum(finite) / len(finite) if finite else float("nan")

    compact_avgs = [avg(size_data[s]["compact"]) for s in sizes]
    naive_avgs   = [avg(size_data[s]["naive"])   for s in sizes]
    log_avgs     = [avg(size_data[s]["log"])     for s in sizes]
    bt_avgs      = [avg(size_data[s]["bt"])      for s in sizes]
    counts       = [len(size_data[s]["bt"])      for s in sizes]
    has_sat      = any(is_valid(v) or is_timeout(v) for v in compact_avgs + naive_avgs + log_avgs)
    any_to       = any(is_timeout(v) for v in compact_avgs + naive_avgs + log_avgs + bt_avgs)

    x       = np.arange(len(sizes))
    w       = 0.19
    xlabels = [f"{s}\u00d7{s}\n(n={counts[i]})" for i, s in enumerate(sizes)]

    fig, ax = plt.subplots(figsize=(max(9, len(sizes) * 1.8 + 2), 6))
    ax.set_title(
        "SAT Encodings vs Backtracking — Average Solve Time by Grid Size",
        fontsize=14, fontweight="bold", pad=14
    )

    for i in range(len(sizes)):
        for offset, val, color in (
            (-1.5 * w, compact_avgs[i], C_SAT),
            (-0.5 * w, naive_avgs[i], C_NAIVE),
            (0.5 * w, log_avgs[i], C_LOG),
            (1.5 * w, bt_avgs[i], C_BT),
        ):
            if is_timeout(val):
                add_bar(ax, x[i] + offset, tb_h, w, C_TIMEOUT, timeout=True)
            elif is_valid(val):
                add_bar(ax, x[i] + offset, val, w, color, label_val=val)

    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=11)
    ax.set_xlabel("Grid Size  (n = number of puzzles averaged)", fontsize=12)
    ax.set_ylabel("Average Solve Time (seconds — log scale)", fontsize=12)
    ax.set_yscale("log")
    finite = [v for v in compact_avgs + naive_avgs + log_avgs + bt_avgs if is_valid(v)]
    ax.set_ylim(bottom=min(finite) * 0.2 if finite else 1e-5)
    ax.grid(axis="y", which="both", zorder=0)

    # Sub-label: which groups are inside each size
    for i, s in enumerate(sizes):
        grps = sorted({r["group"] for r in all_rows if r["size"] == s})
        ax.text(x[i], ax.get_ylim()[0] * 0.55, ", ".join(grps),
                ha="center", va="top", fontsize=7,
                color="#666666", style="italic")

    standard_legend(ax, has_sat=has_sat, has_timeout=any_to)
    plt.tight_layout()
    fname = os.path.join(out_dir, "plot_by_grid_size.png")
    plt.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close()
    return fname


# ══════════════════════════════════════════════════════════════
# Plot 5 – speedup ratio: BT time / SAT time per grid size
# ══════════════════════════════════════════════════════════════

def plot_speedup(all_rows, out_dir):
    """
    For each grid size compute speedup = avg_bt / avg_compact.
    Bar > 1: SAT Compact is faster. Bar < 1: BT is faster.
    """
    from collections import defaultdict
    size_data = defaultdict(lambda: {"compact": [], "bt": []})
    for r in all_rows:
        size_data[r["size"]]["compact"].append(r["sat_compact_time"])
        size_data[r["size"]]["bt"].append(r["bt_time"])

    sizes = sorted(size_data.keys())

    def avg_finite(lst):
        f = [v for v in lst if is_valid(v)]
        return sum(f) / len(f) if f else None

    speedups, bar_colors, annotations, xlabels = [], [], [], []
    for s in sizes:
        sat_a    = avg_finite(size_data[s]["compact"])
        bt_a     = avg_finite(size_data[s]["bt"])
        bt_to    = any(is_timeout(v) for v in size_data[s]["bt"])
        xlabels.append(f"{s}\u00d7{s}")

        if bt_to and sat_a:
            speedups.append(TIMEOUT_SECONDS / sat_a)
            bar_colors.append(C_SAT)
            annotations.append("BT >2min")
        elif sat_a and bt_a and sat_a > 0:
            ratio = bt_a / sat_a
            speedups.append(ratio)
            bar_colors.append(C_SAT if ratio >= 1 else C_BT)
            annotations.append(f"{ratio:.1f}\u00d7")
        else:
            speedups.append(0)
            bar_colors.append("#aaaaaa")
            annotations.append("N/A")

    fig, ax = plt.subplots(figsize=(max(8, len(sizes) * 1.8 + 2), 5.5))
    ax.set_title(
        "SAT Compact Speedup over Backtracking by Grid Size\n"
        "(value > 1 \u2192 SAT Compact faster;  value < 1 \u2192 Backtracking faster)",
        fontsize=13, fontweight="bold", pad=14
    )

    ax.bar(xlabels, speedups, color=bar_colors,
           alpha=0.88, edgecolor="white", linewidth=0.6, zorder=3)

    for xi, (ann, sv) in enumerate(zip(annotations, speedups)):
        ax.text(xi, sv * 1.06, ann, ha="center", va="bottom",
                fontsize=10, fontweight="bold", color="#333333")

    ax.axhline(1, color="#555555", lw=1.5, ls="--", zorder=2)
    ax.set_xlabel("Grid Size", fontsize=12)
    ax.set_ylabel("Speedup  (avg BT time \u00f7 avg SAT Compact time)", fontsize=12)
    ax.set_yscale("log")
    ax.set_ylim(bottom=0.1)
    ax.grid(axis="y", which="both", zorder=0)

    sat_p = mpatches.Patch(color=C_SAT, label="SAT Compact faster")
    bt_p  = mpatches.Patch(color=C_BT,  label="Backtracking faster")
    eq_l  = plt.Line2D([0],[0], color="#555555", lw=1.5, ls="--", label="Equal speed (1\u00d7)")
    ax.legend(handles=[sat_p, bt_p, eq_l], fontsize=9,
              framealpha=0.9, edgecolor="#cccccc")

    plt.tight_layout()
    fname = os.path.join(out_dir, "plot_speedup.png")
    plt.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close()
    return fname
# ══════════════════════════════════════════════════════════════
# Plot 6 – CNF Variables & Clauses per puzzle
# ══════════════════════════════════════════════════════════════

def plot_cnf_stats(rows, out_dir):
    from collections import defaultdict

    groups = defaultdict(list)
    for r in rows:
        groups[r["group"]].append(r)

    for g, g_rows in groups.items():
        n      = len(g_rows)
        x      = np.arange(n)
        w      = 0.26
        labels = [puzzle_num(r["puzzle"]) for r in g_rows]

        fig, (ax_v, ax_c) = plt.subplots(
            1, 2, figsize=(max(12, n * 2.4), 5), sharex=True
        )
        panels = (
            (ax_v, "CNF Variables", "Variables", (
                ("Naive",   "naive_vars",    C_NAIVE),
                ("Compact", "compact_vars",  C_SAT),
                ("Log",     "log_vars",      C_LOG),
            )),
            (ax_c, "CNF Clauses", "Clauses", (
                ("Naive",   "naive_clauses",   C_NAIVE),
                ("Compact", "compact_clauses", C_SAT),
                ("Log",     "log_clauses",     C_LOG),
            )),
        )
        for ax, title, ylabel, series in panels:
            for i, (label, field, color) in enumerate(series):
                ax.bar(x + (i - 1) * w, [r[field] for r in g_rows],
                       width=w, label=label, color=color)
            ax.set_title(title, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.set_xlabel("Puzzle", fontsize=11)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, fontsize=10)
            ax.legend(fontsize=9)
            ax.grid(axis="y", linestyle="--", alpha=0.5)

        fig.suptitle(f"CNF Encoding Size — {GROUP_TITLES.get(g,g)}",
                     fontsize=14, fontweight="bold")

        safe  = g.replace("/", "_").replace(" ", "_")
        fname = os.path.join(out_dir, f"cnf_{safe}.png")
        plt.tight_layout()
        plt.savefig(fname, dpi=160, bbox_inches="tight")
        plt.close()

# ══════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════

def find_csv_auto():
    here = os.path.dirname(os.path.abspath(__file__))
    for p in [
        os.path.join(here, "benchmark_results.csv"),
        os.path.join(here, "..", "..", "Results", "benchmark_results.csv"),
        os.path.join(here, "..", "Results", "benchmark_results.csv"),
    ]:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None


def generate_all_plots(csv_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rows = load_csv(csv_path)
    if not rows:
        print("No rows found in CSV for plotting.")
        return []
    tb_h = timeout_bar_height(rows)

    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        groups[r["group"]].append(r)

    saved = []
    for g in GROUP_ORDER:
        if g not in groups:
            continue
        p = plot_group(g, groups[g], out_dir, tb_h)
        if p: saved.append(p)
        p = plot_group_line(g, groups[g], out_dir, tb_h)
        if p: saved.append(p)

    for g, g_rows in groups.items():
        if g not in GROUP_ORDER:
            p = plot_group(g, g_rows, out_dir, tb_h)
            if p: saved.append(p)
            p = plot_group_line(g, g_rows, out_dir, tb_h)
            if p: saved.append(p)

    p = plot_overview(rows, out_dir, tb_h)
    if p: saved.append(p)
    p = plot_scaling(rows, out_dir, tb_h)
    if p: saved.append(p)
    p = plot_size_comparison(rows, out_dir, tb_h)
    if p: saved.append(p)
    p = plot_speedup(rows, out_dir)
    if p: saved.append(p)
    p = plot_cnf_stats(rows, out_dir)
    if p: saved.append(p)

    return saved


def main():
    parser = argparse.ArgumentParser(
        description="Plot benchmark_results.csv — one chart per Sudoku type"
    )
    parser.add_argument("--csv", default=None, help="Path to CSV file")
    parser.add_argument("--out", default=None, help="Output directory for PNGs")
    args = parser.parse_args()

    csv_path = args.csv or find_csv_auto()
    if not csv_path or not os.path.exists(csv_path):
        print("ERROR: Cannot find benchmark_results.csv")
        print("  Pass it with:  python plot_results.py --csv path/to/file.csv")
        sys.exit(1)

    out_dir = args.out or os.path.dirname(os.path.abspath(csv_path))
    os.makedirs(out_dir, exist_ok=True)

    print(f"Reading : {csv_path}")
    rows = load_csv(csv_path)
    print(f"Rows    : {len(rows)}")

    tb_h = timeout_bar_height(rows)
    print(f"Timeout bar height: {tb_h:.3f}s\n")

    # group rows
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        groups[r["group"]].append(r)

    saved = []

    # ── per-group charts (bar + line) ─────────────────────────
    for g in GROUP_ORDER:
        if g not in groups:
            continue
        print(f"  [{g}] {len(groups[g])} puzzles ...")
        p = plot_group(g, groups[g], out_dir, tb_h)
        saved.append(p)
        print(f"    -> {os.path.basename(p)}")
        p = plot_group_line(g, groups[g], out_dir, tb_h)
        saved.append(p)
        print(f"    -> {os.path.basename(p)}")

    # any group not in GROUP_ORDER
    for g, g_rows in groups.items():
        if g not in GROUP_ORDER:
            print(f"  [{g}] {len(g_rows)} puzzles ...")
            p = plot_group(g, g_rows, out_dir, tb_h)
            saved.append(p); print(f"    -> {os.path.basename(p)}")
            p = plot_group_line(g, g_rows, out_dir, tb_h)
            saved.append(p); print(f"    -> {os.path.basename(p)}")

    # ── overview ───────────────────────────────────────────────
    print("\n  [Overview] all types ...")
    p = plot_overview(rows, out_dir, tb_h)
    saved.append(p); print(f"    -> {os.path.basename(p)}")

    # ── scaling line ───────────────────────────────────────────
    print("\n  [Scaling line chart] ...")
    p = plot_scaling(rows, out_dir, tb_h)
    saved.append(p); print(f"    -> {os.path.basename(p)}")

    # ── average by grid size — direct comparison ───────────────
    print("\n  [Average by grid size — direct comparison] ...")
    p = plot_size_comparison(rows, out_dir, tb_h)
    saved.append(p); print(f"    -> {os.path.basename(p)}")

    # ── speedup ratio ───────────────────────────────────────────
    print("\n  [SAT speedup over backtracking] ...")
    p = plot_speedup(rows, out_dir)
    saved.append(p); print(f"    -> {os.path.basename(p)}")

    print(f"\n✓ {len(saved)} plots saved to: {out_dir}")

    print("\n  [CNF stats per group] ...")
    p = plot_cnf_stats(rows, out_dir)
    print(f"    -> CNF plots saved per group")


if __name__ == "__main__":
    main()