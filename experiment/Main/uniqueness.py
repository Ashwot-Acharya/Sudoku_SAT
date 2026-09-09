"""
uniqueness.py

Implements 4 methods of uniqueness verification for n²×n² Sudoku puzzles.
Each method returns a dict with at minimum: {"unique": bool, "method": str, "time_s": float, ...extra info}.

Methods:
1. sat_blocking_check: SAT-based blocking clause method
2. unavoidable_sets_check: Unavoidable sets concept (requires solution grid)
3. deducibility_check: Constraint propagation only (Mašulović 2022 theorem)
4. validate_solution: Validates a completed grid
5. full_uniqueness_check: Runs all applicable methods and returns combined report
"""

import os
import math
import time
import tempfile
import subprocess
from sudoku_to_cnf import encode


# ────────────────────────────────────────────────────────────────────────────────
# 1. SAT Blocking Clause Method
# ────────────────────────────────────────────────────────────────────────────────

def sat_blocking_check(puzzle, n, solver_path, timeout=600):
    """
    SAT-based blocking clause method for uniqueness verification.
    
    Algorithm:
    1. Encode puzzle to CNF and solve
    2. If UNSAT → no solution → return unique=False
    3. If SAT → get solution, add blocking clause (negation of all true vars)
    4. Solve again: UNSAT → unique (1 solution), SAT → not unique (2+ solutions)
    
    Args:
        puzzle: 2D list of ints (0 = empty), 0-indexed
        n: board size (n² × n²)
        solver_path: path to SAT solver binary
        timeout: solver timeout in seconds
        
    Returns:
        dict with keys: unique (bool), method (str), time_s (float), 
                       solutions_found (int), solution1 (grid), solution2 (grid or None)
    """
    start_time = time.time()
    
    # Encode to CNF
    clauses, num_vars, var_map, V0_list = encode(n, puzzle)
    
    # Solve first time
    sat1, assignment1, time1 = _solve_cnf_temp(clauses, num_vars, solver_path, timeout)
    
    if not sat1:
        # UNSAT → puzzle has no solution
        return {
            "unique": False,
            "method": "sat_blocking",
            "time_s": time.time() - start_time,
            "solutions_found": 0,
            "error": "puzzle has no solution"
        }
    
    # Decode first solution
    solution1 = _decode_assignment(assignment1, puzzle, n, var_map)
    
    # Add blocking clause: negate all true variables from first solution
    blocking_clause = [-var for var in assignment1]
    clauses_with_blocking = clauses + [blocking_clause]
    
    # Solve second time
    sat2, assignment2, time2 = _solve_cnf_temp(clauses_with_blocking, num_vars, solver_path, timeout)
    
    if not sat2:
        # UNSAT → exactly 1 solution (unique)
        return {
            "unique": True,
            "method": "sat_blocking",
            "time_s": time.time() - start_time,
            "solutions_found": 1,
            "solution1": solution1,
            "solve_time1_s": time1,
            "solve_time2_s": time2
        }
    else:
        # SAT → at least 2 solutions (not unique)
        solution2 = _decode_assignment(assignment2, puzzle, n, var_map)
        return {
            "unique": False,
            "method": "sat_blocking",
            "time_s": time.time() - start_time,
            "solutions_found": 2,
            "solution1": solution1,
            "solution2": solution2,
            "solve_time1_s": time1,
            "solve_time2_s": time2
        }


def _solve_cnf_temp(clauses, num_vars, solver_path, timeout):
    """
    Write CNF to temp file, run solver, parse result.
    Returns: (sat: bool, assignment: list[int], elapsed: float)
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False) as f:
        cnf_path = f.name
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")
    
    try:
        t0 = time.time()
        proc = subprocess.run(
            [solver_path, cnf_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - t0
        
        # Parse SAT/UNSAT (IPASIR standard: 10=SAT, 20=UNSAT)
        if proc.returncode == 10:
            sat = True
        elif proc.returncode == 20:
            sat = False
        else:
            # Fallback text parsing
            combined = proc.stdout + proc.stderr
            if "UNSATISFIABLE" in combined:
                sat = False
            elif "SATISFIABLE" in combined:
                sat = True
            else:
                sat = False
        
        # Parse assignment from "v" lines
        assignment = []
        if sat:
            for line in proc.stdout.splitlines():
                s = line.strip()
                if s.startswith("v ") or s == "v":
                    for tok in s.split()[1:]:
                        try:
                            lit = int(tok)
                            if lit > 0:
                                assignment.append(lit)
                        except ValueError:
                            pass
        
        return sat, assignment, elapsed
        
    finally:
        if os.path.exists(cnf_path):
            os.unlink(cnf_path)


def _decode_assignment(assignment, puzzle, n, var_map):
    """
    Decode SAT assignment back to a complete Sudoku grid.
    
    Args:
        assignment: list of positive variable indices
        puzzle: original puzzle (2D list, 0-indexed)
        n: board size
        var_map: dict (r,c,v) -> dimacs_var (1-indexed positions)
        
    Returns:
        2D list representing complete grid
    """
    # Build inverse map
    inv_map = {idx: triple for triple, idx in var_map.items()}
    true_set = set(assignment)
    
    # Start with puzzle (contains fixed clues)
    grid = [row[:] for row in puzzle]
    
    # Fill in values from assignment
    for var_idx in true_set:
        if var_idx in inv_map:
            r, c, v = inv_map[var_idx]
            grid[r - 1][c - 1] = v  # convert 1-indexed to 0-indexed
    
    return grid


# ────────────────────────────────────────────────────────────────────────────────
# 2. Unavoidable Sets Method
# ────────────────────────────────────────────────────────────────────────────────

def unavoidable_sets_check(solution_grid, puzzle, n):
    """
    Unavoidable sets concept for uniqueness verification.
    
    An unavoidable set U is a set of cells where there exists another valid grid
    that differs only on U. For a puzzle to have a unique solution, every unavoidable
    set must be "hit" (contain at least one clue from the puzzle).
    
    Strategy: Find unavoidable sets by swapping pairs of digits in rows/cols/blocks.
    
    Args:
        solution_grid: complete solution (2D list, 0-indexed)
        puzzle: original puzzle with clues (2D list, 0-indexed)
        n: board size
        
    Returns:
        dict with keys: unique (bool), method (str), time_s (float),
                       num_sets_found (int), all_hit (bool), unhit_sets (list)
    """
    start_time = time.time()
    box = int(math.sqrt(n))
    
    unavoidable_sets = []
    
    # Find clue positions
    clue_positions = set()
    for r in range(n):
        for c in range(n):
            if puzzle[r][c] != 0:
                clue_positions.add((r, c))
    
    # Find unavoidable rectangles (size-4 sets)
    # For each pair of digits (d1, d2), find pairs of rows where swapping creates valid grid
    for d1 in range(1, n + 1):
        for d2 in range(d1 + 1, n + 1):
            # Find all positions of d1 and d2
            d1_positions = {}  # row -> col
            d2_positions = {}  # row -> col
            
            for r in range(n):
                for c in range(n):
                    if solution_grid[r][c] == d1:
                        d1_positions[r] = c
                    elif solution_grid[r][c] == d2:
                        d2_positions[r] = c
            
            # Check pairs of rows
            rows = list(range(n))
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    r1, r2 = rows[i], rows[j]
                    
                    if r1 not in d1_positions or r1 not in d2_positions:
                        continue
                    if r2 not in d1_positions or r2 not in d2_positions:
                        continue
                    
                    c1_d1, c1_d2 = d1_positions[r1], d2_positions[r1]
                    c2_d1, c2_d2 = d1_positions[r2], d2_positions[r2]
                    
                    # Check if these 4 cells form an unavoidable rectangle
                    # Condition: same columns AND same blocks
                    if c1_d1 == c2_d1 and c1_d2 == c2_d2:
                        # Same columns - check if swapping maintains block constraint
                        b1_d1 = _get_block(r1, c1_d1, box)
                        b1_d2 = _get_block(r1, c1_d2, box)
                        b2_d1 = _get_block(r2, c2_d1, box)
                        b2_d2 = _get_block(r2, c2_d2, box)
                        
                        # If blocks are the same after swap, it's invalid
                        # We want: swapping creates a DIFFERENT valid grid
                        if b1_d1 == b2_d1 and b1_d2 == b2_d2:
                            u_set = frozenset([(r1, c1_d1), (r1, c1_d2), (r2, c2_d1), (r2, c2_d2)])
                            if len(u_set) == 4:  # ensure 4 distinct cells
                                unavoidable_sets.append(u_set)
    
    # Remove duplicates
    unavoidable_sets = list(set(unavoidable_sets))
    
    # Check if all unavoidable sets are hit by clues
    unhit_sets = []
    for u_set in unavoidable_sets:
        if not any(cell in clue_positions for cell in u_set):
            unhit_sets.append(u_set)
    
    all_hit = len(unhit_sets) == 0
    
    # If there are unhit unavoidable sets, the puzzle is NOT unique
    # (another solution exists that differs only on those sets)
    unique = all_hit if unavoidable_sets else None  # None if no sets found (inconclusive)
    
    return {
        "unique": unique,
        "method": "unavoidable_sets",
        "time_s": time.time() - start_time,
        "num_sets_found": len(unavoidable_sets),
        "all_hit": all_hit,
        "num_unhit": len(unhit_sets),
        "unhit_sets": [list(s) for s in unhit_sets]
    }


def _get_block(r, c, box):
    """Return block index (0-indexed) for cell (r, c)."""
    return (r // box) * box + (c // box)


# ────────────────────────────────────────────────────────────────────────────────
# 3. Deducibility Method (Constraint Propagation)
# ────────────────────────────────────────────────────────────────────────────────

def deducibility_check(puzzle, n):
    """
    Implements the theorem: "unique solution iff logically deducible" (Mašulović 2022).
    
    Uses constraint propagation ONLY (no guessing/backtracking):
    - Naked singles (cell has only one candidate)
    - Hidden singles (digit has only one place in row/col/block)
    - Locked candidates (pointing pairs/box-line reduction)
    
    If the puzzle can be fully solved → unique.
    If stuck but not complete → inconclusive (might be unique but requires deeper techniques).
    
    Args:
        puzzle: 2D list of ints (0 = empty), 0-indexed
        n: board size
        
    Returns:
        dict with keys: unique (bool or None), method (str), time_s (float),
                       cells_solved (int), total_empty (int), techniques_used (list),
                       final_grid (2D list)
    """
    start_time = time.time()
    box = int(math.sqrt(n))
    
    # Initialize grid and candidates
    grid = [row[:] for row in puzzle]
    candidates = [[set(range(1, n + 1)) if grid[r][c] == 0 else set() 
                   for c in range(n)] for r in range(n)]
    
    # Remove candidates based on initial clues
    for r in range(n):
        for c in range(n):
            if grid[r][c] != 0:
                _eliminate_value(grid, candidates, r, c, grid[r][c], n, box)
    
    initial_empty = sum(1 for r in range(n) for c in range(n) if puzzle[r][c] == 0)
    techniques_used = []
    progress = True
    
    while progress:
        progress = False
        
        # Naked singles
        for r in range(n):
            for c in range(n):
                if grid[r][c] == 0 and len(candidates[r][c]) == 1:
                    val = list(candidates[r][c])[0]
                    grid[r][c] = val
                    candidates[r][c] = set()
                    _eliminate_value(grid, candidates, r, c, val, n, box)
                    if "naked_singles" not in techniques_used:
                        techniques_used.append("naked_singles")
                    progress = True
        
        # Hidden singles in rows
        for r in range(n):
            for val in range(1, n + 1):
                positions = [c for c in range(n) if val in candidates[r][c]]
                if len(positions) == 1:
                    c = positions[0]
                    if grid[r][c] == 0:
                        grid[r][c] = val
                        candidates[r][c] = set()
                        _eliminate_value(grid, candidates, r, c, val, n, box)
                        if "hidden_singles_row" not in techniques_used:
                            techniques_used.append("hidden_singles_row")
                        progress = True
        
        # Hidden singles in columns
        for c in range(n):
            for val in range(1, n + 1):
                positions = [r for r in range(n) if val in candidates[r][c]]
                if len(positions) == 1:
                    r = positions[0]
                    if grid[r][c] == 0:
                        grid[r][c] = val
                        candidates[r][c] = set()
                        _eliminate_value(grid, candidates, r, c, val, n, box)
                        if "hidden_singles_col" not in techniques_used:
                            techniques_used.append("hidden_singles_col")
                        progress = True
        
        # Hidden singles in blocks
        for br in range(0, n, box):
            for bc in range(0, n, box):
                for val in range(1, n + 1):
                    positions = [(r, c) for r in range(br, br + box) 
                                 for c in range(bc, bc + box)
                                 if val in candidates[r][c]]
                    if len(positions) == 1:
                        r, c = positions[0]
                        if grid[r][c] == 0:
                            grid[r][c] = val
                            candidates[r][c] = set()
                            _eliminate_value(grid, candidates, r, c, val, n, box)
                            if "hidden_singles_block" not in techniques_used:
                                techniques_used.append("hidden_singles_block")
                            progress = True
        
        # Locked candidates (simplified)
        # If a digit in a block can only be in one row/col, eliminate from rest of that row/col
        for br in range(0, n, box):
            for bc in range(0, n, box):
                for val in range(1, n + 1):
                    positions = [(r, c) for r in range(br, br + box) 
                                 for c in range(bc, bc + box)
                                 if val in candidates[r][c]]
                    
                    if positions:
                        rows = set(r for r, c in positions)
                        cols = set(c for r, c in positions)
                        
                        # If all in same row, eliminate from rest of row
                        if len(rows) == 1:
                            row = list(rows)[0]
                            for c in range(n):
                                if c < bc or c >= bc + box:
                                    if val in candidates[row][c]:
                                        candidates[row][c].discard(val)
                                        if "locked_candidates" not in techniques_used:
                                            techniques_used.append("locked_candidates")
                                        progress = True
                        
                        # If all in same col, eliminate from rest of col
                        if len(cols) == 1:
                            col = list(cols)[0]
                            for r in range(n):
                                if r < br or r >= br + box:
                                    if val in candidates[r][col]:
                                        candidates[r][col].discard(val)
                                        if "locked_candidates" not in techniques_used:
                                            techniques_used.append("locked_candidates")
                                        progress = True
    
    # Count how many cells were solved
    cells_solved = sum(1 for r in range(n) for c in range(n) if grid[r][c] != 0) - (n * n - initial_empty)
    is_complete = all(grid[r][c] != 0 for r in range(n) for c in range(n))
    
    # By Mašulović theorem: if fully solved by propagation → unique
    # If not fully solved → inconclusive (might still be unique but requires guessing)
    unique = True if is_complete else None
    
    return {
        "unique": unique,
        "method": "deducibility",
        "time_s": time.time() - start_time,
        "cells_solved": cells_solved,
        "total_empty": initial_empty,
        "is_complete": is_complete,
        "techniques_used": techniques_used,
        "final_grid": grid
    }


def _eliminate_value(grid, candidates, r, c, val, n, box):
    """
    Eliminate value from all peers (same row/col/block) of cell (r, c).
    """
    # Eliminate from row
    for c2 in range(n):
        if c2 != c:
            candidates[r][c2].discard(val)
    
    # Eliminate from column
    for r2 in range(n):
        if r2 != r:
            candidates[r2][c].discard(val)
    
    # Eliminate from block
    br = (r // box) * box
    bc = (c // box) * box
    for r2 in range(br, br + box):
        for c2 in range(bc, bc + box):
            if (r2, c2) != (r, c):
                candidates[r2][c2].discard(val)


# ────────────────────────────────────────────────────────────────────────────────
# 4. Validate Solution
# ────────────────────────────────────────────────────────────────────────────────

def validate_solution(grid, n):
    """
    Validates that a completed grid is a valid Sudoku solution.
    
    Checks:
    - Every row has all digits 1..n²
    - Every column has all digits 1..n²
    - Every box has all digits 1..n²
    
    Args:
        grid: 2D list of ints (0-indexed)
        n: board size
        
    Returns:
        dict with keys: valid (bool), errors (list of str)
    """
    box = int(math.sqrt(n))
    errors = []
    expected = set(range(1, n + 1))
    
    # Check rows
    for r in range(n):
        row_vals = set(grid[r])
        if row_vals != expected:
            errors.append(f"Row {r} has invalid values: {sorted(row_vals)}")
    
    # Check columns
    for c in range(n):
        col_vals = set(grid[r][c] for r in range(n))
        if col_vals != expected:
            errors.append(f"Col {c} has invalid values: {sorted(col_vals)}")
    
    # Check blocks
    for br in range(0, n, box):
        for bc in range(0, n, box):
            block_vals = set(grid[r][c] for r in range(br, br + box) 
                           for c in range(bc, bc + box))
            if block_vals != expected:
                errors.append(f"Block ({br // box}, {bc // box}) has invalid values: {sorted(block_vals)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# ────────────────────────────────────────────────────────────────────────────────
# 5. Full Uniqueness Check (Combined)
# ────────────────────────────────────────────────────────────────────────────────

def full_uniqueness_check(puzzle, n, solver_path, solution_grid=None, timeout=600):
    """
    Runs all applicable uniqueness check methods and returns a combined report.
    
    Methods run:
    - sat_blocking_check (always)
    - unavoidable_sets_check (only if solution_grid provided)
    - deducibility_check (always)
    
    Args:
        puzzle: 2D list of ints (0 = empty), 0-indexed
        n: board size
        solver_path: path to SAT solver binary
        solution_grid: optional complete solution (2D list, 0-indexed)
        timeout: solver timeout in seconds
        
    Returns:
        dict with keys: sat_blocking, unavoidable_sets (or None), deducibility,
                       consensus (True/False/None), total_time_s
    """
    start_time = time.time()
    
    results = {}
    
    # Run SAT blocking check
    results["sat_blocking"] = sat_blocking_check(puzzle, n, solver_path, timeout)
    
    # Run unavoidable sets check if solution provided
    if solution_grid is not None:
        results["unavoidable_sets"] = unavoidable_sets_check(solution_grid, puzzle, n)
    else:
        results["unavoidable_sets"] = None
    
    # Run deducibility check
    results["deducibility"] = deducibility_check(puzzle, n)
    
    # Determine consensus
    unique_results = []
    
    if results["sat_blocking"]["unique"] is not None:
        unique_results.append(results["sat_blocking"]["unique"])
    
    if results["unavoidable_sets"] is not None and results["unavoidable_sets"]["unique"] is not None:
        unique_results.append(results["unavoidable_sets"]["unique"])
    
    if results["deducibility"]["unique"] is not None:
        unique_results.append(results["deducibility"]["unique"])
    
    # Consensus: True if all agree on unique, False if any says not unique, None if inconclusive
    if not unique_results:
        consensus = None
    elif all(unique_results):
        consensus = True
    elif any(u is False for u in unique_results):
        consensus = False
    else:
        consensus = None
    
    results["consensus"] = consensus
    results["total_time_s"] = time.time() - start_time
    
    return results
