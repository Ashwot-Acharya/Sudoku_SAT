"""
unified_benchmark.py
════════════════════
Core orchestrator module for the Sudoku SAT vs. Backtracking benchmarking pipeline.

Key Features:
  1. Configurable Seed Control & Repetition (--seed, --repeats, --puzzles-per-size, --sizes)
  2. 10-Minute Timeout (600s) Enforced Across ALL Solvers
  3. Dual Encoding Benchmark: Naive (phi) vs Compact (phi')
  4. Solution Validation & Uniqueness Verification
  5. Integrated Workflow: Dataset -> Solvers -> CSV -> Statistical Analysis -> Plots
"""

import os
import sys
import csv
import time
import math
import argparse

# Ensure Main directory is in Python path for local module imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

RESULTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "Results"))
CNF_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "CNF"))

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(CNF_DIR, exist_ok=True)

# Required project imports
from puzzle_manager import assemble_dataset, read_puzzle
from dual_encoder import encode_puzzle_both, compare_encodings
from sat_solver_runner import find_solver, run_solver, decode_solution
from backtracking_solver import solve_puzzle
from uniqueness import validate_solution
from statistical_analysis import analyze_benchmark_results, format_report
import plot_results

TIMEOUT_SECONDS = 600
TIMEOUT_SENTINEL = float("inf")


def decode_naive(assignment, puzzle_grid, n):
    """
    Decode a Naive encoding SAT assignment back to an n*n grid.
    Variable formula: var(r, c, v) = (r-1)*n*n + (c-1)*n + v (1-indexed)
    """
    grid = [row[:] for row in puzzle_grid]
    for var_idx in assignment:
        if 1 <= var_idx <= n * n * n:
            idx = var_idx - 1
            v = idx % n + 1
            c = (idx // n) % n + 1
            r = idx // (n * n) + 1
            grid[r - 1][c - 1] = v
    return grid


def parse_solution_grid(sol_path, n):
    """Parse solved grid from backtracking output text file."""
    if not sol_path or not os.path.exists(sol_path):
        return None
    grid = []
    with open(sol_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    reading = False
    for line in lines:
        if line == "SOLUTION":
            reading = True
            continue
        if reading:
            parts = line.split()
            if len(parts) == n:
                grid.append([int(x) for x in parts])
                if len(grid) == n:
                    break
    return grid if len(grid) == n else None


def format_disp_time(t, timeout_val):
    if math.isinf(t) or t >= timeout_val:
        return f">{int(timeout_val)}s"
    if math.isnan(t):
        return "N/A"
    return f"{t:.3f}s"


def run_benchmark_pipeline(sizes=None, puzzles_per_size=5, repeats=3, seed=42,
                           solver_path=None, timeout=TIMEOUT_SECONDS,
                           no_plot=False, no_stats=False):
    if sizes is None:
        sizes = [4, 9, 16, 25, 36]

    solver = find_solver(solver_path)
    if not solver:
        print("\n[WARN] No executable SAT solver found. SAT solver benchmarks will be skipped.")
        print("       Place 'satch' executable in Main/executable/ or pass --solver path.")
    else:
        print(f"\n[INFO] Found SAT Solver binary: {solver}")

    print(f"\n--- STEP 1: Assembling Dataset ---")
    print(f"Sizes: {sizes} | Puzzles/size: {puzzles_per_size} | Master Seed: {seed}")
    dataset = assemble_dataset(
        sizes=sizes,
        puzzles_per_size=puzzles_per_size,
        seed=seed,
        solver_path=solver,
        timeout=timeout,
    )

    all_results = []
    run_counter = 1

    print(f"\n--- STEP 2: Running Benchmarks (Repeats={repeats}, Timeout={timeout}s) ---")
    for rep in range(1, repeats + 1):
        print(f"\n════════════════════════════════════════════════════════════")
        print(f" REPEAT RUN {rep}/{repeats}")
        print(f"════════════════════════════════════════════════════════════")

        for entry in dataset:
            n = entry["n"]
            group = entry["group"]
            puzzle_path = entry["puzzle_path"]
            puzzle_name = os.path.splitext(os.path.basename(puzzle_path))[0]

            n_grid, puzzle_grid = read_puzzle(puzzle_path)
            num_clues = sum(1 for r in range(n) for c in range(n) if puzzle_grid[r][c] != 0)

            print(f"\n[{group}] {puzzle_name} ({n}x{n}, {num_clues} clues) - Run #{run_counter}")

            # 1. Dual CNF Encoding
            naive_vars, naive_clauses, naive_enc_time = 0, 0, 0.0
            compact_vars, compact_clauses, compact_enc_time = 0, 0, 0.0
            naive_cnf_path, compact_cnf_path = None, None

            try:
                enc_res = encode_puzzle_both(puzzle_path, CNF_DIR)
                naive_cnf_path = enc_res["naive_cnf"]
                compact_cnf_path = enc_res["compact_cnf"]
                comp = enc_res["comparison"]

                naive_vars = comp["naive"]["num_vars"]
                naive_clauses = comp["naive"]["num_clauses"]
                naive_enc_time = comp["naive"]["encode_time_s"]

                compact_vars = comp["compact"]["num_vars"]
                compact_clauses = comp["compact"]["num_clauses"]
                compact_enc_time = comp["compact"]["encode_time_s"]

                print(f"  Naive Enc:   {naive_vars:,} vars, {naive_clauses:,} clauses ({naive_enc_time:.4f}s)")
                print(f"  Compact Enc: {compact_vars:,} vars, {compact_clauses:,} clauses ({compact_enc_time:.4f}s)")
            except Exception as e:
                print(f"  [ERROR] Encoding failed: {e}")

            sol_grids = []

            # 2. SAT Compact (with end-to-end timing including encoding)
            sat_compact_time = float("nan")
            sat_compact_e2e = float("nan")
            sat_compact_status = "skipped"
            if solver and compact_cnf_path and os.path.exists(compact_cnf_path):
                t_enc_total = compact_enc_time  # encoding already done above
                try:
                    sat_c, assignment_c, elapsed_c = run_solver(solver, compact_cnf_path, timeout=timeout)
                    sat_compact_e2e = t_enc_total + elapsed_c  # end-to-end = encode + solve
                    if elapsed_c >= timeout or (not sat_c and elapsed_c >= timeout - 1):
                        sat_compact_time = float("inf")
                        sat_compact_e2e = float("inf")
                        sat_compact_status = "timeout"
                    elif sat_c:
                        sat_compact_time = elapsed_c
                        sat_compact_status = "solved"
                        grid_c, _ = decode_solution(assignment_c, puzzle_path)
                        sol_grids.append(grid_c)
                    else:
                        sat_compact_time = elapsed_c
                        sat_compact_status = "unsat"
                except Exception as e:
                    print(f"  [ERROR] SAT Compact execution error: {e}")
                    sat_compact_time = float("inf")
                    sat_compact_e2e = float("inf")
                    sat_compact_status = "error"

            print(f"  SAT Compact: {format_disp_time(sat_compact_time, timeout)} solve / {format_disp_time(sat_compact_e2e, timeout)} e2e ({sat_compact_status})")

            # 3. SAT Naive (with end-to-end timing including encoding)
            sat_naive_time = float("nan")
            sat_naive_e2e = float("nan")
            sat_naive_status = "skipped"
            if solver and naive_cnf_path and os.path.exists(naive_cnf_path):
                t_enc_total_n = naive_enc_time
                try:
                    sat_n, assignment_n, elapsed_n = run_solver(solver, naive_cnf_path, timeout=timeout)
                    sat_naive_e2e = t_enc_total_n + elapsed_n
                    if elapsed_n >= timeout or (not sat_n and elapsed_n >= timeout - 1):
                        sat_naive_time = float("inf")
                        sat_naive_e2e = float("inf")
                        sat_naive_status = "timeout"
                    elif sat_n:
                        sat_naive_time = elapsed_n
                        sat_naive_status = "solved"
                        grid_n = decode_naive(assignment_n, puzzle_grid, n)
                        sol_grids.append(grid_n)
                    else:
                        sat_naive_time = elapsed_n
                        sat_naive_status = "unsat"
                except Exception as e:
                    print(f"  [ERROR] SAT Naive execution error: {e}")
                    sat_naive_time = float("inf")
                    sat_naive_e2e = float("inf")
                    sat_naive_status = "error"

            print(f"  SAT Naive:   {format_disp_time(sat_naive_time, timeout)} solve / {format_disp_time(sat_naive_e2e, timeout)} e2e ({sat_naive_status})")

            # 4. Backtracking Solver
            bt_time = float("nan")
            bt_status = "error"
            try:
                sol_path, bt_elapsed = solve_puzzle(puzzle_path, verbose=False, timeout=timeout)
                if bt_elapsed == float("inf") or bt_elapsed >= timeout:
                    bt_time = float("inf")
                    bt_status = "timeout"
                elif sol_path and os.path.exists(sol_path):
                    bt_time = bt_elapsed
                    bt_status = "solved"
                    grid_bt = parse_solution_grid(sol_path, n)
                    if grid_bt:
                        sol_grids.append(grid_bt)
                else:
                    bt_time = bt_elapsed
                    bt_status = "unsolvable"
            except Exception as e:
                print(f"  [ERROR] Backtracking solver error: {e}")
                bt_time = float("inf")
                bt_status = "error"

            print(f"  Backtrack:   {format_disp_time(bt_time, timeout)} ({bt_status})")

            # 5. Validate All Returned Solutions
            validator_passed = True
            if sol_grids:
                for grid in sol_grids:
                    val_res = validate_solution(grid, n)
                    if not val_res.get("valid", False):
                        validator_passed = False
                        break

            print(f"  Validation:  {'PASSED' if validator_passed else 'FAILED'}")

            # Record result row
            row = {
                "run_id": f"run_{run_counter:04d}",
                "repeat": rep,
                "group": group,
                "size": n,
                "puzzle_name": puzzle_name,
                "num_clues": num_clues,
                "naive_vars": naive_vars,
                "naive_clauses": naive_clauses,
                "naive_enc_time": f"{naive_enc_time:.6f}",
                "compact_vars": compact_vars,
                "compact_clauses": compact_clauses,
                "compact_enc_time": f"{compact_enc_time:.6f}",
                "sat_compact_time": "inf" if math.isinf(sat_compact_time) else f"{sat_compact_time:.6f}",
                "sat_compact_e2e": "inf" if (isinstance(sat_compact_e2e, float) and math.isinf(sat_compact_e2e)) else (f"{sat_compact_e2e:.6f}" if not math.isnan(sat_compact_e2e) else "nan"),
                "sat_compact_status": sat_compact_status,
                "sat_naive_time": "inf" if math.isinf(sat_naive_time) else f"{sat_naive_time:.6f}",
                "sat_naive_e2e": "inf" if (isinstance(sat_naive_e2e, float) and math.isinf(sat_naive_e2e)) else (f"{sat_naive_e2e:.6f}" if not math.isnan(sat_naive_e2e) else "nan"),
                "sat_naive_status": sat_naive_status,
                "bt_time": "inf" if math.isinf(bt_time) else f"{bt_time:.6f}",
                "bt_status": bt_status,
                "validator_passed": validator_passed,
            }
            all_results.append(row)
            run_counter += 1

            # Incremental CSV save
            csv_path = os.path.join(RESULTS_DIR, "benchmark_results.csv")
            fieldnames = [
                "run_id", "repeat", "group", "size", "puzzle_name", "num_clues",
                "naive_vars", "naive_clauses", "naive_enc_time",
                "compact_vars", "compact_clauses", "compact_enc_time",
                "sat_compact_time", "sat_compact_e2e", "sat_compact_status",
                "sat_naive_time", "sat_naive_e2e", "sat_naive_status",
                "bt_time", "bt_status", "validator_passed"
            ]
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_results)

    # STEP 3: Write CSV Results
    csv_path = os.path.join(RESULTS_DIR, "benchmark_results.csv")
    fieldnames = [
        "run_id", "repeat", "group", "size", "puzzle_name", "num_clues",
        "naive_vars", "naive_clauses", "naive_enc_time",
        "compact_vars", "compact_clauses", "compact_enc_time",
        "sat_compact_time", "sat_compact_e2e", "sat_compact_status",
        "sat_naive_time", "sat_naive_e2e", "sat_naive_status",
        "bt_time", "bt_status", "validator_passed"
    ]

    print(f"\n--- STEP 3: Writing Benchmark CSV Results ---")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    print(f"Results written to: {csv_path}")

    # STEP 4: Statistical Analysis
    if not no_stats:
        print(f"\n--- STEP 4: Running Statistical Analysis ---")
        stats = analyze_benchmark_results(csv_path)
        report_md = format_report(stats)
        stats_md_path = os.path.join(RESULTS_DIR, "STATISTICAL_ANALYSIS.md")
        with open(stats_md_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"Report generated: {stats_md_path}")

    # STEP 5: Generate Plots
    if not no_plot:
        print(f"\n--- STEP 5: Generating Benchmark Plots ---")
        try:
            plots = plot_results.generate_all_plots(csv_path, RESULTS_DIR)
            print(f"✓ {len(plots)} plot(s) generated in {RESULTS_DIR}")
        except Exception as e:
            print(f"[WARN] Plot generation encountered an issue: {e}")

    print(f"\n✓ Unified benchmark pipeline execution complete!\n")
    return csv_path


def main():
    parser = argparse.ArgumentParser(
        description="Unified Sudoku SAT vs Backtracking Benchmark Pipeline"
    )
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=[4, 9, 16, 25, 36],
        help="Grid sizes to include in benchmark (default: 4 9 16 25 36)"
    )
    parser.add_argument(
        "--puzzles-per-size", type=int, default=5,
        help="Number of puzzles per size (default: 5)"
    )
    parser.add_argument(
        "--repeats", type=int, default=3,
        help="Number of benchmark repetition runs (default: 3)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Master random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--solver", type=str, default=None,
        help="Path to SAT solver binary (default: auto-find 'satch')"
    )
    parser.add_argument(
        "--timeout", type=int, default=TIMEOUT_SECONDS,
        help="Solver timeout limit in seconds (default: 600)"
    )
    parser.add_argument(
        "--no-plot", action="store_true",
        help="Skip plot generation"
    )
    parser.add_argument(
        "--no-stats", action="store_true",
        help="Skip statistical analysis report generation"
    )
    parser.add_argument(
        "--from-csv", type=str, default=None,
        help="Load existing CSV and re-run statistical analysis and plotting"
    )

    args = parser.parse_args()

    if args.from_csv:
        csv_path = os.path.abspath(args.from_csv)
        if not os.path.exists(csv_path):
            print(f"ERROR: File not found: {csv_path}")
            sys.exit(1)

        print(f"Re-running stats/plots from existing CSV: {csv_path}")
        if not args.no_stats:
            stats = analyze_benchmark_results(csv_path)
            report_md = format_report(stats)
            stats_md_path = os.path.join(RESULTS_DIR, "STATISTICAL_ANALYSIS.md")
            with open(stats_md_path, "w", encoding="utf-8") as f:
                f.write(report_md)
            print(f"Report generated: {stats_md_path}")

        if not args.no_plot:
            plot_results.generate_plots(csv_path, RESULTS_DIR)

        print("Done.")
        return

    run_benchmark_pipeline(
        sizes=args.sizes,
        puzzles_per_size=args.puzzles_per_size,
        repeats=args.repeats,
        seed=args.seed,
        solver_path=args.solver,
        timeout=args.timeout,
        no_plot=args.no_plot,
        no_stats=args.no_stats,
    )


if __name__ == "__main__":
    main()
