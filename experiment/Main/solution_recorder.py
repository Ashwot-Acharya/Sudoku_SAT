"""Persist per-encoding and backtracking solutions for benchmark runs."""

import csv
import hashlib
import math
import os


METHODS = ["compact", "naive", "log", "bt"]

SOLUTION_MANIFEST_FIELDS = [
    "run_id",
    "repeat",
    "generator",
    "puzzle_seed",
    "group",
    "size",
    "puzzle_name",
    "method",
    "encoding",
    "status",
    "solve_time_s",
    "e2e_time_s",
    "solution_path",
    "assignment_path",
    "grid_hash",
    "model_hash",
    "valid",
    "matches_clues",
    "matches_reference",
    "matches_bt",
    "all_equal",
]

SOLUTION_COMPARISON_FIELDS = [
    "run_id",
    "repeat",
    "generator",
    "puzzle_seed",
    "group",
    "size",
    "puzzle_name",
    "reference_present",
    "reference_hash",
    "compact_hash",
    "naive_hash",
    "log_hash",
    "bt_hash",
    "compact_matches_bt",
    "naive_matches_bt",
    "log_matches_bt",
    "solved_count",
    "solved_methods",
    "all_equal",
    "all_match_reference",
    "all_methods_solved",
    "mismatch_count",
    "diff_path",
]


def format_time(value):
    if value is None:
        return "N/A"
    if isinstance(value, float) and math.isnan(value):
        return "nan"
    if isinstance(value, float) and math.isinf(value):
        return "inf"
    return f"{float(value):.6f}"


def flag(value):
    if value is None:
        return "N/A"
    return "YES" if value else "NO"


SAT_STATUS_MAP = {
    "solved": "SAT",
    "sat": "SAT",
    "unsat": "UNSAT",
    "timeout": "TIMEOUT",
    "error": "ERROR",
    "skipped": "SKIPPED",
}

BT_STATUS_MAP = {
    "solved": "SOLVED",
    "timeout": "TIMEOUT",
    "unsolvable": "UNSOLVABLE",
    "error": "ERROR",
    "skipped": "SKIPPED",
}


def canonical_status(method, status):
    mapping = BT_STATUS_MAP if method == "bt" else SAT_STATUS_MAP
    key = (status or "unknown").lower()
    return mapping.get(key, key.upper())


def overall_status(method, runs):
    statuses = [canonical_status(method, run.get("status")) for run in runs]
    success = "SOLVED" if method == "bt" else "SAT"
    if success in statuses:
        return success
    for status in ("TIMEOUT", "ERROR", "UNSAT", "UNSOLVABLE", "SKIPPED"):
        if status in statuses:
            return status
    return statuses[0] if statuses else "UNKNOWN"


def grid_hash(grid):
    if grid is None:
        return ""
    payload = "\n".join(" ".join(str(v) for v in row) for row in grid)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def model_hash(assignment):
    if not assignment:
        return ""
    payload = " ".join(str(v) for v in sorted(set(assignment)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def grids_equal(first, second):
    return first is not None and second is not None and first == second


def grid_matches_clues(grid, puzzle):
    if grid is None or puzzle is None:
        return False
    if len(grid) != len(puzzle):
        return False
    for r in range(len(puzzle)):
        if len(grid[r]) != len(puzzle[r]):
            return False
        for c in range(len(puzzle[r])):
            clue = puzzle[r][c]
            if clue != 0 and grid[r][c] != clue:
                return False
    return True


def read_reference_solution(filepath, n):
    if not filepath or not os.path.exists(filepath):
        return None

    grid = []
    reading = False
    with open(filepath, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line == "SOLUTION":
                reading = True
                grid = []
                continue
            if not reading:
                continue
            parts = line.split()
            if len(parts) != n:
                return None
            try:
                grid.append([int(value) for value in parts])
            except ValueError:
                return None
            if len(grid) == n:
                break

    return grid if len(grid) == n else None


def diff_cells(n, reference, solutions):
    rows = []
    for r in range(n):
        for c in range(n):
            values = {
                method: solutions[method][r][c]
                for method in METHODS
                if solutions.get(method) is not None
            }
            if not values:
                continue
            reference_value = reference[r][c] if reference is not None else None
            differs = len(set(values.values())) > 1
            if reference_value is not None:
                differs = differs or any(value != reference_value for value in values.values())
            if differs:
                rows.append((r + 1, c + 1, reference_value, values))
    return rows


def compare_solutions(n, reference, solutions):
    present = [method for method in METHODS if solutions.get(method) is not None]
    reference_present = reference is not None

    matches_reference = {}
    for method in METHODS:
        grid = solutions.get(method)
        if grid is None or reference is None:
            matches_reference[method] = "N/A"
        else:
            matches_reference[method] = flag(grid == reference)

    bt = solutions.get("bt")
    matches_bt = {}
    for method in ("compact", "naive", "log"):
        grid = solutions.get(method)
        if grid is None or bt is None:
            matches_bt[method] = "N/A"
        else:
            matches_bt[method] = flag(grid == bt)
    matches_bt["bt"] = "N/A"

    all_equal = "N/A"
    if len(present) >= 2:
        first = solutions[present[0]]
        all_equal = flag(all(solutions[method] == first for method in present[1:]))

    all_match_reference = "N/A"
    if reference is not None and present:
        all_match_reference = flag(
            all(matches_reference[method] == "YES" for method in present)
        )

    rows = diff_cells(n, reference, solutions)
    return {
        "reference_present": "YES" if reference_present else "NO",
        "matches_reference": matches_reference,
        "matches_bt": matches_bt,
        "solved_count": len(present),
        "solved_methods": ",".join(present),
        "all_equal": all_equal,
        "all_match_reference": all_match_reference,
        "all_methods_solved": flag(len(present) == len(METHODS)),
        "mismatch_count": len(rows),
        "diffs": rows,
    }


def write_solution_file(filepath, *, size, puzzle_name, run_id, repeat, method,
                        encoding, status, solve_time_s, e2e_time_s, grid,
                        valid, matches_clues, matches_reference, matches_bt,
                        all_equal):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write(f"SIZE {size}\n")
        handle.write(f"PUZZLE {puzzle_name}\n")
        handle.write(f"RUN_ID {run_id}\n")
        handle.write(f"REPEAT {repeat}\n")
        handle.write(f"METHOD {method}\n")
        handle.write(f"ENCODING {encoding}\n")
        handle.write(f"STATUS {status}\n")
        handle.write(f"SOLVE_TIME_SEC {format_time(solve_time_s)}\n")
        handle.write(f"E2E_TIME_SEC {format_time(e2e_time_s)}\n")
        handle.write(f"GRID_HASH {grid_hash(grid)}\n")
        handle.write(f"VALID {flag(valid)}\n")
        handle.write(f"MATCHES_CLUES {flag(matches_clues)}\n")
        handle.write(f"MATCHES_REFERENCE {matches_reference}\n")
        handle.write(f"MATCHES_BT {matches_bt}\n")
        handle.write(f"ALL_EQUAL {all_equal}\n")
        if grid is not None:
            handle.write("SOLUTION\n")
            for row in grid:
                handle.write(" ".join(str(value) for value in row) + "\n")


def write_assignment_file(filepath, *, puzzle_name, run_id, repeat, method,
                          encoding, cnf_path, status, solve_time_s, raw_lines,
                          model_hash_value):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    raw_lines = raw_lines or []
    literal_count = 0
    for line in raw_lines:
        for token in line.split():
            try:
                if int(token) != 0:
                    literal_count += 1
            except ValueError:
                pass

    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write(f"PUZZLE {puzzle_name}\n")
        handle.write(f"RUN_ID {run_id}\n")
        handle.write(f"REPEAT {repeat}\n")
        handle.write(f"METHOD {method}\n")
        handle.write(f"ENCODING {encoding}\n")
        handle.write(f"CNF {cnf_path or ''}\n")
        handle.write(f"STATUS {status}\n")
        handle.write(f"SOLVE_TIME_SEC {format_time(solve_time_s)}\n")
        handle.write(f"MODEL_HASH {model_hash_value or ''}\n")
        handle.write(f"RAW_LITERAL_COUNT {literal_count}\n")
        handle.write("RAW_ASSIGNMENT\n")
        for line in raw_lines:
            handle.write(line + "\n")


def write_reference_file(filepath, *, size, puzzle_name, reference):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write(f"SIZE {size}\n")
        handle.write(f"PUZZLE {puzzle_name}\n")
        handle.write(f"GRID_HASH {grid_hash(reference)}\n")
        handle.write("SOLUTION\n")
        for row in reference:
            handle.write(" ".join(str(value) for value in row) + "\n")


def write_diff_file(filepath, *, reference, solutions, diffs):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    methods = [method for method in METHODS if solutions.get(method) is not None]
    with open(filepath, "w", encoding="utf-8") as handle:
        header = ["CELL", "REFERENCE"] + [method.upper() for method in methods]
        handle.write(" ".join(f"{column:<12}" for column in header) + "\n")
        for r, c, reference_value, values in diffs:
            row = [f"r{r}c{c}", "-" if reference_value is None else str(reference_value)]
            row.extend(str(values.get(method, "-")) for method in methods)
            handle.write(" ".join(f"{value:<12}" for value in row) + "\n")


def write_report(filepath, *, size, puzzle_name, run_id, repeat, reference,
                 solutions, method_rows, comparison):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    lines = [
        "=" * 60,
        "SOLUTION REPORT",
        f"Puzzle:  {puzzle_name}",
        f"Size:    {size}x{size}",
        f"Run id:  {run_id}",
        f"Repeat:  {repeat}",
        f"Reference present: {comparison['reference_present']}",
        "-" * 60,
    ]

    for row in method_rows:
        lines.append(
            f"{row['method']:<8} status={row['status']:<9} "
            f"time={row['solve_time_s']:<10} "
            f"hash={(row['grid_hash'] or '-')[:12]:<12} "
            f"valid={row['valid']:<3} clues={row['matches_clues']:<3} "
            f"reference={row['matches_reference']:<3} bt={row['matches_bt']}"
        )

    lines.extend([
        "-" * 60,
        f"Solved methods:        {comparison['solved_methods'] or '-'}",
        f"All solved:            {comparison['all_methods_solved']}",
        f"All successful equal:  {comparison['all_equal']}",
        f"All match reference:   {comparison['all_match_reference']}",
        f"Different cells:       {comparison['mismatch_count']}",
        "=" * 60,
    ])

    if reference is not None:
        lines.extend(["", "REFERENCE SOLUTION"])
        lines.extend(" ".join(str(value) for value in row) for row in reference)

    for method in METHODS:
        lines.extend(["", f"{method.upper()} SOLUTION"])
        grid = solutions.get(method)
        if grid is None:
            lines.append("(no solution)")
        else:
            lines.extend(" ".join(str(value) for value in row) for row in grid)

    lines.extend(["", "DIFFERENCES"])
    if comparison["diffs"]:
        for r, c, reference_value, values in comparison["diffs"]:
            parts = [f"r{r}c{c}", f"reference={'-' if reference_value is None else reference_value}"]
            parts.extend(f"{method}={values[method]}" for method in values)
            lines.append(" ".join(parts))
    else:
        lines.append("none")

    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def write_consolidated_sat(filepath, *, size, puzzle_name, method, encoding,
                           runs, solution, raw_lines=None,
                           model_hash_value="", valid=None,
                           matches_clues=None, matches_reference="N/A",
                           matches_bt="N/A"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    status = overall_status(method, runs)
    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write(f"SIZE {size}\n")
        handle.write(f"PUZZLE {puzzle_name}\n")
        handle.write(f"METHOD {method}\n")
        handle.write(f"ENCODING {encoding}\n")
        handle.write(f"STATUS {status}\n")
        handle.write(f"GRID_HASH {grid_hash(solution)}\n")
        handle.write(f"MODEL_HASH {model_hash_value or ''}\n")
        handle.write(f"VALID {flag(valid)}\n")
        handle.write(f"MATCHES_CLUES {flag(matches_clues)}\n")
        handle.write(f"MATCHES_REFERENCE {matches_reference}\n")
        handle.write(f"MATCHES_BT {matches_bt}\n")
        handle.write("RUNS\n")
        for run in runs:
            handle.write(
                f"  run {run['repeat']}: "
                f"{canonical_status(method, run.get('status'))} "
                f"{format_time(run.get('solve_time_s'))}\n"
            )
        handle.write("SOLUTION\n")
        if solution is None:
            handle.write("(no solution)\n")
        else:
            for row in solution:
                handle.write(" ".join(str(value) for value in row) + "\n")
        if raw_lines:
            handle.write("RAW_ASSIGNMENT\n")
            for line in raw_lines:
                handle.write(line + "\n")


def write_consolidated_bt(filepath, *, size, puzzle_name, runs, solution,
                          valid=None, matches_clues=None,
                          matches_reference="N/A"):
    if solution is None:
        return False
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    status = overall_status("bt", runs)
    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write(f"SIZE {size}\n")
        handle.write(f"PUZZLE {puzzle_name}\n")
        handle.write("METHOD backtracking\n")
        handle.write("ENCODING backtracking (MRV + degree + FC)\n")
        handle.write(f"STATUS {status}\n")
        handle.write(f"GRID_HASH {grid_hash(solution)}\n")
        handle.write(f"VALID {flag(valid)}\n")
        handle.write(f"MATCHES_CLUES {flag(matches_clues)}\n")
        handle.write(f"MATCHES_REFERENCE {matches_reference}\n")
        handle.write("RUNS\n")
        for run in runs:
            handle.write(
                f"  run {run['repeat']}: "
                f"{canonical_status('bt', run.get('status'))} "
                f"{format_time(run.get('solve_time_s'))}\n"
            )
        handle.write("SOLUTION\n")
        for row in solution:
            handle.write(" ".join(str(value) for value in row) + "\n")
    return True


def write_csv(filepath, fieldnames, rows):
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
