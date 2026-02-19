"""
benchmark.py
Full benchmark: puzzle sets -> CNF encode -> SAT + Backtracking -> plots.
Backtracking timeout = 10 min; shown as >10min in plots.
"""

import os, sys, csv, math, argparse, importlib.util
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "Output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TIMEOUT_PLOT_Y = 5 * 60
BT_TIMEOUT     = 5 * 60

def _load(name):
    path = os.path.join(SCRIPT_DIR, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def is_timeout(t):
    return t == float("inf") or t is None

def run_benchmark(solver_path=None, run_sat=True, run_bt=True):
    fetcher = _load("puzzle_fetcher")
    enc     = _load("sudoku_to_cnf")
    bt_mod  = _load("backtracking_solver")
    sat_mod = _load("sat_solver_runner")

    solver = sat_mod.find_solver(solver_path) if run_sat else None
    if run_sat and not solver:
        print("WARNING: No SAT solver found. SAT runs skipped.")
        print("Copy satch to Main/executable/satch and chmod +x it.")
        run_sat = False
    elif solver:
        print(f"SAT solver : {solver}")

    print("\n-- Fetching puzzle sets --")
    puzzle_list = fetcher.fetch_all(verbose=True)

    results = []
    print("\n-- Running solvers --")
    for n, group, puzzle_path in puzzle_list:
        basename = os.path.splitext(os.path.basename(puzzle_path))[0]
        print(f"\n  [{group}] {basename}")

        row = dict(group=group, size=n, puzzle=basename,
                   cnf_vars=0, cnf_clauses=0, enc_time=0,
                   sat_time=float("nan"), bt_time=float("nan"),
                   sat_status="skipped", bt_status="skipped")

        try:
            cnf_path, n_vars, n_clauses, enc_time = enc.convert_file(puzzle_path, verbose=False)
            row.update(cnf_vars=n_vars, cnf_clauses=n_clauses, enc_time=enc_time)
            print(f"    encode -> vars={n_vars} clauses={n_clauses} ({enc_time:.3f}s)")
        except Exception as e:
            print(f"    encode ERROR: {e}")
            results.append(row)
            continue

        if run_sat and solver:
            try:
                _, sat_time = sat_mod.solve_cnf(cnf_path, solver, verbose=True)
                row["sat_time"]   = sat_time if sat_time is not None else float("nan")
                row["sat_status"] = "solved" if sat_time is not None else "unsat/error"
            except Exception as e:
                print(f"    SAT ERROR: {e}")
                row["sat_status"] = "error"

        if run_bt:
            try:
                _, bt_time = bt_mod.solve_puzzle(puzzle_path, verbose=True, timeout=BT_TIMEOUT)
                if is_timeout(bt_time):
                    row["bt_time"]   = float("inf")
                    row["bt_status"] = "timeout"
                else:
                    row["bt_time"]   = bt_time if bt_time is not None else float("nan")
                    row["bt_status"] = "solved" if bt_time is not None else "unsolvable"
            except Exception as e:
                print(f"    BT ERROR: {e}")
                row["bt_status"] = "error"

        results.append(row)

    csv_path = os.path.join(OUTPUT_DIR, "benchmark_results.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResults saved -> {csv_path}")
    return results


def plot(results):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
    except ImportError:
        print("matplotlib not installed: pip install matplotlib numpy")
        return

    C_SAT = "#4C72B0"; C_BT = "#DD8452"
    C_TO  = "#CC3333"; C_ENC= "#55A868"

    GROUP_ORDER = ["4x4","17-clue","5-clue","16x16","25x25","36x36"]
    GROUP_LABEL = {"4x4":"4x4","17-clue":"9x9\n17-clue","5-clue":"9x9\n5-clue",
                   "16x16":"16x16","25x25":"25x25","36x36":"36x36"}

    from collections import defaultdict
    agg = defaultdict(lambda: dict(sat=[],bt=[],enc=[],vars=[],clauses=[]))
    for r in results:
        g = r["group"]
        st = r.get("sat_time", float("nan"))
        bt = r.get("bt_time",  float("nan"))
        if not (isinstance(st, float) and math.isnan(st)):
            agg[g]["sat"].append(st)
        agg[g]["bt"].append(bt)
        agg[g]["enc"].append(r["enc_time"])
        agg[g]["vars"].append(r["cnf_vars"])
        agg[g]["clauses"].append(r["cnf_clauses"])

    def safe_mean(lst):
        if not lst: return float("nan")
        if any(x == float("inf") for x in lst): return float("inf")
        finite = [x for x in lst if not math.isnan(x)]
        return sum(finite)/len(finite) if finite else float("nan")

    groups   = [g for g in GROUP_ORDER if g in agg]
    xlabels  = [GROUP_LABEL.get(g,g) for g in groups]
    x        = np.arange(len(groups))
    sat_m    = [safe_mean(agg[g]["sat"]) for g in groups]
    bt_m     = [safe_mean(agg[g]["bt"])  for g in groups]
    enc_m    = [safe_mean(agg[g]["enc"]) for g in groups]
    var_m    = [safe_mean(agg[g]["vars"]) for g in groups]
    cl_m     = [safe_mean(agg[g]["clauses"]) for g in groups]
    has_sat  = any(not math.isnan(v) for v in sat_m if v != float("inf"))

    # ── Plot 1: Main bar chart ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 6))
    fig.suptitle("Sudoku Solver Benchmark: SAT vs Backtracking",
                 fontsize=14, fontweight="bold")
    w = 0.30

    for i, g in enumerate(groups):
        sv, bv = sat_m[i], bt_m[i]
        if has_sat and not math.isnan(sv) and sv != float("inf"):
            ax.bar(x[i] - w/2, sv, w, color=C_SAT, alpha=0.85)
        elif has_sat and sv == float("inf"):
            ax.bar(x[i] - w/2, TIMEOUT_PLOT_Y, w, color=C_TO, alpha=0.7, hatch="//")

        if bv == float("inf"):
            ax.bar(x[i] + w/2, TIMEOUT_PLOT_Y, w, color=C_TO, alpha=0.7, hatch="//")
            ax.text(x[i] + w/2, TIMEOUT_PLOT_Y*1.15, ">10min",
                    ha="center", va="bottom", fontsize=8, color=C_TO, fontweight="bold")
        elif not math.isnan(bv):
            ax.bar(x[i] + w/2, bv, w, color=C_BT, alpha=0.85)

    ax.set_xticks(x); ax.set_xticklabels(xlabels, fontsize=10)
    ax.set_xlabel("Puzzle Group", fontsize=11)
    ax.set_ylabel("Solve Time (seconds, log scale)", fontsize=11)
    ax.set_yscale("log"); ax.set_ylim(bottom=1e-4)
    ax.grid(axis="y", linestyle="--", alpha=0.4, which="both")
    patches = []
    if has_sat: patches.append(mpatches.Patch(color=C_SAT, label="SAT Solver (satch)"))
    patches.append(mpatches.Patch(color=C_BT, label="Backtracking (MRV+FC)"))
    patches.append(mpatches.Patch(color=C_TO, label=">10 min timeout", hatch="//"))
    ax.legend(handles=patches, fontsize=9)
    plt.tight_layout()
    out1 = os.path.join(OUTPUT_DIR, "timing_comparison.png")
    plt.savefig(out1, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Plot -> {out1}")

    # ── Plot 2: Line plot + CNF size ────────────────────────────
    fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(14, 5))
    fig2.suptitle("Scaling Analysis", fontsize=13, fontweight="bold")

    def to_plot(vals):
        return [TIMEOUT_PLOT_Y if v==float("inf") else (None if math.isnan(v) else v)
                for v in vals]

    sat_y = to_plot(sat_m); bt_y = to_plot(bt_m)
    xl    = [l.replace("\n"," ") for l in xlabels]

    valid_sat = [(xl[i],sat_y[i]) for i in range(len(xl)) if sat_y[i] is not None]
    valid_bt  = [(xl[i],bt_y[i])  for i in range(len(xl)) if bt_y[i]  is not None]
    to_bt     = [(xl[i],bt_y[i])  for i in range(len(xl))
                 if bt_y[i]==TIMEOUT_PLOT_Y]

    if has_sat and valid_sat:
        xs,ys = zip(*valid_sat)
        ax2a.plot(xs, ys, "o-", color=C_SAT, lw=2, ms=7, label="SAT Solver")
    if valid_bt:
        xs2, ys2 = zip(*[(a,b) for a,b in valid_bt if b!=TIMEOUT_PLOT_Y]) if any(b!=TIMEOUT_PLOT_Y for a,b in valid_bt) else ([],[])
        if xs2: ax2a.plot(xs2, ys2, "s-", color=C_BT, lw=2, ms=7, label="Backtracking")
    if to_bt:
        xs3,ys3 = zip(*to_bt)
        ax2a.plot(xs3, ys3, "v", color=C_TO, ms=12, label=">10 min timeout")
    ax2a.set_yscale("log"); ax2a.set_ylim(bottom=1e-4)
    ax2a.set_xlabel("Puzzle Group"); ax2a.set_ylabel("Time (s, log)")
    ax2a.set_title("Solve Time Scaling"); ax2a.legend(fontsize=8)
    ax2a.grid(True, which="both", linestyle="--", alpha=0.4)

    ax2b_r = ax2b.twinx()
    ax2b.plot(xl, var_m, "o-", color=C_ENC, lw=2, ms=7, label="Variables")
    ax2b_r.plot(xl, cl_m, "s--", color="#9467BD", lw=2, ms=7, label="Clauses")
    ax2b.set_xlabel("Puzzle Group")
    ax2b.set_ylabel("CNF Variables", color=C_ENC)
    ax2b_r.set_ylabel("CNF Clauses", color="#9467BD")
    ax2b.set_title("CNF Size (Optimised Encoding)")
    ax2b.tick_params(axis="y", labelcolor=C_ENC)
    ax2b_r.tick_params(axis="y", labelcolor="#9467BD")
    l1,n1=ax2b.get_legend_handles_labels(); l2,n2=ax2b_r.get_legend_handles_labels()
    ax2b.legend(l1+l2, n1+n2, fontsize=8, loc="upper left")
    ax2b.grid(axis="x", linestyle="--", alpha=0.4)

    plt.tight_layout()
    out2 = os.path.join(OUTPUT_DIR, "scaling_analysis.png")
    plt.savefig(out2, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Plot -> {out2}")

    # ── Plot 3: 9x9 deep dive ───────────────────────────────────
    nine_r = [r for r in results if r["group"] in ("17-clue","5-clue")]
    if nine_r:
        fig3, ax3 = plt.subplots(figsize=(12, 5))
        fig3.suptitle("9x9 Deep Dive: 17-clue vs 5-clue", fontsize=13, fontweight="bold")
        nx = np.arange(len(nine_r))
        nlbls = [f"{r['group']}\n#{r['puzzle'].split('_')[-1]}" for r in nine_r]
        sv_n = [r["sat_time"] if not math.isnan(r.get("sat_time",float("nan"))) else 0 for r in nine_r]
        bv_n = [min(r["bt_time"], TIMEOUT_PLOT_Y) if r["bt_time"]!=float("inf")
                else TIMEOUT_PLOT_Y for r in nine_r]
        if has_sat: ax3.bar(nx-w/2, sv_n, w, color=C_SAT, alpha=0.85, label="SAT")
        ax3.bar(nx+w/2, bv_n, w, color=C_BT, alpha=0.85, label="Backtracking")
        for i,r in enumerate(nine_r):
            if r["bt_time"]==float("inf"):
                ax3.text(nx[i]+w/2, TIMEOUT_PLOT_Y*1.1, ">10m",
                         ha="center", va="bottom", fontsize=7, color=C_TO, fontweight="bold")
        ax3.set_xticks(nx); ax3.set_xticklabels(nlbls, fontsize=8)
        ax3.set_yscale("log"); ax3.set_ylim(bottom=1e-5)
        ax3.set_xlabel("Puzzle"); ax3.set_ylabel("Solve Time (s, log)")
        ax3.legend(); ax3.grid(axis="y", linestyle="--", alpha=0.4, which="both")
        plt.tight_layout()
        out3 = os.path.join(OUTPUT_DIR, "nine_by_nine_deepdive.png")
        plt.savefig(out3, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Plot -> {out3}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver")
    parser.add_argument("--no-sat",  action="store_true")
    parser.add_argument("--no-bt",   action="store_true")
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument("--from-csv", help="Re-plot from existing CSV")
    args = parser.parse_args()

    if args.from_csv:
        with open(args.from_csv) as f:
            reader = csv.DictReader(f)
            results = []
            for row in reader:
                row["size"]=int(row["size"]); row["cnf_vars"]=int(row["cnf_vars"])
                row["cnf_clauses"]=int(row["cnf_clauses"]); row["enc_time"]=float(row["enc_time"])
                row["sat_time"]=float(row["sat_time"])
                bt=row["bt_time"]; row["bt_time"]=float("inf") if bt in("inf","Infinity") else float(bt)
                results.append(row)
        plot(results)
        return

    results = run_benchmark(solver_path=args.solver,
                            run_sat=not args.no_sat,
                            run_bt=not args.no_bt)
    if not args.no_plot:
        plot(results)

if __name__ == "__main__":
    main()