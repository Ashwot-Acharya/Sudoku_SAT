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
C_SAT     = "#4C72B0"   # blue
C_BT      = "#DD8452"   # orange
C_TIMEOUT = "#CC3333"   # red  (hatched)
TIMEOUT_LABEL = ">10 min"

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
GROUP_ORDER  = ["4x4", "17-clue", "5-clue", "16x16", "25x25", "36x36"]
GROUP_TITLES = {
    "4x4":     "4×4 Sudoku",
    "17-clue": "9×9 Sudoku — 17-Clue (Royle)",
    "5-clue":  "9×9 Sudoku — 5-Clue",
    "16x16":   "16×16 Sudoku",
    "25x25":   "25×25 Sudoku",
    "36x36":   "36×36 Sudoku",
}
GROUP_SHORT = {
    "4x4":     "4×4",
    "17-clue": "9×9\n17-clue",
    "5-clue":  "9×9\n5-clue",
    "16x16":   "16×16",
    "25x25":   "25×25",
    "36x36":   "36×36",
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

            rows.append({
                "group":       row.get("group", ""),
                "size":        int(row.get("size", 0)),
                "puzzle":      row.get("puzzle", ""),
                "cnf_vars":    parse_int("cnf_vars"),
                "cnf_clauses": parse_int("cnf_clauses"),
                "enc_time":    parse_float("enc_time"),
                "sat_time":    parse_float("sat_time"),
                "bt_time":     parse_float("bt_time"),
                "sat_status":  row.get("sat_status", ""),
                "bt_status":   row.get("bt_status", ""),
            })
    return rows



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
              for v in (r["sat_time"], r["bt_time"]) if is_valid(v)]
    return max(finite) * 3 if finite else 600.0


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
        patches.append(mpatches.Patch(color=C_SAT, label="SAT Solver (satch)"))
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
    w      = 0.32
    title  = GROUP_TITLES.get(group, group)
    labels = [puzzle_num(r["puzzle"]) for r in rows]

    sat_times = [r["sat_time"] for r in rows]
    bt_times  = [r["bt_time"]  for r in rows]
    has_sat   = any(is_valid(v) for v in sat_times)
    any_to    = any(is_timeout(v) for v in sat_times + bt_times)

    log = use_log(rows)

    fig, ax = plt.subplots(figsize=(max(7, n * 1.6 + 1.5), 5.5))
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)

    for i in range(n):
        sv, bv = sat_times[i], bt_times[i]

        # SAT bar
        if has_sat:
            if is_timeout(sv):
                add_bar(ax, x[i] - w/2, tb_h, w, C_TIMEOUT, timeout=True)
            elif is_valid(sv):
                add_bar(ax, x[i] - w/2, sv, w, C_SAT, label_val=sv)

        # Backtracking bar
        if is_timeout(bv):
            add_bar(ax, x[i] + w/2, tb_h, w, C_TIMEOUT, timeout=True)
        elif is_valid(bv):
            add_bar(ax, x[i] + w/2, bv, w, C_BT, label_val=bv)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_xlabel("Puzzle", fontsize=12)
    ax.set_ylabel("Solve Time (seconds)" + (" — log scale" if log else ""),
                  fontsize=12)
    ax.grid(axis="y", zorder=0)

    if log:
        ax.set_yscale("log")
        finite = [v for v in sat_times + bt_times if is_valid(v)]
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

    sat_times = [r["sat_time"] for r in rows]
    bt_times  = [r["bt_time"]  for r in rows]
    has_sat   = any(is_valid(v) or is_timeout(v) for v in sat_times)

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
        draw_line(sat_times, C_SAT, "SAT Solver (satch)", "o")
    draw_line(bt_times, C_BT, "Backtracking (MRV + FC)", "s")

    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_xlabel("Puzzle", fontsize=12)
    ax.set_ylabel("Solve Time (seconds — log scale)", fontsize=12)
    ax.set_yscale("log")

    all_finite = [v for v in sat_times + bt_times if is_valid(v)]
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
    agg = defaultdict(lambda: {"sat": [], "bt": []})
    for r in all_rows:
        g = r["group"]
        if is_valid(r["sat_time"]):    agg[g]["sat"].append(r["sat_time"])
        elif is_timeout(r["sat_time"]): agg[g]["sat"].append(tb_h)
        if is_valid(r["bt_time"]):     agg[g]["bt"].append(r["bt_time"])
        elif is_timeout(r["bt_time"]): agg[g]["bt"].append(tb_h)

    def mean_or_timeout(lst):
        if not lst: return float("nan")
        if tb_h in lst: return float("inf")   # any timeout → timeout
        return sum(lst) / len(lst)

    groups  = [g for g in GROUP_ORDER if g in agg]
    xlabels = [GROUP_SHORT.get(g, g) for g in groups]
    x       = np.arange(len(groups))
    w       = 0.32

    sat_m = [mean_or_timeout(agg[g]["sat"]) for g in groups]
    bt_m  = [mean_or_timeout(agg[g]["bt"])  for g in groups]
    has_sat = any(is_valid(v) or is_timeout(v) for v in sat_m)
    any_to  = any(is_timeout(v) for v in sat_m + bt_m)

    fig, ax = plt.subplots(figsize=(max(9, len(groups) * 1.6 + 1.5), 5.5))
    ax.set_title("Benchmark Overview: SAT vs Backtracking (mean per type)",
                 fontsize=14, fontweight="bold", pad=14)

    for i in range(len(groups)):
        sv, bv = sat_m[i], bt_m[i]
        if has_sat:
            if is_timeout(sv):
                add_bar(ax, x[i] - w/2, tb_h, w, C_TIMEOUT, timeout=True)
            elif is_valid(sv):
                add_bar(ax, x[i] - w/2, sv, w, C_SAT, label_val=sv)
        if is_timeout(bv):
            add_bar(ax, x[i] + w/2, tb_h, w, C_TIMEOUT, timeout=True)
        elif is_valid(bv):
            add_bar(ax, x[i] + w/2, bv, w, C_BT, label_val=bv)

    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=11)
    ax.set_xlabel("Puzzle Type", fontsize=12)
    ax.set_ylabel("Mean Solve Time (seconds — log scale)", fontsize=12)
    ax.set_yscale("log")
    finite = [v for v in sat_m + bt_m if is_valid(v)]
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
    agg = defaultdict(lambda: {"sat": [], "bt": []})
    for r in all_rows:
        g = r["group"]
        if is_valid(r["sat_time"]):     agg[g]["sat"].append(r["sat_time"])
        elif is_timeout(r["sat_time"]): agg[g]["sat"].append(float("inf"))
        if is_valid(r["bt_time"]):      agg[g]["bt"].append(r["bt_time"])
        elif is_timeout(r["bt_time"]):  agg[g]["bt"].append(float("inf"))

    def mean_or_inf(lst):
        if not lst: return float("nan")
        if float("inf") in lst: return float("inf")
        return sum(lst) / len(lst)

    groups  = [g for g in GROUP_ORDER if g in agg]
    xlabels = [GROUP_SHORT.get(g, g).replace("\n", " ") for g in groups]
    sat_m   = [mean_or_inf(agg[g]["sat"]) for g in groups]
    bt_m    = [mean_or_inf(agg[g]["bt"])  for g in groups]
    has_sat = any(is_valid(v) or is_timeout(v) for v in sat_m)

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
        draw_line(sat_m, C_SAT, "SAT Solver (satch)", "o")
    draw_line(bt_m, C_BT, "Backtracking (MRV + FC)", "s")

    ax.set_xlabel("Puzzle Type", fontsize=12)
    ax.set_ylabel("Mean Solve Time (seconds — log scale)", fontsize=12)
    ax.set_yscale("log")
    finite = [v for v in sat_m + bt_m if is_valid(v)]
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
    If ANY puzzle in a size group timed out -> shows >10 min bar.
    """
    from collections import defaultdict
    size_data = defaultdict(lambda: {"sat": [], "bt": []})
    for r in all_rows:
        size_data[r["size"]]["sat"].append(r["sat_time"])
        size_data[r["size"]]["bt"].append(r["bt_time"])

    sizes = sorted(size_data.keys())

    def avg(lst):
        if any(is_timeout(v) for v in lst): return float("inf")
        finite = [v for v in lst if is_valid(v)]
        return sum(finite) / len(finite) if finite else float("nan")

    sat_avgs = [avg(size_data[s]["sat"]) for s in sizes]
    bt_avgs  = [avg(size_data[s]["bt"])  for s in sizes]
    counts   = [len(size_data[s]["sat"]) for s in sizes]
    has_sat  = any(is_valid(v) or is_timeout(v) for v in sat_avgs)
    any_to   = any(is_timeout(v) for v in sat_avgs + bt_avgs)

    x       = np.arange(len(sizes))
    w       = 0.32
    xlabels = [f"{s}\u00d7{s}\n(n={counts[i]})" for i, s in enumerate(sizes)]

    fig, ax = plt.subplots(figsize=(max(9, len(sizes) * 1.8 + 2), 6))
    ax.set_title(
        "SAT vs Backtracking — Average Solve Time by Grid Size",
        fontsize=14, fontweight="bold", pad=14
    )

    for i in range(len(sizes)):
        sv, bv = sat_avgs[i], bt_avgs[i]
        if has_sat:
            if is_timeout(sv):
                add_bar(ax, x[i] - w/2, tb_h, w, C_TIMEOUT, timeout=True)
            elif is_valid(sv):
                add_bar(ax, x[i] - w/2, sv, w, C_SAT, label_val=sv)
        if is_timeout(bv):
            add_bar(ax, x[i] + w/2, tb_h, w, C_TIMEOUT, timeout=True)
        elif is_valid(bv):
            add_bar(ax, x[i] + w/2, bv, w, C_BT, label_val=bv)

    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=11)
    ax.set_xlabel("Grid Size  (n = number of puzzles averaged)", fontsize=12)
    ax.set_ylabel("Average Solve Time (seconds — log scale)", fontsize=12)
    ax.set_yscale("log")
    finite = [v for v in sat_avgs + bt_avgs if is_valid(v)]
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
    For each grid size compute speedup = avg_bt / avg_sat.
    Bar > 1: SAT is faster. Bar < 1: BT is faster.
    """
    from collections import defaultdict
    size_data = defaultdict(lambda: {"sat": [], "bt": []})
    for r in all_rows:
        size_data[r["size"]]["sat"].append(r["sat_time"])
        size_data[r["size"]]["bt"].append(r["bt_time"])

    sizes = sorted(size_data.keys())

    def avg_finite(lst):
        f = [v for v in lst if is_valid(v)]
        return sum(f) / len(f) if f else None

    speedups, bar_colors, annotations, xlabels = [], [], [], []
    for s in sizes:
        sat_a    = avg_finite(size_data[s]["sat"])
        bt_a     = avg_finite(size_data[s]["bt"])
        bt_to    = any(is_timeout(v) for v in size_data[s]["bt"])
        xlabels.append(f"{s}\u00d7{s}")

        if bt_to and sat_a:
            speedups.append(600.0 / sat_a)
            bar_colors.append(C_SAT)
            annotations.append("BT >10min")
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
        "SAT Speedup over Backtracking by Grid Size\n"
        "(value > 1 \u2192 SAT faster;  value < 1 \u2192 Backtracking faster)",
        fontsize=13, fontweight="bold", pad=14
    )

    ax.bar(xlabels, speedups, color=bar_colors,
           alpha=0.88, edgecolor="white", linewidth=0.6, zorder=3)

    for xi, (ann, sv) in enumerate(zip(annotations, speedups)):
        ax.text(xi, sv * 1.06, ann, ha="center", va="bottom",
                fontsize=10, fontweight="bold", color="#333333")

    ax.axhline(1, color="#555555", lw=1.5, ls="--", zorder=2)
    ax.set_xlabel("Grid Size", fontsize=12)
    ax.set_ylabel("Speedup  (avg BT time \u00f7 avg SAT time)", fontsize=12)
    ax.set_yscale("log")
    ax.set_ylim(bottom=0.1)
    ax.grid(axis="y", which="both", zorder=0)

    sat_p = mpatches.Patch(color=C_SAT, label="SAT faster")
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
        w      = 0.35
        labels = [puzzle_num(r["puzzle"]) for r in g_rows]

        vars_vals    = [r["cnf_vars"] for r in g_rows]
        clauses_vals = [r["cnf_clauses"] for r in g_rows]

        fig, ax = plt.subplots(figsize=(max(7, n * 1.6), 5))
        ax.bar(x - w/2, vars_vals, width=w, label="CNF Variables", color="#5DADE2")
        ax.bar(x + w/2, clauses_vals, width=w, label="CNF Clauses", color="#F5B041")

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=11)
        ax.set_xlabel("Puzzle", fontsize=12)
        ax.set_ylabel("Count", fontsize=12)
        ax.set_title(f"CNF Variables & Clauses — {GROUP_TITLES.get(g,g)}", fontsize=14)
        ax.legend(fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.5)

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
        os.path.join(here, "..", "Output", "benchmark_results.csv"),
        os.path.join(here, "Output",         "benchmark_results.csv"),
    ]:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None


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