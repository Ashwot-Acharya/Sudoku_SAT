import os
import csv
import importlib.util

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "Output")
CSV_PATH   = os.path.join(OUTPUT_DIR, "benchmark_results.csv")


# ─────────────────────────────────────────────
# Dynamic loader
# ─────────────────────────────────────────────
def _load(name):
    path = os.path.join(SCRIPT_DIR, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────
# Remove ALL previous 9x9 rows
# ─────────────────────────────────────────────
def clean_csv():
    if not os.path.exists(CSV_PATH):
        print("No existing CSV found.")
        return []

    cleaned = []
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["size"] != "9":
                cleaned.append(row)

    print(f"Removed all previous 9x9 rows. Remaining rows: {len(cleaned)}")
    return cleaned


# ─────────────────────────────────────────────
# Generic runner for a 9x9 puzzle set
# ─────────────────────────────────────────────
def run_9x9_group(puzzles, group_label, prefix):
    fetcher = _load("puzzle_fetcher")
    enc     = _load("sudoku_to_cnf")
    bt_mod  = _load("backtracking_solver")
    sat_mod = _load("sat_solver_runner")

    solver = sat_mod.find_solver(None)
    results = []

    for i, grid in enumerate(puzzles, 1):
        name = f"{prefix}_{i:02d}"
        puzzle_path = fetcher.save_puzzle(grid, 9, name)

        print(f"\nRunning {name}")

        row = dict(
            group=group_label,
            size=9,
            puzzle=name,
            cnf_vars=0,
            cnf_clauses=0,
            enc_time=0,
            sat_time=float("nan"),
            bt_time=float("nan"),
            sat_status="skipped",
            bt_status="skipped"
        )

        # Encode
        cnf_path, n_vars, n_clauses, enc_time = enc.convert_file(
            puzzle_path, verbose=False
        )

        row.update(
            cnf_vars=n_vars,
            cnf_clauses=n_clauses,
            enc_time=enc_time
        )

        # SAT
        if solver:
            _, sat_time = sat_mod.solve_cnf(cnf_path, solver, verbose=False)
            row["sat_time"]   = sat_time if sat_time is not None else float("nan")
            row["sat_status"] = "solved"

        # Backtracking
        _, bt_time = bt_mod.solve_puzzle(puzzle_path, verbose=False, timeout=600)

        if bt_time == float("inf"):
            row["bt_time"]   = float("inf")
            row["bt_status"] = "timeout"
        else:
            row["bt_time"]   = bt_time
            row["bt_status"] = "solved"

        results.append(row)

    return results


# ─────────────────────────────────────────────
# Rewrite CSV
# ─────────────────────────────────────────────
def rewrite_csv(rows):
    if not rows:
        print("No rows to write.")
        return

    fieldnames = list(rows[0].keys())

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nUpdated CSV -> {CSV_PATH}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    fetcher = _load("puzzle_fetcher")

    cleaned_rows = clean_csv()

    # 17-clue group
    rows_17 = run_9x9_group(
        puzzles=fetcher.NINE_17_CLUE,
        group_label="17-clue",
        prefix="sudoku_9x9_17clue"
    )

    # 20+ clue group
    rows_20 = run_9x9_group(
        puzzles=fetcher.NINE_HIGHER_CLUE,
        group_label="20plus-clue",
        prefix="sudoku_9x9_20plus"
    )

    rewrite_csv(cleaned_rows + rows_17 + rows_20)
