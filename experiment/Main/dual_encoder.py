"""
dual_encoder.py
Two CNF encoding strategies for Sudoku puzzles, plus comparison utilities.

Encoding 1 — Naive (Full) Encoding  φ  (phi)
    Uses the full n³ variable space with NO optimisation from given clues.

Encoding 2 — Compact/Optimised Encoding  φ' (phi-prime)
    Wraps the encoding from sudoku_to_cnf.py (Kwon & Jain).
"""

import os
import math
import time
from collections import Counter

from sudoku_to_cnf import (
    encode as _encode_compact,
    read_puzzle,
    write_dimacs as _write_dimacs_compact,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CNF_DIR = os.path.join(SCRIPT_DIR, "..", "CNF")
os.makedirs(CNF_DIR, exist_ok=True)


# ── Naive (Full) Encoding ─────────────────────────────────────────────────────

def _naive_var(r, c, v, n):
    """Map 1-indexed (r, c, v) to a 1-indexed DIMACS variable."""
    return (r - 1) * n * n + (c - 1) * n + v


def encode_naive(n, puzzle):
    """
    Full/naive CNF encoding.  Uses n³ variables (one for each (row, col, val)
    triple).  Does NOT remove variables or clauses based on given clues.

    Variable mapping:
        var(r, c, v) = (r-1)*n*n + (c-1)*n + v     (1-indexed, r,c,v ∈ [1,n])

    Clauses generated:
        1. Cell definedness   – each cell has at least one value
        2. Cell uniqueness    – each cell has at most one value
        3. Row definedness    – each value appears in each row at least once
        4. Row uniqueness     – each value appears at most once per row
        5. Col definedness    – similarly
        6. Col uniqueness     – similarly
        7. Block definedness  – similarly
        8. Block uniqueness   – similarly
        9. Clue unit clauses  – for each given cell (r,c)=v, add [var(r,c,v)]

    Returns
    -------
    (clauses, num_vars, var_map)
        clauses  : list[list[int]]          – DIMACS clauses
        num_vars : int                      – total number of variables (n³)
        var_map  : dict[(r,c,v) -> int]     – variable mapping
    """
    box = int(math.sqrt(n))
    num_vars = n * n * n
    var_map = {}
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v in range(1, n + 1):
                var_map[(r, c, v)] = _naive_var(r, c, v, n)

    clauses = []

    # 1. Cell definedness: each cell has at least one value
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            clauses.append([_naive_var(r, c, v, n) for v in range(1, n + 1)])

    # 2. Cell uniqueness: each cell has at most one value
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for vi in range(1, n):
                for vj in range(vi + 1, n + 1):
                    clauses.append([
                        -_naive_var(r, c, vi, n),
                        -_naive_var(r, c, vj, n),
                    ])

    # 3. Row definedness: each value appears in each row at least once
    for r in range(1, n + 1):
        for v in range(1, n + 1):
            clauses.append([_naive_var(r, c, v, n) for c in range(1, n + 1)])

    # 4. Row uniqueness: each value appears at most once per row
    for r in range(1, n + 1):
        for v in range(1, n + 1):
            for ci in range(1, n):
                for cj in range(ci + 1, n + 1):
                    clauses.append([
                        -_naive_var(r, ci, v, n),
                        -_naive_var(r, cj, v, n),
                    ])

    # 5. Col definedness: each value appears in each column at least once
    for c in range(1, n + 1):
        for v in range(1, n + 1):
            clauses.append([_naive_var(r, c, v, n) for r in range(1, n + 1)])

    # 6. Col uniqueness: each value appears at most once per column
    for c in range(1, n + 1):
        for v in range(1, n + 1):
            for ri in range(1, n):
                for rj in range(ri + 1, n + 1):
                    clauses.append([
                        -_naive_var(ri, c, v, n),
                        -_naive_var(rj, c, v, n),
                    ])

    # 7. Block definedness: each value appears in each block at least once
    for br in range(0, n, box):
        for bc in range(0, n, box):
            for v in range(1, n + 1):
                clauses.append([
                    _naive_var(br + dr, bc + dc, v, n)
                    for dr in range(1, box + 1)
                    for dc in range(1, box + 1)
                ])

    # 8. Block uniqueness: each value appears at most once per block
    for br in range(0, n, box):
        for bc in range(0, n, box):
            for v in range(1, n + 1):
                cells = [
                    (br + dr, bc + dc)
                    for dr in range(1, box + 1)
                    for dc in range(1, box + 1)
                ]
                for i in range(len(cells)):
                    for j in range(i + 1, len(cells)):
                        r1, c1 = cells[i]
                        r2, c2 = cells[j]
                        clauses.append([
                            -_naive_var(r1, c1, v, n),
                            -_naive_var(r2, c2, v, n),
                        ])

    # 9. Clue unit clauses: for each given cell (r,c)=v, add [var(r,c,v)]
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            v = puzzle[r - 1][c - 1]
            if v != 0:
                clauses.append([_naive_var(r, c, v, n)])

    return clauses, num_vars, var_map


# ── Compact / Optimised Encoding ──────────────────────────────────────────────

def encode_compact(n, puzzle):
    """
    Optimised encoding from Kwon & Jain.  Wraps sudoku_to_cnf.encode().

    Returns
    -------
    (clauses, num_vars, var_map)
        clauses  : list[list[int]]
        num_vars : int
        var_map  : dict[(r,c,v) -> int]
    """
    clauses, num_vars, var_map, _V0_list = _encode_compact(n, puzzle)
    return clauses, num_vars, var_map


# ── Comparison ────────────────────────────────────────────────────────────────

def _clause_length_distribution(clauses):
    """Return a dict mapping clause length -> count."""
    return dict(sorted(Counter(len(c) for c in clauses).items()))


def compare_encodings(n, puzzle):
    """
    Encode the same puzzle with both methods and return comparison statistics.

    Returns
    -------
    dict with keys:
        n, num_clues,
        naive   : {num_vars, num_clauses, encode_time_s, clause_lengths}
        compact : {num_vars, num_clauses, encode_time_s, clause_lengths}
        reduction : {var_reduction_pct, clause_reduction_pct}
    """
    # Count clues
    num_clues = sum(
        1
        for r in range(n)
        for c in range(n)
        if puzzle[r][c] != 0
    )

    # Naive
    t0 = time.time()
    n_clauses, n_vars, _ = encode_naive(n, puzzle)
    naive_time = time.time() - t0

    # Compact
    t0 = time.time()
    c_clauses, c_vars, _ = encode_compact(n, puzzle)
    compact_time = time.time() - t0

    naive_stats = {
        "num_vars": n_vars,
        "num_clauses": len(n_clauses),
        "encode_time_s": naive_time,
        "clause_lengths": _clause_length_distribution(n_clauses),
    }
    compact_stats = {
        "num_vars": c_vars,
        "num_clauses": len(c_clauses),
        "encode_time_s": compact_time,
        "clause_lengths": _clause_length_distribution(c_clauses),
    }

    var_red = (1 - c_vars / n_vars) * 100 if n_vars else 0.0
    clause_red = (
        (1 - len(c_clauses) / len(n_clauses)) * 100
        if len(n_clauses)
        else 0.0
    )

    return {
        "n": n,
        "num_clues": num_clues,
        "naive": naive_stats,
        "compact": compact_stats,
        "reduction": {
            "var_reduction_pct": var_red,
            "clause_reduction_pct": clause_red,
        },
    }


# ── DIMACS writers ────────────────────────────────────────────────────────────

def write_dimacs_naive(filepath, clauses, num_vars, n, puzzle):
    """Write the naive encoding to DIMACS format with comments."""
    num_clues = sum(
        1 for r in range(n) for c in range(n) if puzzle[r][c] != 0
    )

    with open(filepath, "w") as f:
        f.write(f"c Naive (full) CNF encoding for {n}x{n} Sudoku\n")
        f.write(f"c Variables: {num_vars}  Clauses: {len(clauses)}\n")
        f.write(f"c Clues: {num_clues}\n")
        f.write(f"c SIZE {n}\n")

        # Variable mapping comment: var(r,c,v) = (r-1)*n*n + (c-1)*n + v
        f.write(f"c VAR_FORMULA var(r,c,v) = (r-1)*{n}*{n} + (c-1)*{n} + v\n")

        # Fixed cells
        for r in range(1, n + 1):
            for c in range(1, n + 1):
                v = puzzle[r - 1][c - 1]
                if v != 0:
                    f.write(f"c FIXED {r} {c} {v}\n")

        # Problem line
        f.write(f"p cnf {num_vars} {len(clauses)}\n")

        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")


def write_dimacs_compact(filepath, clauses, num_vars, n, puzzle, V0_list, fixed_cells):
    """Write the compact encoding to DIMACS format (wraps sudoku_to_cnf.write_dimacs)."""
    _write_dimacs_compact(filepath, clauses, num_vars, n, filepath, V0_list, fixed_cells)


# ── Encode-and-save ───────────────────────────────────────────────────────────

def encode_puzzle_both(puzzle_path, output_dir):
    """
    Read a puzzle file, encode with BOTH methods, save both CNF files.

    Returns
    -------
    dict with keys:
        naive_cnf   : str  – path to naive CNF file
        compact_cnf : str  – path to compact CNF file
        comparison  : dict – output of compare_encodings()
    """
    os.makedirs(output_dir, exist_ok=True)

    n, puzzle = read_puzzle(puzzle_path)
    basename = os.path.splitext(os.path.basename(puzzle_path))[0]

    # ── Naive encoding ────────────────────────────────────────────────────
    naive_cnf_path = os.path.join(output_dir, basename + "_naive.cnf")
    n_clauses, n_vars, _ = encode_naive(n, puzzle)
    write_dimacs_naive(naive_cnf_path, n_clauses, n_vars, n, puzzle)

    # ── Compact encoding ──────────────────────────────────────────────────
    compact_cnf_path = os.path.join(output_dir, basename + "_compact.cnf")
    c_clauses, c_vars, c_var_map, V0_list = _encode_compact(n, puzzle)

    fixed_cells = {}
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            v = puzzle[r - 1][c - 1]
            if v != 0:
                fixed_cells[(r, c)] = v

    _write_dimacs_compact(
        compact_cnf_path, c_clauses, c_vars, n,
        puzzle_path, V0_list, fixed_cells,
    )

    # ── Comparison stats ──────────────────────────────────────────────────
    comparison = compare_encodings(n, puzzle)

    return {
        "naive_cnf": naive_cnf_path,
        "compact_cnf": compact_cnf_path,
        "comparison": comparison,
    }


# ── CLI demo ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import json

    # If a puzzle path is given on the command line, use it; otherwise generate
    # a small 4x4 demo puzzle inline.
    if len(sys.argv) > 1:
        puzzle_path = sys.argv[1]
        n, puzzle = read_puzzle(puzzle_path)
    else:
        # Hardcoded 4x4 demo puzzle (box size 2)
        n = 4
        puzzle = [
            [1, 0, 0, 0],
            [0, 0, 3, 0],
            [0, 2, 0, 0],
            [0, 0, 0, 4],
        ]

    print(f"=== Dual Encoder Demo ({n}x{n}) ===\n")

    # ── Naive encoding ────────────────────────────────────────────────────
    t0 = time.time()
    n_clauses, n_vars, n_vmap = encode_naive(n, puzzle)
    naive_t = time.time() - t0
    print(f"Naive   encoding:  vars={n_vars}  clauses={len(n_clauses)}  time={naive_t:.4f}s")

    # ── Compact encoding ──────────────────────────────────────────────────
    t0 = time.time()
    c_clauses, c_vars, c_vmap = encode_compact(n, puzzle)
    compact_t = time.time() - t0
    print(f"Compact encoding:  vars={c_vars}  clauses={len(c_clauses)}  time={compact_t:.4f}s")

    # ── Comparison ────────────────────────────────────────────────────────
    comparison = compare_encodings(n, puzzle)
    print(f"\n--- Comparison ---")
    print(f"Clues:             {comparison['num_clues']}")
    print(f"Var reduction:     {comparison['reduction']['var_reduction_pct']:.1f}%")
    print(f"Clause reduction:  {comparison['reduction']['clause_reduction_pct']:.1f}%")
    print(f"\nNaive clause lengths:   {comparison['naive']['clause_lengths']}")
    print(f"Compact clause lengths: {comparison['compact']['clause_lengths']}")

    # ── Save CNF files (if a puzzle file was provided) ────────────────────
    if len(sys.argv) > 1:
        result = encode_puzzle_both(puzzle_path, CNF_DIR)
        print(f"\nSaved naive   CNF: {result['naive_cnf']}")
        print(f"Saved compact CNF: {result['compact_cnf']}")
    else:
        # Save demo to /tmp
        demo_dir = os.path.join("/tmp", "dual_encoder_demo")
        os.makedirs(demo_dir, exist_ok=True)

        naive_path = os.path.join(demo_dir, "demo_4x4_naive.cnf")
        write_dimacs_naive(naive_path, n_clauses, n_vars, n, puzzle)
        print(f"\nSaved naive   CNF: {naive_path}")

        # For compact, we need V0_list and fixed_cells
        c_clauses_full, c_vars_full, c_vmap_full, V0_list = _encode_compact(n, puzzle)
        fixed_cells = {}
        for r in range(1, n + 1):
            for c in range(1, n + 1):
                v = puzzle[r - 1][c - 1]
                if v != 0:
                    fixed_cells[(r, c)] = v
        compact_path = os.path.join(demo_dir, "demo_4x4_compact.cnf")
        _write_dimacs_compact(
            compact_path, c_clauses_full, c_vars_full, n,
            "demo_4x4", V0_list, fixed_cells,
        )
        print(f"Saved compact CNF: {compact_path}")

    print("\nDone.")
