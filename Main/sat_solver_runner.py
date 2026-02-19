import os
import subprocess
import argparse
import time
import re
import sys

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CNF_DIR     = os.path.join(SCRIPT_DIR, "..", "CNF")
SOL_DIR     = os.path.join(SCRIPT_DIR, "..", "Output", "Sol")
TEMP_DIR    = os.path.join(SCRIPT_DIR, "..", "Temp")
PUZZLES_DIR = os.path.join(SCRIPT_DIR, "..", "Puzzles")

for d in [SOL_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)


# ── find solver ────────────────────────────────────────────────────────────────

def find_solver(preferred=None):
    exe_dir    = os.path.join(SCRIPT_DIR, "executable")
    candidates = []
    if preferred:
        candidates.append(preferred)
    for name in ["satch", "minisat", "picosat", "glucose"]:
        candidates.append(os.path.join(exe_dir, name))
        candidates.append(name)

    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
        try:
            r = subprocess.run(["which", c], capture_output=True, text=True)
            if r.returncode == 0:
                return r.stdout.strip()
        except FileNotFoundError:
            pass
    return None


# ── run solver ─────────────────────────────────────────────────────────────────

def run_solver(solver, cnf_path, timeout=3600):
    solver_name = os.path.basename(solver).lower()
    out_file    = os.path.join(TEMP_DIR, os.path.basename(cnf_path) + ".out")

    if "minisat" in solver_name:
        cmd = [solver, cnf_path, out_file]
    else:
        cmd = [solver, cnf_path]   # satch, picosat

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, [], time.time() - t0
    elapsed = time.time() - t0

    # ── SAT/UNSAT decision ─────────────────────────────────────
    # returncode: satch uses 10=SAT, 20=UNSAT (IPASIR standard)
    if proc.returncode == 10:
        sat = True
    elif proc.returncode == 20:
        sat = False
    else:
        # Fallback text parsing — check UNSATISFIABLE BEFORE SATISFIABLE
        # because "UNSATISFIABLE" contains "SATISFIABLE" as a substring!
        combined = proc.stdout + proc.stderr
        if "UNSATISFIABLE" in combined:
            sat = False
        elif "SATISFIABLE" in combined:
            sat = True
        else:
            print(f"\n  [WARN] returncode={proc.returncode}, no SAT/UNSAT in output")
            print(f"  stdout: {proc.stdout[:300]}")
            sat = False

    if not sat:
        return False, [], elapsed

    # ── parse "v" lines for variable assignment ────────────────
    assignment = []
    for line in proc.stdout.splitlines():
        s = line.strip()
        if s.startswith("v ") or s == "v":
            for tok in s.split()[1:]:
                try:
                    lit = int(tok)
                    if lit != 0 and lit > 0:
                        assignment.append(lit)
                except ValueError:
                    pass

    # minisat writes assignment to file
    if not assignment and os.path.exists(out_file):
        with open(out_file) as f:
            content = f.read()
        for line in content.splitlines():
            if line.strip() in ("SAT", "UNSAT", ""):
                continue
            for tok in line.split():
                try:
                    lit = int(tok)
                    if lit > 0:
                        assignment.append(lit)
                except ValueError:
                    pass

    return True, assignment, elapsed


# ── decode ─────────────────────────────────────────────────────────────────────

def decode_solution(assignment, puzzle_path):
    sys.path.insert(0, SCRIPT_DIR)
    from sudoku_to_cnf import read_puzzle, encode

    n, puzzle    = read_puzzle(puzzle_path)
    _, _, var_map, _ = encode(n, puzzle)
    inv_map      = {idx: triple for triple, idx in var_map.items()}
    true_set     = set(assignment)

    grid = [row[:] for row in puzzle]
    for var_idx in true_set:
        if var_idx in inv_map:
            r, c, v = inv_map[var_idx]
            grid[r - 1][c - 1] = v
    return grid, n


# ── save ───────────────────────────────────────────────────────────────────────

def save_solution(grid, n, basename, sat_time, assignment):
    out = os.path.join(SOL_DIR, basename + "_SAT_solved.txt")
    with open(out, "w+") as f:
        f.write(f"SIZE {n}\nSOLVE_TIME_SEC {sat_time:.4f}\n")
        f.write("METHOD SAT\nSTATUS SOLVED\nSOLUTION\n")
        for row in grid:
            f.write(" ".join(str(v) for v in row) + "\n")
        for x in assignment: 
            f.write(str(x))
    return out


def find_puzzle_for_cnf(cnf_path):
    basename = os.path.splitext(os.path.basename(cnf_path))[0]
    p = os.path.join(PUZZLES_DIR, basename + ".txt")
    if os.path.exists(p):
        return p
    for f in os.listdir(PUZZLES_DIR):
        if os.path.splitext(f)[0] == basename:
            return os.path.join(PUZZLES_DIR, f)
    return None


# ── public API ─────────────────────────────────────────────────────────────────

def solve_cnf(cnf_path, solver, verbose=True, timeout=3600):
    basename = os.path.splitext(os.path.basename(cnf_path))[0]
    if verbose:
        print(f"  SAT {os.path.basename(cnf_path)} ...", end=" ", flush=True)

    sat, assignment, elapsed = run_solver(solver, cnf_path, timeout=timeout)
    print(assignment)
    if not sat:
        if verbose:
            print(f"✗ UNSAT/ERROR ({elapsed:.3f}s)")
        open(os.path.join(SOL_DIR, basename + "_SAT_UNSAT.txt"), "w").write(
            f"STATUS UNSATISFIABLE\nTIME {elapsed:.4f}\n")
        return None, elapsed

    puzzle_path = find_puzzle_for_cnf(cnf_path)
    if not puzzle_path:
        if verbose: print(f"✗ puzzle file not found")
        return None, elapsed

    try:
        grid, n  = decode_solution(assignment, puzzle_path)
        sol_path = save_solution(grid, n, basename, elapsed, assignment) 
        if verbose:
            print(f"✓ {elapsed:.3f}s → {os.path.basename(sol_path)}")
        return sol_path, elapsed
    except Exception as e:
        if verbose: print(f"✗ decode error: {e}")
        return None, elapsed


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cnf")
    p.add_argument("--solver")
    p.add_argument("--timeout", type=int, default=3600)
    args = p.parse_args()

    solver = find_solver(args.solver)
    if not solver:
        print("ERROR: No SAT solver found. Place satch in Main/executable/")
        return
    print(f"Solver: {solver}\n")

    files = [args.cnf] if args.cnf else sorted(
        os.path.join(CNF_DIR, f) for f in os.listdir(CNF_DIR) if f.endswith(".cnf")
    )
    for cnf in files:
        solve_cnf(cnf, solver, timeout=args.timeout)


if __name__ == "__main__":
    main()