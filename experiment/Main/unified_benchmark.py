"""
unified_benchmark.py
════════════════════
Core orchestrator module for the Sudoku SAT vs. Backtracking benchmarking pipeline.

Key Features:
  1. Configurable Seed Control & Repetition (--seed, --repeats, --puzzles-per-size, --sizes)
  2. 120-second Timeout Enforced Across ALL Solvers
  3. Triple Encoding Benchmark: Naive (phi), Compact (phi'), and Logarithmic
  4. Solution Persistence: Decoded grids, raw SAT assignments, and cross-method checks
  5. Solution Validation & Uniqueness Verification
  6. Integrated Workflow: Dataset -> Solvers -> Per-Generator CSVs -> Combined Stats/Plots
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
from log_encoder import decode_log_assignment
from sat_solver_runner import find_solver, run_solver_raw, decode_solution
from backtracking_solver import solve_puzzle
from uniqueness import validate_solution
import solution_recorder as recorder
from statistical_analysis import analyze_benchmark_results
import plot_results

TIMEOUT_SECONDS = 120
TIMEOUT_SENTINEL = float("inf")

BENCHMARK_FIELDS = [
    "run_id", "repeat", "generator", "master_seed", "puzzle_seed", "attempt",
    "group", "size", "puzzle_name", "num_clues", "fill_pct", "verified_unique",
    "naive_vars", "naive_clauses", "naive_enc_time",
    "compact_vars", "compact_clauses", "compact_enc_time",
    "log_vars", "log_clauses", "log_enc_time",
    "sat_compact_time", "sat_compact_e2e", "sat_compact_status",
    "sat_naive_time", "sat_naive_e2e", "sat_naive_status",
    "sat_log_time", "sat_log_e2e", "sat_log_status",
    "bt_time", "bt_status", "validator_passed",
]


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
    if t < 0.001:
        return f"{t*1000:.3f}ms"
    return f"{t:.6f}s"


def _run_single_generator_benchmark(sizes=None, puzzles_per_size=10, repeats=3, seed=42,
                                    solver_path=None, timeout=TIMEOUT_SECONDS,
                                    no_plot=False, no_stats=False, generator="back_circulant",
                                    solution_dir=None, save_solutions=True,
                                    save_assignments=True):
    if sizes is None:
        sizes = [4, 9, 16, 25, 36]

    if solution_dir is None:
        solution_dir = os.path.join(RESULTS_DIR, "Solutions", generator)
    solution_manifest_path = os.path.join(solution_dir, "solution_manifest.csv")
    solution_comparison_path = os.path.join(solution_dir, "solution_comparison.csv")
    csv_path = os.path.join(RESULTS_DIR, f"benchmark_results_{generator}.csv")

    solver = find_solver(solver_path)
    if not solver:
        print("\n[WARN] No executable SAT solver found. SAT solver benchmarks will be skipped.")
        print("       Install CaDiCaL or place 'satch' in Main/executable/, or pass --solver path.")
    else:
        print(f"\n[INFO] Found SAT Solver binary: {solver}")

    print(f"\n--- STEP 1: Assembling Dataset ---")
    print(f"Sizes: {sizes} | Puzzles/size: {puzzles_per_size} | "
          f"Master Seed: {seed} | Generator: {generator}")
    dataset = assemble_dataset(
        sizes=sizes,
        puzzles_per_size=puzzles_per_size,
        seed=seed,
        solver_path=solver,
        timeout=timeout,
        generator=generator,
        generation_timeout=timeout,
    )

    all_results = []
    run_counter = 1
    solution_manifest_rows = []
    solution_comparison_rows = []
    consolidated = {}

    if save_solutions:
        os.makedirs(solution_dir, exist_ok=True)
        recorder.write_csv(
            solution_manifest_path,
            recorder.SOLUTION_MANIFEST_FIELDS,
            solution_manifest_rows,
        )
        recorder.write_csv(
            solution_comparison_path,
            recorder.SOLUTION_COMPARISON_FIELDS,
            solution_comparison_rows,
        )

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
            log_vars, log_clauses, log_enc_time = 0, 0, 0.0
            naive_cnf_path, compact_cnf_path, log_cnf_path = None, None, None

            try:
                enc_res = encode_puzzle_both(puzzle_path, CNF_DIR)
                naive_cnf_path = enc_res["naive_cnf"]
                compact_cnf_path = enc_res["compact_cnf"]
                log_cnf_path = enc_res["log_cnf"]
                comp = enc_res["comparison"]

                naive_vars = comp["naive"]["num_vars"]
                naive_clauses = comp["naive"]["num_clauses"]
                naive_enc_time = comp["naive"]["encode_time_s"]

                compact_vars = comp["compact"]["num_vars"]
                compact_clauses = comp["compact"]["num_clauses"]
                compact_enc_time = comp["compact"]["encode_time_s"]
                log_vars = comp["log"]["num_vars"]
                log_clauses = comp["log"]["num_clauses"]
                log_enc_time = comp["log"]["encode_time_s"]

                print(f"  Naive Enc:   {naive_vars:,} vars, {naive_clauses:,} clauses ({naive_enc_time:.4f}s)")
                print(f"  Compact Enc: {compact_vars:,} vars, {compact_clauses:,} clauses ({compact_enc_time:.4f}s)")
                print(f"  Log Enc:     {log_vars:,} vars, {log_clauses:,} clauses ({log_enc_time:.4f}s)")
            except Exception as e:
                print(f"  [ERROR] Encoding failed: {e}")

            solutions = {}
            assignments = {}
            raw_lines_by_method = {}
            invoked = {
                "compact": bool(solver and compact_cnf_path and os.path.exists(compact_cnf_path)),
                "naive": bool(solver and naive_cnf_path and os.path.exists(naive_cnf_path)),
                "log": bool(solver and log_cnf_path and os.path.exists(log_cnf_path)),
            }

            # 2. SAT Compact (with end-to-end timing including encoding)
            sat_compact_time = float("nan")
            sat_compact_e2e = float("nan")
            sat_compact_status = "skipped"
            if solver and compact_cnf_path and os.path.exists(compact_cnf_path):
                t_enc_total = compact_enc_time  # encoding already done above
                assignment_c, raw_c = [], []
                try:
                    sat_c, assignment_c, elapsed_c, raw_c = run_solver_raw(
                        solver, compact_cnf_path, timeout=timeout
                    )
                    assignments["compact"] = assignment_c
                    raw_lines_by_method["compact"] = raw_c
                    sat_compact_e2e = t_enc_total + elapsed_c  # end-to-end = encode + solve
                    if elapsed_c >= timeout or (not sat_c and elapsed_c >= timeout - 1):
                        sat_compact_time = float("inf")
                        sat_compact_e2e = float("inf")
                        sat_compact_status = "timeout"
                    elif sat_c and not assignment_c:
                        sat_compact_time = elapsed_c
                        sat_compact_status = "error"
                        print("  [ERROR] SAT Compact returned SAT without a parseable model")
                    elif sat_c:
                        sat_compact_time = elapsed_c
                        sat_compact_status = "solved"
                        grid_c, _ = decode_solution(assignment_c, puzzle_path)
                        solutions["compact"] = grid_c
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
                assignment_n, raw_n = [], []
                try:
                    sat_n, assignment_n, elapsed_n, raw_n = run_solver_raw(
                        solver, naive_cnf_path, timeout=timeout
                    )
                    assignments["naive"] = assignment_n
                    raw_lines_by_method["naive"] = raw_n
                    sat_naive_e2e = t_enc_total_n + elapsed_n
                    if elapsed_n >= timeout or (not sat_n and elapsed_n >= timeout - 1):
                        sat_naive_time = float("inf")
                        sat_naive_e2e = float("inf")
                        sat_naive_status = "timeout"
                    elif sat_n and not assignment_n:
                        sat_naive_time = elapsed_n
                        sat_naive_status = "error"
                        print("  [ERROR] SAT Naive returned SAT without a parseable model")
                    elif sat_n:
                        sat_naive_time = elapsed_n
                        sat_naive_status = "solved"
                        grid_n = decode_naive(assignment_n, puzzle_grid, n)
                        solutions["naive"] = grid_n
                    else:
                        sat_naive_time = elapsed_n
                        sat_naive_status = "unsat"
                except Exception as e:
                    print(f"  [ERROR] SAT Naive execution error: {e}")
                    sat_naive_time = float("inf")
                    sat_naive_e2e = float("inf")
                    sat_naive_status = "error"

            print(f"  SAT Naive:   {format_disp_time(sat_naive_time, timeout)} solve / {format_disp_time(sat_naive_e2e, timeout)} e2e ({sat_naive_status})")

            # 4. SAT Logarithmic (with end-to-end timing including encoding)
            sat_log_time = float("nan")
            sat_log_e2e = float("nan")
            sat_log_status = "skipped"
            if solver and log_cnf_path and os.path.exists(log_cnf_path):
                assignment_l, raw_l = [], []
                try:
                    sat_l, assignment_l, elapsed_l, raw_l = run_solver_raw(
                        solver, log_cnf_path, timeout=timeout
                    )
                    assignments["log"] = assignment_l
                    raw_lines_by_method["log"] = raw_l
                    sat_log_e2e = log_enc_time + elapsed_l
                    if elapsed_l >= timeout or (not sat_l and elapsed_l >= timeout - 1):
                        sat_log_time = float("inf")
                        sat_log_e2e = float("inf")
                        sat_log_status = "timeout"
                    elif sat_l and not assignment_l:
                        sat_log_time = elapsed_l
                        sat_log_status = "error"
                        print("  [ERROR] SAT Log returned SAT without a parseable model")
                    elif sat_l:
                        sat_log_time = elapsed_l
                        sat_log_status = "solved"
                        solutions["log"] = decode_log_assignment(
                            assignment_l, puzzle_grid, n
                        )
                    else:
                        sat_log_time = elapsed_l
                        sat_log_status = "unsat"
                except Exception as e:
                    print(f"  [ERROR] SAT Log execution error: {e}")
                    sat_log_time = float("inf")
                    sat_log_e2e = float("inf")
                    sat_log_status = "error"

            print(f"  SAT Log:     {format_disp_time(sat_log_time, timeout)} solve / {format_disp_time(sat_log_e2e, timeout)} e2e ({sat_log_status})")

            # 5. Backtracking Solver
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
                        solutions["bt"] = grid_bt
                else:
                    bt_time = bt_elapsed
                    bt_status = "unsolvable"
            except Exception as e:
                print(f"  [ERROR] Backtracking solver error: {e}")
                bt_time = float("inf")
                bt_status = "error"

            print(f"  Backtrack:   {format_disp_time(bt_time, timeout)} ({bt_status})")

            run_id = f"{generator}_{run_counter:04d}"

            method_meta = {
                "compact": {
                    "encoding": "compact (Kwon & Jain)",
                    "status": sat_compact_status,
                    "solve_time_s": sat_compact_time,
                    "e2e_time_s": sat_compact_e2e,
                    "cnf": compact_cnf_path,
                },
                "naive": {
                    "encoding": "naive (N^3 direct)",
                    "status": sat_naive_status,
                    "solve_time_s": sat_naive_time,
                    "e2e_time_s": sat_naive_e2e,
                    "cnf": naive_cnf_path,
                },
                "log": {
                    "encoding": "logarithmic (zero-aux binary)",
                    "status": sat_log_status,
                    "solve_time_s": sat_log_time,
                    "e2e_time_s": sat_log_e2e,
                    "cnf": log_cnf_path,
                },
                "bt": {
                    "encoding": "backtracking (MRV + degree + FC)",
                    "status": bt_status,
                    "solve_time_s": bt_time,
                    "e2e_time_s": bt_time,
                    "cnf": "",
                },
            }

            reference = recorder.read_reference_solution(puzzle_path, n)
            comparison = recorder.compare_solutions(n, reference, solutions)

            valid_by_method = {}
            clues_by_method = {}
            grid_hashes = {}
            for method in recorder.METHODS:
                grid = solutions.get(method)
                if grid is None:
                    valid_by_method[method] = None
                    clues_by_method[method] = None
                    grid_hashes[method] = ""
                else:
                    valid_by_method[method] = validate_solution(grid, n).get("valid", False)
                    clues_by_method[method] = recorder.grid_matches_clues(grid, puzzle_grid)
                    grid_hashes[method] = recorder.grid_hash(grid)

            validator_passed = (
                all(valid_by_method[method] for method in solutions)
                if solutions else True
            )

            print(f"  Validation:  {'PASSED' if validator_passed else 'FAILED'}")
            solved_summary = " ".join(
                f"{method}={'OK' if method in solutions else '--'}"
                for method in recorder.METHODS
            )
            all_clues = (
                recorder.flag(all(clues_by_method[method] for method in solutions))
                if solutions else "N/A"
            )
            print(f"  Solutions:   {solved_summary}")
            print(f"  Solution match: all_equal={comparison['all_equal']} "
                  f"reference={comparison['all_match_reference']} "
                  f"clues={all_clues} diffs={comparison['mismatch_count']}")

            if save_solutions:
                puzzle_dir = os.path.join(solution_dir, puzzle_name)
                puzzle_solution_dir = os.path.join(puzzle_dir, "runs")
                os.makedirs(puzzle_solution_dir, exist_ok=True)

                if reference is not None:
                    recorder.write_reference_file(
                        os.path.join(puzzle_dir, "reference_solution.txt"),
                        size=n,
                        puzzle_name=puzzle_name,
                        reference=reference,
                    )

                method_rows = []
                solution_paths = {}
                assignment_paths = {}

                for method in recorder.METHODS:
                    meta = method_meta[method]
                    solution_path = os.path.join(
                        puzzle_solution_dir,
                        f"run_{rep:02d}_{method}_solution.txt",
                    )
                    recorder.write_solution_file(
                        solution_path,
                        size=n,
                        puzzle_name=puzzle_name,
                        run_id=run_id,
                        repeat=rep,
                        method=method,
                        encoding=meta["encoding"],
                        status=meta["status"],
                        solve_time_s=meta["solve_time_s"],
                        e2e_time_s=meta["e2e_time_s"],
                        grid=solutions.get(method),
                        valid=valid_by_method[method],
                        matches_clues=clues_by_method[method],
                        matches_reference=comparison["matches_reference"][method],
                        matches_bt=comparison["matches_bt"][method],
                        all_equal=comparison["all_equal"],
                    )
                    solution_paths[method] = solution_path

                    if save_assignments and method in ("compact", "naive", "log") and invoked.get(method):
                        assignment_path = os.path.join(
                            puzzle_solution_dir,
                            f"run_{rep:02d}_{method}_assignment.txt",
                        )
                        recorder.write_assignment_file(
                            assignment_path,
                            puzzle_name=puzzle_name,
                            run_id=run_id,
                            repeat=rep,
                            method=method,
                            encoding=meta["encoding"],
                            cnf_path=meta["cnf"],
                            status=meta["status"],
                            solve_time_s=meta["solve_time_s"],
                            raw_lines=raw_lines_by_method.get(method, []),
                            model_hash_value=recorder.model_hash(
                                assignments.get(method)
                            ),
                        )
                        assignment_paths[method] = assignment_path

                    method_rows.append({
                        "run_id": run_id,
                        "repeat": rep,
                        "generator": entry.get("generator", generator),
                        "puzzle_seed": entry.get("seed", entry.get("puzzle_seed", "")),
                        "group": group,
                        "size": n,
                        "puzzle_name": puzzle_name,
                        "method": method,
                        "encoding": meta["encoding"],
                        "status": meta["status"],
                        "solve_time_s": recorder.format_time(meta["solve_time_s"]),
                        "e2e_time_s": recorder.format_time(meta["e2e_time_s"]),
                        "solution_path": solution_path,
                        "assignment_path": assignment_paths.get(method, ""),
                        "grid_hash": grid_hashes[method],
                        "model_hash": recorder.model_hash(
                            assignments.get(method)
                        ) if method != "bt" else "",
                        "valid": recorder.flag(valid_by_method[method]),
                        "matches_clues": recorder.flag(clues_by_method[method]),
                        "matches_reference": comparison["matches_reference"][method],
                        "matches_bt": comparison["matches_bt"][method],
                        "all_equal": comparison["all_equal"],
                    })

                state = consolidated.setdefault(puzzle_name, {
                    "size": n,
                    "runs": {},
                    "solution": {},
                    "raw": {},
                    "valid": {},
                    "matches_clues": {},
                })
                for method in recorder.METHODS:
                    meta = method_meta[method]
                    state["runs"].setdefault(method, []).append({
                        "repeat": rep,
                        "status": meta["status"],
                        "solve_time_s": meta["solve_time_s"],
                    })
                    if solutions.get(method) is not None:
                        state["solution"][method] = solutions[method]
                    if method in raw_lines_by_method:
                        state["raw"][method] = raw_lines_by_method[method]
                    state["valid"][method] = valid_by_method[method]
                    state["matches_clues"][method] = clues_by_method[method]

                for method in ("compact", "naive", "log"):
                    recorder.write_consolidated_sat(
                        os.path.join(puzzle_dir, f"SAT_{method}.txt"),
                        size=n,
                        puzzle_name=puzzle_name,
                        method=method,
                        encoding=method_meta[method]["encoding"],
                        runs=state["runs"].get(method, []),
                        solution=state["solution"].get(method),
                        raw_lines=state["raw"].get(method, []),
                        model_hash_value=recorder.model_hash(
                            assignments.get(method)
                        ),
                        valid=state["valid"].get(method),
                        matches_clues=state["matches_clues"].get(method),
                        matches_reference=comparison["matches_reference"][method],
                        matches_bt=comparison["matches_bt"][method],
                    )
                recorder.write_consolidated_bt(
                    os.path.join(puzzle_dir, "BACKTRACKING.txt"),
                    size=n,
                    puzzle_name=puzzle_name,
                    runs=state["runs"].get("bt", []),
                    solution=state["solution"].get("bt"),
                    valid=state["valid"].get("bt"),
                    matches_clues=state["matches_clues"].get("bt"),
                    matches_reference=comparison["matches_reference"]["bt"],
                )

                diff_path = ""
                if comparison["mismatch_count"] > 0:
                    diff_path = os.path.join(
                        puzzle_solution_dir, f"run_{rep:02d}_diff.txt"
                    )
                    recorder.write_diff_file(
                        diff_path,
                        reference=reference,
                        solutions=solutions,
                        diffs=comparison["diffs"],
                    )

                report_path = os.path.join(
                    puzzle_solution_dir, f"run_{rep:02d}_report.txt"
                )
                recorder.write_report(
                    report_path,
                    size=n,
                    puzzle_name=puzzle_name,
                    run_id=run_id,
                    repeat=rep,
                    reference=reference,
                    solutions=solutions,
                    method_rows=method_rows,
                    comparison=comparison,
                )

                solution_manifest_rows.extend(method_rows)
                solution_comparison_rows.append({
                    "run_id": run_id,
                    "repeat": rep,
                    "generator": entry.get("generator", generator),
                    "puzzle_seed": entry.get("seed", entry.get("puzzle_seed", "")),
                    "group": group,
                    "size": n,
                    "puzzle_name": puzzle_name,
                    "reference_present": comparison["reference_present"],
                    "reference_hash": recorder.grid_hash(reference),
                    "compact_hash": grid_hashes.get("compact", ""),
                    "naive_hash": grid_hashes.get("naive", ""),
                    "log_hash": grid_hashes.get("log", ""),
                    "bt_hash": grid_hashes.get("bt", ""),
                    "compact_matches_bt": comparison["matches_bt"]["compact"],
                    "naive_matches_bt": comparison["matches_bt"]["naive"],
                    "log_matches_bt": comparison["matches_bt"]["log"],
                    "solved_count": comparison["solved_count"],
                    "solved_methods": comparison["solved_methods"],
                    "all_equal": comparison["all_equal"],
                    "all_match_reference": comparison["all_match_reference"],
                    "all_methods_solved": comparison["all_methods_solved"],
                    "mismatch_count": comparison["mismatch_count"],
                    "diff_path": diff_path,
                })

                recorder.write_csv(
                    solution_manifest_path,
                    recorder.SOLUTION_MANIFEST_FIELDS,
                    solution_manifest_rows,
                )
                recorder.write_csv(
                    solution_comparison_path,
                    recorder.SOLUTION_COMPARISON_FIELDS,
                    solution_comparison_rows,
                )
                print(f"  Solutions saved: {os.path.abspath(puzzle_dir)}")

            # Record result row
            row = {
                "run_id": run_id,
                "repeat": rep,
                "generator": entry.get("generator", generator),
                "master_seed": entry.get("master_seed", seed),
                "puzzle_seed": entry.get("seed", entry.get("puzzle_seed", "")),
                "attempt": entry.get("attempt", 0),
                "group": group,
                "size": n,
                "puzzle_name": puzzle_name,
                "num_clues": num_clues,
                "fill_pct": entry.get("fill_pct", ""),
                "verified_unique": entry.get("verified_unique", ""),
                "naive_vars": naive_vars,
                "naive_clauses": naive_clauses,
                "naive_enc_time": f"{naive_enc_time:.6f}",
                "compact_vars": compact_vars,
                "compact_clauses": compact_clauses,
                "compact_enc_time": f"{compact_enc_time:.6f}",
                "log_vars": log_vars,
                "log_clauses": log_clauses,
                "log_enc_time": f"{log_enc_time:.6f}",
                "sat_compact_time": "inf" if math.isinf(sat_compact_time) else f"{sat_compact_time:.6f}",
                "sat_compact_e2e": "inf" if (isinstance(sat_compact_e2e, float) and math.isinf(sat_compact_e2e)) else (f"{sat_compact_e2e:.6f}" if not math.isnan(sat_compact_e2e) else "nan"),
                "sat_compact_status": sat_compact_status,
                "sat_naive_time": "inf" if math.isinf(sat_naive_time) else f"{sat_naive_time:.6f}",
                "sat_naive_e2e": "inf" if (isinstance(sat_naive_e2e, float) and math.isinf(sat_naive_e2e)) else (f"{sat_naive_e2e:.6f}" if not math.isnan(sat_naive_e2e) else "nan"),
                "sat_naive_status": sat_naive_status,
                "sat_log_time": "inf" if math.isinf(sat_log_time) else f"{sat_log_time:.6f}",
                "sat_log_e2e": "inf" if (isinstance(sat_log_e2e, float) and math.isinf(sat_log_e2e)) else (f"{sat_log_e2e:.6f}" if not math.isnan(sat_log_e2e) else "nan"),
                "sat_log_status": sat_log_status,
                "bt_time": "inf" if math.isinf(bt_time) else f"{bt_time:.6f}",
                "bt_status": bt_status,
                "validator_passed": validator_passed,
            }
            all_results.append(row)
            run_counter += 1

            # Incremental CSV save
            fieldnames = BENCHMARK_FIELDS
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_results)

    # STEP 3: Write CSV Results
    fieldnames = BENCHMARK_FIELDS

    print(f"\n--- STEP 3: Writing Benchmark CSV Results ---")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    print(f"Results written to: {csv_path}")

    if save_solutions:
        print(f"Solution artifacts: {os.path.abspath(solution_dir)}")
        print(f"Solution manifest:  {solution_manifest_path}")
        print(f"Solution comparison: {solution_comparison_path}")

    # STEP 4: Statistical Analysis (Memory/internal structure only, no markdown file written)
    stats = {}
    if not no_stats:
        stats = analyze_benchmark_results(csv_path)

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



def run_benchmark_pipeline(sizes=None, puzzles_per_size=10, repeats=3, seed=42,
                           solver_path=None, timeout=TIMEOUT_SECONDS,
                           no_plot=False, no_stats=False, generator="both",
                           generators=None, solution_dir=None,
                           save_solutions=True, save_assignments=True):
    """Run one or both generators and write per-generator + combined results."""
    if generators is None:
        generators = ["legacy", "back_circulant"] if generator == "both" else [generator]
    if isinstance(generators, str):
        generators = [generators]

    combined_rows = []
    per_generator_paths = []
    for gen in generators:
        gen_solution_dir = (
            os.path.join(solution_dir, gen) if solution_dir
            else os.path.join(RESULTS_DIR, "Solutions", gen)
        )
        csv_path = _run_single_generator_benchmark(
            sizes=sizes,
            puzzles_per_size=puzzles_per_size,
            repeats=repeats,
            seed=seed,
            solver_path=solver_path,
            timeout=timeout,
            no_plot=True,
            no_stats=True,
            generator=gen,
            solution_dir=gen_solution_dir,
            save_solutions=save_solutions,
            save_assignments=save_assignments,
        )
        per_generator_paths.append(csv_path)
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                row = dict(row)
                row["generator"] = row.get("generator") or gen
                original_group = row.get("group", "")
                row["group"] = f"{gen} / {original_group}"
                combined_rows.append(row)

    combined_path = os.path.join(RESULTS_DIR, "benchmark_results_combined.csv")
    with open(combined_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=BENCHMARK_FIELDS)
        writer.writeheader()
        for row in combined_rows:
            writer.writerow({k: row.get(k, "") for k in BENCHMARK_FIELDS})
    print(f"Combined CSV written to: {combined_path}")

    if not no_stats:
        analyze_benchmark_results(combined_path)
    if not no_plot:
        print(f"\n--- Generating shared plots for all generators ---")
        try:
            plots = plot_results.generate_all_plots(combined_path, RESULTS_DIR)
            print(f"✓ {len(plots)} plot(s) generated in {RESULTS_DIR}")
        except Exception as e:
            print(f"[WARN] Plot generation encountered an issue: {e}")

    return combined_path

def main():
    parser = argparse.ArgumentParser(
        description="Unified Sudoku SAT vs Backtracking Benchmark Pipeline"
    )
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=[4, 9, 16, 25, 36],
        help="Grid sizes to include in benchmark (default: 4 9 16 25 36)"
    )
    parser.add_argument(
        "--puzzles-per-size", type=int, default=30,
        help="Number of puzzles per size per generator (default: 30)"
    )
    parser.add_argument(
        "--repeats", type=int, default=1,
        help="Number of benchmark repetition runs (default: 1)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Master random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--generator", choices=["both", "legacy", "back_circulant"], default="both",
        help="Puzzle generator: both (default), legacy, or back_circulant"
    )
    parser.add_argument(
        "--solver", type=str, default=None,
        help="Path to SAT solver binary (default: auto-find CaDiCaL, fallback satch)"
    )
    parser.add_argument(
        "--timeout", type=int, default=TIMEOUT_SECONDS,
        help="Solver timeout limit in seconds (default: 120)"
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
        "--no-save-solutions", action="store_true",
        help="Skip writing per-run solution, assignment, and comparison files"
    )
    parser.add_argument(
        "--no-save-assignments", action="store_true",
        help="Skip saving raw SAT assignments"
    )
    parser.add_argument(
        "--solution-dir", type=str, default=None,
        help="Directory for solution artifacts (default: Results/Solutions)"
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
            print(f"Stats computed in memory for {len(stats.get('groups', {}))} group(s) "
                  "(no report file written)")

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
        generator=args.generator,
        solution_dir=args.solution_dir,
        save_solutions=not args.no_save_solutions,
        save_assignments=not args.no_save_assignments,
    )


if __name__ == "__main__":
    main()
