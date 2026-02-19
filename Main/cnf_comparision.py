"""
cnf_comparison.py
Compares optimized (φ') vs unoptimized (φ) CNF encoding sizes across Sudoku sizes.

Unoptimized encoding: generates ALL clauses for ALL variables (N³ variables),
ignoring any pre-assigned cells.

Optimized encoding: uses the existing sudoku_to_cnf.py (Kwon & Jain φ').

Run:
    python cnf_comparison.py                    # uses puzzles in ../Puzzles/
    python cnf_comparison.py --sizes 4 9 16 25  # specific sizes only
"""

import os, sys, math, time, argparse
import importlib.util
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "Output")
PUZZLES_DIR = os.path.join(SCRIPT_DIR, "..", "Puzzles")
os.makedirs(OUTPUT_DIR, exist_ok=True)

sys.path.insert(0, SCRIPT_DIR)

# ── load sudoku_to_cnf for the optimized encoder ──────────────────────────────

def _load(name):
    path = os.path.join(SCRIPT_DIR, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ══════════════════════════════════════════════════════════════════════════════
# UNOPTIMIZED encoding  (φ — standard full encoding, no puzzle-specific pruning)
#
# Variables:  var(r,c,v) = (r-1)*N*N + (c-1)*N + v   → N³ variables total
# Clauses:
#   Cell definedness : N² clauses of size N
#   Cell uniqueness  : N² * C(N,2) clauses of size 2
#   Row  definedness : N² clauses of size N
#   Row  uniqueness  : N  * N * C(N,2) clauses of size 2
#   Col  definedness : N² clauses of size N
#   Col  uniqueness  : N  * N * C(N,2) clauses of size 2
#   Block definedness: N² clauses of size N
#   Block uniqueness : N  * C(N²/box², N²/box²) ... = N * C(N,2) per block val
#   Unit clauses for fixed cells: one per clue
#
# We count analytically — no need to materialise all clauses.
# ══════════════════════════════════════════════════════════════════════════════

def unoptimized_counts(n, num_clues):
    """
    Return (num_vars, num_clauses) for the unoptimized φ encoding.
    num_clues = number of pre-filled cells in the puzzle.
    """
    box   = int(math.sqrt(n))
    cn2   = n * (n - 1) // 2          # C(n, 2)
    bsz   = box * box                 # cells per block  = n
    bcn2  = bsz * (bsz - 1) // 2     # C(block_size, 2) = C(n, 2)  since bsz=n

    num_vars = n * n * n              # N³

    cell_def  = n * n                 # one per cell
    cell_uniq = n * n * cn2           # per cell, per pair of values
    row_def   = n * n                 # one per (row, value)
    row_uniq  = n * n * cn2           # per row, per value, per pair of cols
    col_def   = n * n
    col_uniq  = n * n * cn2
    blk_def   = n * n                 # one per (block, value)
    blk_uniq  = n * n * cn2           # per block, per value, per pair of cells

    unit_clues = num_clues            # one unit clause per fixed cell

    num_clauses = (cell_def + cell_uniq +
                   row_def  + row_uniq  +
                   col_def  + col_uniq  +
                   blk_def  + blk_uniq  +
                   unit_clues)

    return num_vars, num_clauses


# ══════════════════════════════════════════════════════════════════════════════
# Collect puzzle files grouped by board size
# ══════════════════════════════════════════════════════════════════════════════

def collect_puzzles_by_size():
    """Return dict: n -> list of puzzle paths."""
    by_size = defaultdict(list)
    if not os.path.isdir(PUZZLES_DIR):
        print(f"Puzzles dir not found: {PUZZLES_DIR}")
        return by_size
    for fname in sorted(os.listdir(PUZZLES_DIR)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(PUZZLES_DIR, fname)
        try:
            enc = _load("sudoku_to_cnf")
            n, puzzle = enc.read_puzzle(path)
            by_size[n].append((path, puzzle))
        except Exception:
            pass
    return by_size


# ══════════════════════════════════════════════════════════════════════════════
# Main comparison
# ══════════════════════════════════════════════════════════════════════════════

def run_comparison(filter_sizes=None):
    enc = _load("sudoku_to_cnf")
    by_size = collect_puzzles_by_size()

    if not by_size:
        print("No puzzles found. Check ../Puzzles/ directory.")
        return []

    sizes = sorted(by_size.keys())
    if filter_sizes:
        sizes = [s for s in sizes if s in filter_sizes]

    print(f"\n{'Size':>6}  {'Clues':>6}  "
          f"{'Unopt Vars':>12}  {'Opt Vars':>10}  {'Var Reduc%':>10}  "
          f"{'Unopt Clauses':>14}  {'Opt Clauses':>12}  {'Clause Reduc%':>13}  "
          f"{'Enc Time(s)':>11}")
    print("-" * 110)

    rows = []

    for n in sizes:
        puzzles = by_size[n]
        size_rows = []

        for path, puzzle in puzzles:
            # Count clues
            num_clues = sum(1 for r in puzzle for v in r if v != 0)

            # Unoptimized counts (analytic)
            unopt_vars, unopt_clauses = unoptimized_counts(n, num_clues)

            # Optimized counts (actually run the encoder)
            t0 = time.time()
            clauses, opt_vars, var_map, V0_list = enc.encode(n, puzzle)
            enc_time = time.time() - t0
            opt_clauses = len(clauses)

            var_reduc    = 100.0 * (1 - opt_vars    / unopt_vars)    if unopt_vars    else 0
            clause_reduc = 100.0 * (1 - opt_clauses / unopt_clauses) if unopt_clauses else 0

            print(f"{n:>4}x{n:<2}  {num_clues:>6}  "
                  f"{unopt_vars:>12,}  {opt_vars:>10,}  {var_reduc:>9.1f}%  "
                  f"{unopt_clauses:>14,}  {opt_clauses:>12,}  {clause_reduc:>12.1f}%  "
                  f"{enc_time:>11.4f}")

            size_rows.append(dict(
                n=n, clues=num_clues,
                unopt_vars=unopt_vars,   opt_vars=opt_vars,   var_reduc=var_reduc,
                unopt_clauses=unopt_clauses, opt_clauses=opt_clauses, clause_reduc=clause_reduc,
                enc_time=enc_time
            ))

        # Averages per size
        def avg(key): return sum(r[key] for r in size_rows) / len(size_rows)
        rows.append(dict(
            n=n,
            unopt_vars=avg("unopt_vars"),       opt_vars=avg("opt_vars"),
            var_reduc=avg("var_reduc"),
            unopt_clauses=avg("unopt_clauses"),  opt_clauses=avg("opt_clauses"),
            clause_reduc=avg("clause_reduc"),
            enc_time=avg("enc_time")
        ))

    print()
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# Plotting
# ══════════════════════════════════════════════════════════════════════════════

def plot_comparison(rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib/numpy not installed: pip install matplotlib numpy")
        return

    if not rows:
        print("No data to plot.")
        return

    sizes   = [r["n"] for r in rows]
    xlbls   = [f"{n}×{n}" for n in sizes]
    x       = np.arange(len(sizes))
    w       = 0.35

    unopt_v = [r["unopt_vars"]    for r in rows]
    opt_v   = [r["opt_vars"]      for r in rows]
    unopt_c = [r["unopt_clauses"] for r in rows]
    opt_c   = [r["opt_clauses"]   for r in rows]
    var_red = [r["var_reduc"]     for r in rows]
    cl_red  = [r["clause_reduc"]  for r in rows]

    C_UNOPT = "#DD8452"
    C_OPT   = "#4C72B0"
    C_RED   = "#55A868"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Optimized (φ') vs Unoptimized (φ) CNF Encoding",
                 fontsize=14, fontweight="bold")

    # ── Variables ─────────────────────────────────────────────────────────────
    ax1.bar(x - w/2, unopt_v, w, color=C_UNOPT, alpha=0.85, label="Unoptimized (φ)")
    ax1.bar(x + w/2, opt_v,   w, color=C_OPT,   alpha=0.85, label="Optimized (φ')")
    ax1.set_xticks(x); ax1.set_xticklabels(xlbls, fontsize=11)
    ax1.set_yscale("log")
    ax1.set_title("Variable Count", fontsize=12)
    ax1.set_ylabel("# Variables (log scale)")
    ax1.legend(fontsize=9)
    ax1.grid(axis="y", linestyle="--", alpha=0.4, which="both")
    for i, (u, o, red) in enumerate(zip(unopt_v, opt_v, var_red)):
        ax1.text(i, max(u, o) * 1.4, f"−{red:.0f}%",
                 ha="center", fontsize=9, color=C_RED, fontweight="bold")

    # ── Clauses ───────────────────────────────────────────────────────────────
    ax2.bar(x - w/2, unopt_c, w, color=C_UNOPT, alpha=0.85, label="Unoptimized (φ)")
    ax2.bar(x + w/2, opt_c,   w, color=C_OPT,   alpha=0.85, label="Optimized (φ')")
    ax2.set_xticks(x); ax2.set_xticklabels(xlbls, fontsize=11)
    ax2.set_yscale("log")
    ax2.set_title("Clause Count", fontsize=12)
    ax2.set_ylabel("# Clauses (log scale)")
    ax2.legend(fontsize=9)
    ax2.grid(axis="y", linestyle="--", alpha=0.4, which="both")
    for i, (u, o, red) in enumerate(zip(unopt_c, opt_c, cl_red)):
        ax2.text(i, max(u, o) * 1.4, f"−{red:.0f}%",
                 ha="center", fontsize=9, color=C_RED, fontweight="bold")

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, "cnf_encoding_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Plot saved -> {out}")


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Compare optimized vs unoptimized Sudoku CNF encodings")
    parser.add_argument("--sizes", nargs="*", type=int,
                        help="Board sizes to include, e.g. --sizes 4 9 16 25")
    parser.add_argument("--no-plot", action="store_true",
                        help="Print table only, skip matplotlib")
    args = parser.parse_args()

    print("CNF Encoding Comparison: Optimized (φ') vs Unoptimized (φ)")
    print("=" * 110)

    rows = run_comparison(filter_sizes=set(args.sizes) if args.sizes else None)

    if rows and not args.no_plot:
        plot_comparison(rows)


if __name__ == "__main__":
    main()