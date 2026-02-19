"""
backtracking_solver.py
Optimized backtracking solver with MRV + degree heuristic + forward checking.
Supports a timeout (default 300 = 5 ). If timeout is hit, returns
TIMEOUT_SENTINEL so the benchmark can mark it as ">10min".
"""

import os
import math
import time
import argparse
import signal

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PUZZLES_DIR = os.path.join(SCRIPT_DIR, "..", "Puzzles")
SOL_DIR     = os.path.join(SCRIPT_DIR, "..", "Output", "Sol")
os.makedirs(SOL_DIR, exist_ok=True)

TIMEOUT_SECONDS  = 5 * 60
TIMEOUT_SENTINEL = float("inf")   # used in benchmark to mean ">5 min"


# ───────────────────────────────────────────────────────────────
# Timeout (SIGALRM on Unix; Windows uses wall-clock fallback)
# ───────────────────────────────────────────────────────────────

class _TimeoutError(Exception):
    pass

def _alarm_handler(signum, frame):
    raise _TimeoutError()


# ───────────────────────────────────────────────────────────────
# I/O
# ───────────────────────────────────────────────────────────────

def read_puzzle(filepath):
    with open(filepath) as f:
        lines = [l.strip() for l in f if l.strip()]
    n = int(lines[0].split()[1])
    puzzle, reading = [], False
    for line in lines[1:]:
        if line == "PUZZLE":   reading = True;  continue
        if line == "SOLUTION": break
        if reading:            puzzle.append(list(map(int, line.split())))
    return n, puzzle


def save_solution(grid, n, basename, elapsed, timed_out=False):
    out_path = os.path.join(SOL_DIR, basename + "_BT_solved.txt")
    with open(out_path, "w") as f:
        f.write(f"SIZE {n}\n")
        f.write("SOLVE_TIME_SEC >300  (timeout at 5 min)\n" if timed_out
                else f"SOLVE_TIME_SEC {elapsed:.6f}\n")
        f.write("METHOD Optimized_Backtracking\n")
        f.write("STATUS TIMEOUT\n" if timed_out else "STATUS SOLVED\n")
        if not timed_out:
            f.write("SOLUTION\n")
            for row in grid:
                f.write(" ".join(str(v) for v in row) + "\n")
    return out_path


# ───────────────────────────────────────────────────────────────
# Precompute peers
# ───────────────────────────────────────────────────────────────

def precompute_peers(n):
    box, peers = int(math.sqrt(n)), {}
    for r in range(n):
        for c in range(n):
            p = set()
            for cc in range(n):
                if cc != c: p.add((r, cc))
            for rr in range(n):
                if rr != r: p.add((rr, c))
            br, bc = (r // box) * box, (c // box) * box
            for rr in range(br, br + box):
                for cc in range(bc, bc + box):
                    if (rr, cc) != (r, c): p.add((rr, cc))
            peers[(r, c)] = p
    return peers


# ───────────────────────────────────────────────────────────────
# Domain construction
# ───────────────────────────────────────────────────────────────

def build_domains(grid, n, peers):
    domains = {}
    for r in range(n):
        for c in range(n):
            if grid[r][c] == 0:
                used   = {grid[rr][cc] for (rr, cc) in peers[(r, c)] if grid[rr][cc] != 0}
                domain = set(range(1, n + 1)) - used
                if not domain:
                    return None
                domains[(r, c)] = domain
    return domains


# ───────────────────────────────────────────────────────────────
# Solver
# ───────────────────────────────────────────────────────────────

def select_cell(domains, peers):
    return min(domains, key=lambda k: (len(domains[k]), -len(peers[k])))


def solve_recursive(grid, domains, peers):
    if not domains:
        return True

    cell = select_cell(domains, peers)
    r, c = cell

    for val in list(domains[cell]):
        grid[r][c] = val
        removed, fail = [], False

        for p in peers[cell]:
            if p in domains and val in domains[p]:
                domains[p].remove(val)
                removed.append(p)
                if not domains[p]:
                    fail = True
                    break

        if not fail:
            saved = domains.pop(cell)
            if solve_recursive(grid, domains, peers):
                return True
            domains[cell] = saved

        for p in removed:
            domains[p].add(val)
        grid[r][c] = 0

    return False


# ───────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────

def solve_puzzle(filepath, verbose=True, timeout=TIMEOUT_SECONDS):
    """
    Returns (sol_path | None, elapsed_seconds).
    elapsed == TIMEOUT_SENTINEL (inf) when the-min wall is hit.
    """
    basename  = os.path.splitext(os.path.basename(filepath))[0]
    n, puzzle = read_puzzle(filepath)
    grid      = [row[:] for row in puzzle]

    if verbose:
        print(f"  Solving {n}x{n} backtracking ...", end=" ", flush=True)

    peers   = precompute_peers(n)
    domains = build_domains(grid, n, peers)

    if domains is None:
        if verbose: print("✗ invalid puzzle (domain wipeout at start)")
        return None, 0.0

    t0, timed_out = time.time(), False

    use_signal = hasattr(signal, "SIGALRM")
    if use_signal:
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(int(timeout))

    try:
        success = solve_recursive(grid, domains, peers)
    except _TimeoutError:
        timed_out, success = True, False
    finally:
        if use_signal:
            signal.alarm(0)

    elapsed = time.time() - t0

    if not timed_out and elapsed >= timeout:   # Windows fallback
        timed_out, success = True, False

    if timed_out:
        if verbose:
            print(f"⏱  TIMEOUT (>{timeout//60} min limit)")
        save_solution(grid, n, basename, elapsed, timed_out=True)
        return None, TIMEOUT_SENTINEL

    if not success:
        if verbose: print(f"✗ UNSOLVABLE ({elapsed:.3f}s)")
        err = os.path.join(SOL_DIR, basename + "_BT_UNSOLVABLE.txt")
        open(err, "w").write(f"STATUS UNSOLVABLE\nTIME {elapsed:.6f}\n")
        return None, elapsed

    sol_path = save_solution(grid, n, basename, elapsed)
    if verbose:
        print(f"✓ {elapsed:.3f}s → {os.path.basename(sol_path)}")
    return sol_path, elapsed


# ───────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("puzzles", nargs="*")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS)
    args = parser.parse_args()

    files = args.puzzles or sorted(
        os.path.join(PUZZLES_DIR, f)
        for f in os.listdir(PUZZLES_DIR) if f.endswith(".txt")
    )
    if not files:
        print("No puzzle files found."); return

    print(f"Solving {len(files)} puzzle(s)...\n")
    for f in files:
        solve_puzzle(f, timeout=args.timeout)
    print(f"\n✓ Solutions saved to: {os.path.abspath(SOL_DIR)}")


if __name__ == "__main__":
    main()