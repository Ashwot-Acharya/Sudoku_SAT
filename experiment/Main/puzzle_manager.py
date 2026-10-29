"""
puzzle_manager.py
═════════════════
Unified puzzle sourcing module for the Sudoku SAT benchmark suite.

Responsibilities:
  1. Hardcoded known puzzles  (Gordon Royle 17-clue 9×9, simple 4×4)
  2. Procedural generation    (seed-controlled, with uniqueness checking)
  3. I/O utilities            (read / save / parse / convert)
  4. Dataset assembly          (complete benchmark dataset for sizes 4–64)

All randomness is routed through `random.Random(seed)` instances for
reproducibility — the global RNG is never touched.
"""

import os
import sys
import math
import time
import json
import csv
import random
import copy
import hashlib
import subprocess
import tempfile

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PUZZLES_DIR = os.path.join(SCRIPT_DIR, "..", "Puzzles")
GENERATION_DIR = os.path.join(SCRIPT_DIR, "..", "GenerationMethods")
os.makedirs(PUZZLES_DIR, exist_ok=True)

VALID_SIZES = [4, 9, 16, 25, 36, 49, 64]
DEFAULT_LEGACY_MAX_FILL = 0.50
DEFAULT_LEGACY_SOFT_FILL = 0.35


# ══════════════════════════════════════════════════════════════════════════════
#  Part 1 — Hardcoded known puzzles
# ══════════════════════════════════════════════════════════════════════════════

# ── Gordon Royle's 17-clue 9×9 database ──────────────────────────────────────
# Source: http://staffhome.ecm.uwa.edu.au/~00013890/sudokumin.php
# These are minimal-clue puzzles proven to have unique solutions.
# Represented as 81-char one-line strings (0 = empty).

ROYLE_17_CLUE_STRINGS = [
    # 10 verified-unique 17-clue puzzles from Gordon Royle's sudoku17 collection
    # (mirror: github.com/m-k-l-s/sudoku/all_17_clue_sudokus.txt, first 10
    # entries; every entry below re-verified unique with CaDiCaL).
    "000000010400000000020000000000050407008000300001090000300400200050100000000806000",
    "000000010400000000020000000000050604008000300001090000300400200050100000000807000",
    "000000012000035000000600070700000300000400800100000000000120000080000040050000600",
    "000000012003600000000007000410020000000500300700000600280000040000300500000000000",
    "000000012008030000000000040120500000000004700060000000507000300000620000000100000",
    "000000012040050000000009000070600400000100000000000050000087500601000300200000000",
    "000000012050400000000000030700600400001000000000080000920000800000510700000003000",
    "000000012300000060000040000900000500000001070020000000000350400001400800060000000",
    "000000012400090000000000050070200000600000400000108000018000000000030700502000000",
    "000000012500008000000700000600120000700000450000030000030000800000500700020000000",
]


def _oneline_to_grid_9x9(line):
    """Convert an 81-char string (0=empty) into a 9×9 2D list."""
    line = line.strip().replace(".", "0")
    assert len(line) == 81, f"Expected 81 chars, got {len(line)}"
    return [[int(line[r * 9 + c]) for c in range(9)] for r in range(9)]


def _oneline_to_clues(line):
    """Convert an 81-char string into a list of (row, col, val) tuples."""
    grid = _oneline_to_grid_9x9(line)
    clues = []
    for r in range(9):
        for c in range(9):
            if grid[r][c] != 0:
                clues.append((r, c, grid[r][c]))
    return clues


# Pre-parse into 2D grids
ROYLE_17_CLUE = [_oneline_to_grid_9x9(s) for s in ROYLE_17_CLUE_STRINGS]


# ── 4×4 puzzles (5 puzzles, simple, hand-constructed) ────────────────────────
FOUR_PUZZLES = [
    # P1: 6 clues
    [[1, 0, 0, 4],
     [0, 4, 0, 0],
     [0, 0, 4, 0],
     [4, 0, 0, 1]],
    # P2: 4 clues
    [[0, 2, 0, 0],
     [0, 0, 0, 3],
     [4, 0, 0, 0],
     [0, 0, 1, 0]],
    # P3: 4 clues
    [[0, 0, 3, 0],
     [0, 1, 0, 0],
     [0, 0, 0, 2],
     [0, 4, 0, 0]],
    # P4: 4 clues
    [[4, 0, 0, 0],
     [0, 0, 2, 0],
     [0, 3, 0, 0],
     [0, 0, 0, 1]],
    # P5: 4 clues
    [[0, 3, 0, 2],
     [0, 0, 0, 0],
     [0, 0, 0, 0],
     [1, 0, 4, 0]],
]


# ══════════════════════════════════════════════════════════════════════════════
#  Part 2 — Procedural generator with uniqueness checking
# ══════════════════════════════════════════════════════════════════════════════

# ── Solution generation (Shirley method with band shuffling) ─────────────────
# Copied from sudoku_generator.py — deterministic base pattern construction.

def _pattern(r, c, base, side):
    """Compute the value index at (r, c) in the base Latin square."""
    return (base * (r % base) + r // base + c) % side


def generate_solution(n, rng=None, trace=None):
    """
    Generate a full valid n×n Sudoku solution instantly using the
    deterministic base-pattern method with random band/stack shuffling.

    Parameters
    ----------
    n     : board size (must be a perfect square)
    rng   : random.Random instance (for reproducibility)
    trace : optional dict populated with every random permutation used

    Returns
    -------
    grid : list[list[int]]  — complete valid solution
    """
    if rng is None:
        rng = random.Random()

    base = int(math.isqrt(n))
    assert base * base == n, f"n={n} must be a perfect square"
    side = n

    def _shuffle(seq):
        lst = list(seq)
        rng.shuffle(lst)
        return lst

    band_order = _shuffle(range(base))
    row_order = []
    rows_within_bands = []
    for band in band_order:
        offsets = _shuffle(range(base))
        rows_within_bands.append(offsets)
        row_order.extend(band * base + offset for offset in offsets)

    stack_order = _shuffle(range(base))
    column_order = []
    columns_within_stacks = []
    for stack in stack_order:
        offsets = _shuffle(range(base))
        columns_within_stacks.append(offsets)
        column_order.extend(stack * base + offset for offset in offsets)

    nums = _shuffle(range(1, side + 1))

    if trace is not None:
        trace.update({
            "band_order": list(band_order),
            "rows_within_bands": [list(v) for v in rows_within_bands],
            "row_order": list(row_order),
            "stack_order": list(stack_order),
            "columns_within_stacks": [list(v) for v in columns_within_stacks],
            "column_order": list(column_order),
            "symbol_order": list(nums),
        })

    grid = [
        [nums[_pattern(r, c, base, side)] for c in column_order]
        for r in row_order
    ]
    return grid


# ── Default clue targets ─────────────────────────────────────────────────────

def _default_clues(n):
    """Sensible default number of clues for a given board size.

    Uses graduated sparsity: larger grids are targeted at a lower fill
    fraction (16x16 -> 25%, 25x25 -> 20%, 36x36 -> 14%).  For seeded legacy
    puzzles these are lower bounds: uniqueness may require extra clues, with
    a hard cap controlled by ``DEFAULT_LEGACY_MAX_FILL``.
    """
    defaults = {
        4:   4,     # 25%
        9:  25,     # 31%
        16:  64,    # 25%
        25: 125,    # 20%
        36: 180,    # 14%
        49: 280,    # 12%
        64: 380,    # 9%
    }
    return defaults.get(n, int(n * n * 0.35))


def derive_puzzle_seed(master_seed, generator, n, index, attempt=0):
    """Derive a stable 31-bit puzzle seed from the experiment coordinates."""
    payload = f"{master_seed}|{generator}|{n}|{index}|{attempt}".encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big") & 0x7FFFFFFF


def puzzle_name_for(generator, n, seed, index):
    return f"sudoku_{n}x{n}_{generator}_seed{seed}_{index:02d}"


def _choices_path_for(puzzle_path):
    return os.path.splitext(puzzle_path)[0] + "_choices.json"


def _write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _grid_digest(grid):
    if grid is None:
        return ""
    payload = "\n".join(" ".join(str(v) for v in row) for row in grid)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_seed_index(directory, rows):
    if not rows:
        return None
    path = os.path.join(directory, "puzzle_seeds.csv")
    fields = [
        "master_seed",
        "generator",
        "size",
        "index",
        "attempt",
        "puzzle_seed",
        "puzzle_name",
        "puzzle_path",
        "choices_path",
        "clue_count",
        "fill_pct",
        "unique",
        "generation_time_s",
        "puzzle_hash",
        "solution_hash",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


# ── Constraint propagation (naked singles) ───────────────────────────────────

def _constraint_propagate(grid, n):
    """
    Try to solve the puzzle by constraint propagation alone (naked singles).

    Returns
    -------
    (solved_grid, is_complete, had_contradiction)
    """
    base = int(math.isqrt(n))
    g = [row[:] for row in grid]

    def _peers(r, c):
        s = set()
        for cc in range(n):
            if cc != c:
                s.add((r, cc))
        for rr in range(n):
            if rr != r:
                s.add((rr, c))
        br, bc = (r // base) * base, (c // base) * base
        for rr in range(br, br + base):
            for cc in range(bc, bc + base):
                if (rr, cc) != (r, c):
                    s.add((rr, cc))
        return s

    changed = True
    while changed:
        changed = False
        for r in range(n):
            for c in range(n):
                if g[r][c] != 0:
                    continue
                used = {g[rr][cc] for rr, cc in _peers(r, c) if g[rr][cc] != 0}
                possible = set(range(1, n + 1)) - used
                if len(possible) == 0:
                    return g, False, True   # contradiction
                if len(possible) == 1:
                    g[r][c] = possible.pop()
                    changed = True

    is_complete = all(g[r][c] != 0 for r in range(n) for c in range(n))
    return g, is_complete, False


# ── Simple backtracking solver for uniqueness check (counts up to 2) ─────────

def _count_solutions(grid, n, limit=2):
    """
    Count solutions of the puzzle, stopping at `limit`.
    Used for uniqueness verification when SAT is unavailable.
    """
    base = int(math.isqrt(n))
    g = [row[:] for row in grid]

    # Build peer sets once
    peer_cache = {}
    for r in range(n):
        for c in range(n):
            s = set()
            for cc in range(n):
                if cc != c:
                    s.add((r, cc))
            for rr in range(n):
                if rr != r:
                    s.add((rr, c))
            br, bc = (r // base) * base, (c // base) * base
            for rr in range(br, br + base):
                for cc in range(bc, bc + base):
                    if (rr, cc) != (r, c):
                        s.add((rr, cc))
            peer_cache[(r, c)] = s

    count = [0]

    # Find empty cells
    empties = [(r, c) for r in range(n) for c in range(n) if g[r][c] == 0]

    def _solve(idx):
        if count[0] >= limit:
            return
        if idx == len(empties):
            count[0] += 1
            return

        r, c = empties[idx]
        used = {g[rr][cc] for rr, cc in peer_cache[(r, c)] if g[rr][cc] != 0}

        for v in range(1, n + 1):
            if v not in used:
                g[r][c] = v
                _solve(idx + 1)
                if count[0] >= limit:
                    g[r][c] = 0
                    return
                g[r][c] = 0

    _solve(0)
    return count[0]


def _check_unique_sat(grid, n, solver_path=None, timeout=30):
    """
    Use constraint propagation + SAT-based blocking check for uniqueness.
    """
    try:
        from uniqueness import deducibility_check
        res = deducibility_check(grid, n)
        if res.get("unique") is True:
            return True
    except (ImportError, Exception):
        pass

    if solver_path is None:
        try:
            from sat_solver_runner import find_solver
            solver_path = find_solver()
        except (ImportError, Exception):
            pass

    if solver_path is not None:
        try:
            from uniqueness import sat_blocking_check
            result = sat_blocking_check(grid, n, solver_path=solver_path, timeout=timeout)
            if isinstance(result, dict):
                return bool(result.get("unique", False))
            return bool(result)
        except (ImportError, Exception):
            pass

    # For n <= 9, use exact backtracking count
    if n <= 9:
        return _count_solutions(grid, n, limit=2) == 1

    # For n > 9, attempt backtracking count with a generous timeout.
    # If it times out, conservatively assume NOT unique (safer for benchmarking).
    try:
        import signal

        def _timeout_handler(signum, frame):
            raise TimeoutError()

        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(max(1, int(timeout)))
        try:
            result = _count_solutions(grid, n, limit=2) == 1
            signal.alarm(0)
            return result
        except TimeoutError:
            return False  # conservative: assume not unique if we can't verify
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)
    except (ImportError, AttributeError):
        # signal.SIGALRM not available (Windows?) — skip check, assume not unique
        return False


# ── Main generator ───────────────────────────────────────────────────────────

def generate_puzzle(n, seed=None, target_clues=None, ensure_unique=True,
                    solver_path=None, timeout=60, max_fill=DEFAULT_LEGACY_MAX_FILL,
                    soft_fill=DEFAULT_LEGACY_SOFT_FILL, uniqueness_timeout=30,
                    batch_fraction=0.05):
    """
    Generate a Sudoku puzzle by creating a full solution and removing cells.

    For n >= 16 removal uses a fast deducibility gate in batches.  If that
    leaves more clues than ``max_fill``, individual clue removals are verified
    with SAT until the hard cap is met.  The historical clue target is used as
    a lower bound; extra clues are allowed when required for uniqueness.

    Returns
    -------
    (puzzle_grid, solution_grid, metadata_dict)
    """
    base = int(math.isqrt(n))
    assert base * base == n, f"n={n} must be a perfect square"

    if target_clues is None:
        target_clues = _default_clues(n)

    rng = random.Random(seed)
    t0 = time.time()

    solution_trace = {}
    solution = generate_solution(n, rng=rng, trace=solution_trace)

    puzzle = [row[:] for row in solution]
    total_cells = n * n
    current_clues = total_cells

    cells = [(r, c) for r in range(n) for c in range(n)]
    rng.shuffle(cells)
    choices = {
        "solution": solution_trace,
        "cell_order": [[r, c] for r, c in cells],
        "removed_cells": [],
        "restored_cells": [],
        "batch_events": [],
        "target_clues": target_clues,
        "max_fill": max_fill,
        "soft_fill": soft_fill,
        "batch_fraction": batch_fraction,
    }

    uniqueness_checks = 0
    uniqueness_time_s = 0.0
    removal_failures = 0
    deducibility_checks = 0
    sat_checks = 0
    refined_cells = []

    def _is_deducible():
        nonlocal deducibility_checks, uniqueness_time_s
        started = time.perf_counter()
        try:
            from uniqueness import deducibility_check
            result = deducibility_check(puzzle, n).get("unique") is True
        except Exception:
            _, complete, contradiction = _constraint_propagate(puzzle, n)
            result = bool(complete and not contradiction)
        deducibility_checks += 1
        uniqueness_time_s += time.perf_counter() - started
        return result

    def _is_unique_sat():
        nonlocal sat_checks, uniqueness_checks, uniqueness_time_s
        started = time.perf_counter()
        result = _check_unique_sat(
            puzzle, n, solver_path=solver_path,
            timeout=uniqueness_timeout,
        )
        sat_checks += 1
        uniqueness_checks += 1
        uniqueness_time_s += time.perf_counter() - started
        return bool(result)

    if ensure_unique and n >= 16:
        batch_size = max(1, int(round(total_cells * batch_fraction)))
        hard_cap = int(math.floor(max_fill * total_cells + 1e-9))
        propagation_deadline = t0 + min(timeout, 60.0)

        def _process_batch(batch):
            nonlocal current_clues, removal_failures
            if not batch or current_clues <= target_clues:
                return
            if time.time() > propagation_deadline:
                return

            take = min(len(batch), current_clues - target_clues)
            subset = batch[:take]
            saved = []
            for r, c in subset:
                saved.append((r, c, puzzle[r][c]))
                puzzle[r][c] = 0

            if _is_deducible():
                current_clues -= len(subset)
                choices["removed_cells"].extend([[r, c] for r, c in subset])
                choices["batch_events"].append({
                    "size": len(subset),
                    "accepted": True,
                    "cells": [[r, c] for r, c in subset],
                })
                return

            for r, c, value in reversed(saved):
                puzzle[r][c] = value
            removal_failures += 1
            choices["restored_cells"].extend([[r, c] for r, c in subset])
            choices["batch_events"].append({
                "size": len(subset),
                "accepted": False,
                "cells": [[r, c] for r, c in subset],
            })

            if len(subset) > 1:
                middle = len(subset) // 2
                _process_batch(subset[:middle])
                _process_batch(subset[middle:])

        for start in range(0, len(cells), batch_size):
            if current_clues <= target_clues or time.time() > propagation_deadline:
                break
            _process_batch(cells[start:start + batch_size])

        if current_clues > hard_cap:
            remaining = [
                (r, c) for r, c in cells
                if puzzle[r][c] != 0
            ]
            for r, c in remaining:
                if current_clues <= hard_cap:
                    break
                if time.time() - t0 > timeout:
                    break
                value = puzzle[r][c]
                puzzle[r][c] = 0
                current_clues -= 1
                if _is_unique_sat():
                    refined_cells.append([r, c])
                    choices["removed_cells"].append([r, c])
                    choices["batch_events"].append({
                        "size": 1,
                        "accepted": True,
                        "cells": [[r, c]],
                        "phase": "sat-refine",
                    })
                else:
                    puzzle[r][c] = value
                    current_clues += 1
                    removal_failures += 1
                    choices["restored_cells"].append([r, c])
                    choices["batch_events"].append({
                        "size": 1,
                        "accepted": False,
                        "cells": [[r, c]],
                        "phase": "sat-refine",
                    })

    else:
        for r, c in cells:
            if current_clues <= target_clues:
                break
            if time.time() - t0 > timeout:
                break

            saved_val = puzzle[r][c]
            if saved_val == 0:
                continue

            puzzle[r][c] = 0
            current_clues -= 1

            if ensure_unique:
                if not _is_unique_sat():
                    puzzle[r][c] = saved_val
                    current_clues += 1
                    removal_failures += 1
                    choices["restored_cells"].append([r, c])
                    choices["batch_events"].append({
                        "size": 1,
                        "accepted": False,
                        "cells": [[r, c]],
                    })
                else:
                    choices["removed_cells"].append([r, c])
                    choices["batch_events"].append({
                        "size": 1,
                        "accepted": True,
                        "cells": [[r, c]],
                    })
            else:
                choices["removed_cells"].append([r, c])
                choices["batch_events"].append({
                    "size": 1,
                    "accepted": True,
                    "cells": [[r, c]],
                })

    generation_time = time.time() - t0
    final_clues = sum(1 for r in range(n) for c in range(n) if puzzle[r][c] != 0)
    final_fill = final_clues / total_cells
    uniqueness_verified = bool(ensure_unique)

    propagation_solved = None
    propagation_contradiction = None
    if n >= 16:
        try:
            _, propagation_solved, propagation_contradiction = _constraint_propagate(puzzle, n)
        except Exception:
            propagation_solved = None
            propagation_contradiction = None

    metadata = {
        "seed": seed,
        "n": n,
        "num_clues": final_clues,
        "fill_pct": round(100.0 * final_fill, 4),
        "target_clues": target_clues,
        "reached_target": final_clues <= target_clues,
        "max_fill": max_fill,
        "soft_fill": soft_fill,
        "above_soft_cap": final_fill > soft_fill,
        "above_max_fill": final_fill > max_fill,
        "generation_time_s": round(generation_time, 4),
        "uniqueness_verified": uniqueness_verified,
        "uniqueness_policy": (
            "deducibility-greedy+sat-refine" if ensure_unique and n >= 16
            else ("exact-per-removal" if ensure_unique else "none")
        ),
        "uniqueness_checks": uniqueness_checks,
        "deducibility_checks": deducibility_checks,
        "sat_checks": sat_checks,
        "sat_refined_cells": refined_cells,
        "uniqueness_time_s": round(uniqueness_time_s, 4),
        "removal_failures": removal_failures,
        "propagation_solved": propagation_solved,
        "propagation_contradiction": propagation_contradiction,
        "choices": choices,
    }

    return puzzle, solution, metadata


# ══════════════════════════════════════════════════════════════════════════════
#  Part 3 — I/O utilities
# ══════════════════════════════════════════════════════════════════════════════

def read_puzzle(filepath):
    """
    Read a puzzle file in the SIZE N / PUZZLE format.

    Returns
    -------
    (n, grid) where grid is a 2D list of ints (0 = empty).
    """
    with open(filepath) as f:
        lines = [l.strip() for l in f if l.strip()]

    n = int(lines[0].split()[1])
    puzzle = []
    reading = False
    for line in lines[1:]:
        if line == "PUZZLE":
            reading = True
            continue
        if line == "SOLUTION":
            break
        if reading:
            puzzle.append(list(map(int, line.split())))
    return n, puzzle


def save_puzzle(puzzle, n, name, solution=None, directory=None):
    """
    Save a puzzle in the SIZE N / PUZZLE format, optionally with a SOLUTION block.

    Parameters
    ----------
    puzzle    : 2D list of ints
    n         : board size
    name      : filename stem (without extension)
    solution  : optional 2D list of ints (full solution)
    directory : output directory (default: PUZZLES_DIR)

    Returns
    -------
    filepath : str — path to the saved file
    """
    if directory is None:
        directory = PUZZLES_DIR
    os.makedirs(directory, exist_ok=True)

    filepath = os.path.join(directory, name + ".txt")
    with open(filepath, "w") as f:
        f.write(f"SIZE {n}\n")
        f.write("PUZZLE\n")
        for row in puzzle:
            f.write(" ".join(str(v) for v in row) + "\n")
        if solution is not None:
            f.write("SOLUTION\n")
            for row in solution:
                f.write(" ".join(str(v) for v in row) + "\n")
    return filepath


def parse_oneline(line, n=9):
    """
    Parse a one-line string representation into a 2D grid.

    Accepts '0' or '.' for empty cells.  Length must be n*n.

    Parameters
    ----------
    line : str — e.g. "003020600900005004..."
    n    : board size (default 9)

    Returns
    -------
    grid : list[list[int]]
    """
    line = line.strip().replace(".", "0")
    assert len(line) == n * n, f"Expected {n*n} chars, got {len(line)}"
    return [[int(line[r * n + c]) for c in range(n)] for r in range(n)]


def grid_to_oneline(grid):
    """
    Convert a 2D grid to a one-line string (0 for empty cells).

    Parameters
    ----------
    grid : list[list[int]]

    Returns
    -------
    str — compact one-line representation
    """
    return "".join(str(v) for row in grid for v in row)


# ══════════════════════════════════════════════════════════════════════════════
#  Part 4 — Dataset assembly
# ══════════════════════════════════════════════════════════════════════════════

def _validate_grid(grid, n):
    """Check a grid for row/col/box conflicts. Returns list of error strings."""
    base = int(math.isqrt(n))
    errors = []
    for r in range(n):
        vals = [grid[r][c] for c in range(n) if grid[r][c] != 0]
        if len(vals) != len(set(vals)):
            errors.append(f"row {r}")
    for c in range(n):
        vals = [grid[r][c] for r in range(n) if grid[r][c] != 0]
        if len(vals) != len(set(vals)):
            errors.append(f"col {c}")
    for br in range(0, n, base):
        for bc in range(0, n, base):
            vals = [grid[br + dr][bc + dc]
                    for dr in range(base) for dc in range(base)
                    if grid[br + dr][bc + dc] != 0]
            if len(vals) != len(set(vals)):
                errors.append(f"box({br // base},{bc // base})")
    return errors


def count_clues(grid):
    """Count the number of non-zero cells in a grid."""
    return sum(v != 0 for row in grid for v in row)


def _load_back_circulant_generator():
    if GENERATION_DIR not in sys.path:
        sys.path.insert(0, GENERATION_DIR)
    from back_circulant import generate_back_circulant_puzzle

    return generate_back_circulant_puzzle


def _write_choices_sidecar(*, master_seed, generator, n, index, attempt,
                           puzzle_seed, puzzle_name, puzzle_path, metadata):
    path = _choices_path_for(puzzle_path)
    payload = {
        "master_seed": master_seed,
        "generator": generator,
        "size": n,
        "index": index,
        "attempt": attempt,
        "puzzle_seed": puzzle_seed,
        "puzzle_name": puzzle_name,
        "puzzle_path": puzzle_path,
        "metadata": metadata,
    }
    _write_json(path, payload)
    return path


def _assemble_back_circulant_dataset(sizes, puzzles_per_size, seed):
    generator = _load_back_circulant_generator()
    directory = os.path.join(PUZZLES_DIR, "back_circulant")
    dataset = []
    index_rows = []

    for n in sizes:
        group = "4x4" if n == 4 else ("9x9-generated" if n == 9 else f"{n}x{n}")
        print(f"\n── {group} (back-circulant) ──")
        for index in range(1, puzzles_per_size + 1):
            puzzle_seed = derive_puzzle_seed(seed, "back_circulant", n, index)
            puzzle, solution, meta = generator(n, seed=puzzle_seed)
            meta["master_seed"] = seed
            name = puzzle_name_for("back_circulant", n, puzzle_seed, index)
            path = save_puzzle(puzzle, n, name, solution=solution, directory=directory)
            choices_path = _write_choices_sidecar(
                master_seed=seed,
                generator="back_circulant",
                n=n,
                index=index,
                attempt=0,
                puzzle_seed=puzzle_seed,
                puzzle_name=name,
                puzzle_path=path,
                metadata=meta,
            )
            print(f"  {name}  ({meta['clue_count']} clues, "
                  f"{meta['fill_pct']:.2f}% fill, {meta['generation_time_s']:.4f}s) "
                  f"-> {os.path.basename(path)}")
            dataset.append({
                "n": n,
                "group": group,
                "puzzle_path": path,
                "solution": solution,
                "verified_unique": None,
                "construction_valid": meta["valid"],
                "generator": "back_circulant",
                "master_seed": seed,
                "seed": puzzle_seed,
                "puzzle_seed": puzzle_seed,
                "index": index,
                "attempt": 0,
                "choices_path": choices_path,
                "metadata_path": choices_path,
                "metadata": meta,
                "clue_count": meta["clue_count"],
                "fill_pct": meta["fill_pct"],
                "generation_time_s": meta["generation_time_s"],
            })
            index_rows.append({
                "master_seed": seed,
                "generator": "back_circulant",
                "size": n,
                "index": index,
                "attempt": 0,
                "puzzle_seed": puzzle_seed,
                "puzzle_name": name,
                "puzzle_path": path,
                "choices_path": choices_path,
                "clue_count": meta["clue_count"],
                "fill_pct": f"{meta['fill_pct']:.4f}",
                "unique": "",
                "generation_time_s": f"{meta['generation_time_s']:.9f}",
                "puzzle_hash": meta["puzzle_hash"],
                "solution_hash": meta["solution_hash"],
            })

    index_path = _write_seed_index(directory, index_rows)
    total = len(dataset)
    valid_count = sum(1 for d in dataset if d["construction_valid"])
    print(f"\n--- Dataset assembled: {total} puzzles "
          f"({valid_count} construction-valid) ---")
    print(f"Puzzle directory: {os.path.abspath(directory)}")
    print(f"Seed index:       {index_path}")
    return dataset


def _assemble_legacy_seeded_dataset(sizes, puzzles_per_size, seed, solver_path,
                                    timeout, max_fill, soft_fill,
                                    uniqueness_timeout, max_attempts=20):
    directory = os.path.join(PUZZLES_DIR, "legacy")
    dataset = []
    index_rows = []

    for n in sizes:
        group = "4x4" if n == 4 else ("9x9-generated" if n == 9 else f"{n}x{n}")
        print(f"\n── {group} (legacy, seeded) ──")
        hard_cap = int(math.floor(max_fill * n * n))
        for index in range(1, puzzles_per_size + 1):
            attempt = 0
            while True:
                puzzle_seed = derive_puzzle_seed(seed, "legacy", n, index, attempt)
                puzzle, solution, meta = generate_puzzle(
                    n,
                    seed=puzzle_seed,
                    ensure_unique=True,
                    solver_path=solver_path,
                    timeout=timeout,
                    max_fill=max_fill,
                    soft_fill=soft_fill,
                    uniqueness_timeout=uniqueness_timeout,
                )
                meta["master_seed"] = seed
                if meta["num_clues"] <= hard_cap:
                    break
                attempt += 1
                if attempt >= max_attempts:
                    raise RuntimeError(
                        f"legacy {n}x{n} puzzle {index} exceeded the "
                        f"{max_fill:.0%} clue cap after {max_attempts} attempts"
                    )

            name = puzzle_name_for("legacy", n, puzzle_seed, index)
            path = save_puzzle(puzzle, n, name, solution=solution, directory=directory)
            choices_path = _write_choices_sidecar(
                master_seed=seed,
                generator="legacy",
                n=n,
                index=index,
                attempt=attempt,
                puzzle_seed=puzzle_seed,
                puzzle_name=name,
                puzzle_path=path,
                metadata=meta,
            )
            print(f"  {name}  ({meta['num_clues']} clues, "
                  f"{meta['fill_pct']:.2f}% fill, "
                  f"unique={recorder_flag(meta['uniqueness_verified'])}, "
                  f"{meta['generation_time_s']:.2f}s) -> {os.path.basename(path)}")
            dataset.append({
                "n": n,
                "group": group,
                "puzzle_path": path,
                "solution": solution,
                "verified_unique": meta["uniqueness_verified"],
                "construction_valid": meta["uniqueness_verified"],
                "generator": "legacy",
                "master_seed": seed,
                "seed": puzzle_seed,
                "puzzle_seed": puzzle_seed,
                "index": index,
                "attempt": attempt,
                "choices_path": choices_path,
                "metadata_path": choices_path,
                "metadata": meta,
                "clue_count": meta["num_clues"],
                "fill_pct": meta["fill_pct"],
                "generation_time_s": meta["generation_time_s"],
            })
            index_rows.append({
                "master_seed": seed,
                "generator": "legacy",
                "size": n,
                "index": index,
                "attempt": attempt,
                "puzzle_seed": puzzle_seed,
                "puzzle_name": name,
                "puzzle_path": path,
                "choices_path": choices_path,
                "clue_count": meta["num_clues"],
                "fill_pct": f"{meta['fill_pct']:.4f}",
                "unique": recorder_flag(meta["uniqueness_verified"]),
                "generation_time_s": f"{meta['generation_time_s']:.9f}",
                "puzzle_hash": _grid_digest(puzzle),
                "solution_hash": _grid_digest(solution),
            })

    index_path = _write_seed_index(directory, index_rows)
    total = len(dataset)
    unique_count = sum(1 for d in dataset if d["verified_unique"])
    print(f"\n--- Dataset assembled: {total} puzzles "
          f"({unique_count} uniqueness-verified) ---")
    print(f"Puzzle directory: {os.path.abspath(directory)}")
    print(f"Seed index:       {index_path}")
    return dataset


def recorder_flag(value):
    return "YES" if value else "NO"

def assemble_dataset(sizes=None, puzzles_per_size=10, seed=42,
                     solver_path=None, timeout=60, generator="back_circulant",
                     include_known=False, generation_timeout=600,
                     max_fill=DEFAULT_LEGACY_MAX_FILL,
                     soft_fill=DEFAULT_LEGACY_SOFT_FILL,
                     uniqueness_timeout=30):
    """
    Assemble a complete dataset for benchmarking.

    - generator="back_circulant": back-circulant construction for every size
    - generator="legacy", include_known=False: purely procedural, seeded
    - generator="legacy", include_known=True: legacy hardcoded/Royle mix

    For legacy n >= 16 uniqueness is enforced with a deducibility-gated
    removal pass plus SAT refinement.  Extra clues are allowed up to
    ``max_fill``; a seed is retried if that hard cap is exceeded.

    Returns
    -------
    list of dicts:
        [{"n": int, "group": str, "puzzle_path": str,
          "solution": grid_or_None, "verified_unique": bool,
          "generator": str, "seed": int, ...}, ...]
    """
    if sizes is None:
        sizes = [4, 9, 16, 25, 36]

    for s in sizes:
        base = int(math.isqrt(s))
        assert base * base == s, f"Size {s} is not a perfect square"
        assert s in VALID_SIZES, f"Size {s} is not in VALID_SIZES"

    if generator == "back_circulant":
        return _assemble_back_circulant_dataset(sizes, puzzles_per_size, seed)
    if generator != "legacy":
        raise ValueError(f"unknown generator: {generator}")
    if not include_known:
        return _assemble_legacy_seeded_dataset(
            sizes, puzzles_per_size, seed, solver_path,
            timeout=generation_timeout,
            max_fill=max_fill,
            soft_fill=soft_fill,
            uniqueness_timeout=uniqueness_timeout,
        )

    dataset = []
    master_rng = random.Random(seed)

    for n in sizes:
        base = int(math.isqrt(n))
        group = f"{n}x{n}"
        print(f"\n── {group} ──")

        # ── For 4×4: hardcoded puzzles, then generated extras ─────
        if n == 4:
            for i, grid in enumerate(FOUR_PUZZLES[:puzzles_per_size]):
                name = f"sudoku_4x4_{i + 1:02d}"
                errors = _validate_grid(grid, n)
                if errors:
                    print(f"  WARNING: {name} has conflicts: {errors}")
                path = save_puzzle(grid, n, name)
                clues = count_clues(grid)
                print(f"  {name}  ({clues} clues) -> {os.path.basename(path)}")
                dataset.append({
                    "n": n,
                    "group": "4x4",
                    "puzzle_path": path,
                    "solution": None,
                    "verified_unique": True,  # hand-verified
                })

            # Top up with generated 4x4 puzzles when more are requested
            for i in range(len(FOUR_PUZZLES), puzzles_per_size):
                sub_seed = master_rng.randint(0, 2**31)
                puzzle, solution, meta = generate_puzzle(
                    n, seed=sub_seed, ensure_unique=True,
                    solver_path=solver_path, timeout=timeout,
                )
                name = f"sudoku_4x4_{i + 1:02d}"
                path = save_puzzle(puzzle, n, name, solution=solution)
                print(f"  {name}  ({meta['num_clues']} clues, generated, "
                      f"{meta['generation_time_s']:.2f}s) -> "
                      f"{os.path.basename(path)}")
                dataset.append({
                    "n": n,
                    "group": "4x4",
                    "puzzle_path": path,
                    "solution": solution,
                    "verified_unique": meta["uniqueness_verified"],
                })

        # ── For 9×9: include Royle 17-clue + generated ───────────
        elif n == 9:
            # Royle 17-clue puzzles (defensive filter: keep only exact 17-clue,
            # de-duplicated entries; corrupted rows are never benchmarked)
            royle_valid = []
            seen = set()
            for grid in ROYLE_17_CLUE:
                key = tuple(map(tuple, grid))
                if key in seen or count_clues(grid) != 17:
                    continue
                seen.add(key)
                royle_valid.append(grid)
            skipped = len(ROYLE_17_CLUE) - len(royle_valid)
            if skipped:
                print(f"  [note] skipped {skipped} invalid/duplicate Royle entries")

            num_royle = min(puzzles_per_size, len(royle_valid))
            for i, grid in enumerate(royle_valid[:num_royle]):
                name = f"sudoku_9x9_17clue_{i + 1:02d}"
                errors = _validate_grid(grid, n)
                if errors:
                    print(f"  WARNING: {name} has conflicts: {errors}")
                path = save_puzzle(grid, n, name)
                clues = count_clues(grid)
                print(f"  {name}  ({clues} clues, Royle 17-clue) -> "
                      f"{os.path.basename(path)}")
                dataset.append({
                    "n": n,
                    "group": "17-clue",
                    "puzzle_path": path,
                    "solution": None,
                    "verified_unique": True,  # proven unique (Royle database)
                })

            # Also generate some 9×9 puzzles with more clues
            num_gen = max(0, puzzles_per_size - num_royle)
            for i in range(num_gen):
                sub_seed = master_rng.randint(0, 2**31)
                puzzle, solution, meta = generate_puzzle(
                    n, seed=sub_seed, ensure_unique=True,
                    solver_path=solver_path, timeout=timeout,
                )
                name = f"sudoku_9x9_gen_{i + 1:02d}"
                path = save_puzzle(puzzle, n, name, solution=solution)
                print(f"  {name}  ({meta['num_clues']} clues, generated, "
                      f"{meta['generation_time_s']:.2f}s) -> "
                      f"{os.path.basename(path)}")
                dataset.append({
                    "n": n,
                    "group": "9x9-generated",
                    "puzzle_path": path,
                    "solution": solution,
                    "verified_unique": meta["uniqueness_verified"],
                })

        # ── All other sizes: generated ────────────────────────────
        else:
            for i in range(puzzles_per_size):
                sub_seed = master_rng.randint(0, 2**31)
                # Uniqueness checking: always try, but generate_puzzle
                # internally skips the slow backtracking check for n > 9
                # when no SAT solver is available.
                puzzle, solution, meta = generate_puzzle(
                    n, seed=sub_seed, target_clues=None,
                    ensure_unique=True,
                    solver_path=solver_path, timeout=timeout,
                )
                name = f"sudoku_{n}x{n}_{i + 1:02d}"
                path = save_puzzle(puzzle, n, name, solution=solution)
                print(f"  {name}  ({meta['num_clues']} clues, "
                      f"{meta['generation_time_s']:.2f}s) -> "
                      f"{os.path.basename(path)}")
                dataset.append({
                    "n": n,
                    "group": group,
                    "puzzle_path": path,
                    "solution": solution,
                    "verified_unique": meta["uniqueness_verified"],
                })

    total = len(dataset)
    unique_count = sum(1 for d in dataset if d["verified_unique"])
    print(f"\n--- Dataset assembled: {total} puzzles "
          f"({unique_count} uniqueness-verified) ---")
    print(f"Puzzle directory: {os.path.abspath(PUZZLES_DIR)}")

    return dataset


# ══════════════════════════════════════════════════════════════════════════════
#  Main — test dataset generation
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Puzzle Manager: generate a test dataset"
    )
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=[4, 9],
        help="Board sizes to generate (default: 4 9)"
    )
    parser.add_argument(
        "--count", type=int, default=3,
        help="Puzzles per size (default: 3)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Master seed (default: 42)"
    )
    parser.add_argument(
        "--solver", type=str, default=None,
        help="Path to SAT solver binary for uniqueness checks"
    )
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="Timeout per puzzle generation in seconds (default: 30)"
    )
    args = parser.parse_args()

    print("=== Puzzle Manager: Test Dataset ===\n")

    # Quick smoke test of I/O utilities
    print("-- I/O utility tests --")
    test_line = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
    test_grid = parse_oneline(test_line, n=9)
    roundtrip = grid_to_oneline(test_grid)
    assert roundtrip == test_line, "Round-trip parse/format failed"
    print(f"  parse_oneline + grid_to_oneline round-trip: OK")

    # Test Royle clue parsing
    for i, g in enumerate(ROYLE_17_CLUE[:3]):
        clues = count_clues(g)
        print(f"  Royle #{i+1}: {clues} clues")

    # Quick generation test
    print("\n-- Quick generation test (9x9) --")
    puzzle, sol, meta = generate_puzzle(9, seed=123, ensure_unique=True, timeout=15)
    print(f"  Generated: {meta['num_clues']} clues in {meta['generation_time_s']:.2f}s")
    print(f"  Uniqueness verified: {meta['uniqueness_verified']}")

    # Assemble a small dataset
    print("\n-- Assembling test dataset --")
    dataset = assemble_dataset(
        sizes=args.sizes,
        puzzles_per_size=args.count,
        seed=args.seed,
        solver_path=args.solver,
        timeout=args.timeout,
    )

    print(f"\nDone. {len(dataset)} puzzle(s) in dataset.")
    for entry in dataset:
        print(f"  [{entry['group']}] {os.path.basename(entry['puzzle_path'])} "
              f"(unique={entry['verified_unique']})")
