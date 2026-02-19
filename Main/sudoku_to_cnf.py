"""
sudoku_to_cnf.py
Converts a Sudoku puzzle file to DIMACS CNF format using the OPTIMIZED encoding
from: "Optimized CNF Encoding for Sudoku Puzzles" (Kwon & Jain).

Key idea: exploit fixed (pre-assigned) cells to eliminate variables and clauses
that are already determined — dramatically reducing CNF size.

Encoding used: φ' (reduced extended encoding)
  - Uniqueness constraints: Cell_u, Row_u, Col_u, Block_u  (delete satisfied clauses)
  - Definedness constraints: Cell_d, Row_d, Col_d, Block_d (delete false literals)
  - Assigned unit clauses for fixed cells

Output: ../CNF/sudoku_<size>_<id>.cnf  (DIMACS format)
"""

import os
import math
import argparse
import time

# ── paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CNF_DIR    = os.path.join(SCRIPT_DIR, "..", "CNF")
os.makedirs(CNF_DIR, exist_ok=True)

# ── variable encoding ──────────────────────────────────────────────────────────

def var(r, c, v, n):
    """Return the DIMACS variable number for (row r, col c, value v). 1-indexed."""
    return (r - 1) * n * n + (c - 1) * n + (v - 1) + 1


# ── puzzle reader ──────────────────────────────────────────────────────────────

def read_puzzle(filepath):
    """Read a puzzle file produced by sudoku_generator.py."""
    with open(filepath) as f:
        lines = [l.strip() for l in f if l.strip()]

    n       = int(lines[0].split()[1])
    puzzle  = []
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


# ── optimized CNF encoding ─────────────────────────────────────────────────────

def encode(n, puzzle):
    """
    Produce clauses using the optimised encoding φ' from Kwon & Jain.

    Returns (clauses, num_vars, V0) where clauses is a list of lists of ints.
    """
    box = int(math.sqrt(n))

    # ── partition variables ────────────────────────────────────────────────────
    # V+  : variables known TRUE  (fixed cell value)
    # V-  : variables known FALSE (same cell/row/col/block as a V+ variable)
    # V0  : unknown — what the SAT solver must decide

    V_plus  = set()   # (r,c,v)  1-indexed
    V_minus = set()

    fixed = {}  # (r,c) -> v  for pre-assigned cells
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            v = puzzle[r - 1][c - 1]
            if v != 0:
                fixed[(r, c)] = v
                V_plus.add((r, c, v))

    def luc(i, box):
        """Left-upper corner of the block containing index i."""
        return ((i - 1) // box) * box + 1

    for (r, c, v) in list(V_plus):
        # same cell, different value
        for v2 in range(1, n + 1):
            if v2 != v:
                V_minus.add((r, c, v2))
        # same row, same value
        for c2 in range(1, n + 1):
            if c2 != c:
                V_minus.add((r, c2, v))
        # same col, same value
        for r2 in range(1, n + 1):
            if r2 != r:
                V_minus.add((r2, c, v))
        # same block, same value
        br, bc = luc(r, box), luc(c, box)
        for r2 in range(br, br + box):
            for c2 in range(bc, bc + box):
                if (r2, c2) != (r, c):
                    V_minus.add((r2, c2, v))

    # V0 = all variables not in V+ or V-
    V0 = set()
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v in range(1, n + 1):
                triple = (r, c, v)
                if triple not in V_plus and triple not in V_minus:
                    V0.add(triple)

    # Build a mapping from (r,c,v) in V0 to a compact DIMACS integer
    V0_list    = sorted(V0)
    var_map    = {triple: idx + 1 for idx, triple in enumerate(V0_list)}
    num_vars   = len(var_map)

    def lit(r, c, v, neg=False):
        """Return DIMACS literal, or sentinel string if variable is determined.
        
        neg=False means we want the positive literal  (+x):
            x in V+  -> TRUE  (clause satisfied, drop it)
            x in V-  -> FALSE (literal false, drop it from clause)
        neg=True means we want the negative literal  (NOT x):
            x in V+  -> FALSE (NOT true = false, drop literal from clause)
            x in V-  -> TRUE  (NOT false = true, clause satisfied, drop it)
        """
        if (r, c, v) in V_plus:
            return "FALSE" if neg else "TRUE"
        if (r, c, v) in V_minus:
            return "TRUE" if neg else "FALSE"
        idx = var_map[(r, c, v)]
        return -idx if neg else idx

    clauses = []

    # ── Assigned (unit clauses for fixed cells) ────────────────────────────────
    # These are all in V_plus so they are eliminated by ⇓V+; no clause needed.
    # (The SAT solver starts with them implicitly satisfied.)

    # ── helper: add clause, applying reductions ────────────────────────────────
    def add_clause(literals):
        """
        literals: list of (r,c,v,neg) tuples.
        Apply ⇓V+ (drop clause if any literal is TRUE) and ↓V- (drop FALSE lits).
        """
        resolved = []
        for (r, c, v, neg) in literals:
            l = lit(r, c, v, neg)
            if l == "TRUE":
                return          # clause satisfied → skip entirely  (⇓V+)
            if l == "FALSE":
                continue        # literal false → drop it           (↓V-)
            resolved.append(l)
        if resolved:            # don't add empty clauses (would make UNSAT)
            clauses.append(resolved)

    # ── Cell definedness: each cell has at least one value ─────────────────────
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            add_clause([(r, c, v, False) for v in range(1, n + 1)])

    # ── Cell uniqueness: each cell has at most one value ──────────────────────
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for vi in range(1, n):
                for vj in range(vi + 1, n + 1):
                    add_clause([(r, c, vi, True), (r, c, vj, True)])

    # ── Row definedness ────────────────────────────────────────────────────────
    for r in range(1, n + 1):
        for v in range(1, n + 1):
            add_clause([(r, c, v, False) for c in range(1, n + 1)])

    # ── Row uniqueness ─────────────────────────────────────────────────────────
    for r in range(1, n + 1):
        for v in range(1, n + 1):
            for ci in range(1, n):
                for cj in range(ci + 1, n + 1):
                    add_clause([(r, ci, v, True), (r, cj, v, True)])

    # ── Col definedness ────────────────────────────────────────────────────────
    for c in range(1, n + 1):
        for v in range(1, n + 1):
            add_clause([(r, c, v, False) for r in range(1, n + 1)])

    # ── Col uniqueness ─────────────────────────────────────────────────────────
    for c in range(1, n + 1):
        for v in range(1, n + 1):
            for ri in range(1, n):
                for rj in range(ri + 1, n + 1):
                    add_clause([(ri, c, v, True), (rj, c, v, True)])

    # ── Block definedness ──────────────────────────────────────────────────────
    for roffs in range(0, n, box):
        for coffs in range(0, n, box):
            for v in range(1, n + 1):
                add_clause([
                    (roffs + dr, coffs + dc, v, False)
                    for dr in range(1, box + 1)
                    for dc in range(1, box + 1)
                ])

    # ── Block uniqueness ───────────────────────────────────────────────────────
    for roffs in range(0, n, box):
        for coffs in range(0, n, box):
            for v in range(1, n + 1):
                cells_in_block = [
                    (roffs + dr, coffs + dc)
                    for dr in range(1, box + 1)
                    for dc in range(1, box + 1)
                ]
                for i in range(len(cells_in_block)):
                    for j in range(i + 1, len(cells_in_block)):
                        r1, c1 = cells_in_block[i]
                        r2, c2 = cells_in_block[j]
                        add_clause([(r1, c1, v, True), (r2, c2, v, True)])

    return clauses, num_vars, var_map, V0_list


# ── DIMACS writer ──────────────────────────────────────────────────────────────

def write_dimacs(filepath, clauses, num_vars, n, source_file):
    with open(filepath, "w") as f:
        f.write(f"c Optimised CNF encoding for {n}x{n} Sudoku\n")
        f.write(f"c Source: {os.path.basename(source_file)}\n")
        f.write(f"c Variables: {num_vars}  Clauses: {len(clauses)}\n")
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")


# ── main ───────────────────────────────────────────────────────────────────────

def convert_file(puzzle_path, verbose=True):
    basename = os.path.splitext(os.path.basename(puzzle_path))[0]
    cnf_path = os.path.join(CNF_DIR, basename + ".cnf")

    t0     = time.time()
    n, puzzle = read_puzzle(puzzle_path)
    clauses, num_vars, var_map, V0_list = encode(n, puzzle)
    write_dimacs(cnf_path, clauses, num_vars, n, puzzle_path)
    elapsed = time.time() - t0

    if verbose:
        print(f"  {os.path.basename(puzzle_path)} → {os.path.basename(cnf_path)}")
        print(f"    vars={num_vars}  clauses={len(clauses)}  time={elapsed:.3f}s")

    return cnf_path, num_vars, len(clauses), elapsed


def main():
    parser = argparse.ArgumentParser(description="Sudoku → optimised CNF encoder")
    parser.add_argument("puzzles", nargs="*",
                        help="Puzzle .txt files to convert (default: all in Puzzles/)")
    args = parser.parse_args()

    puzzles_dir = os.path.join(SCRIPT_DIR, "..", "Puzzles")

    if args.puzzles:
        files = args.puzzles
    else:
        files = sorted(
            os.path.join(puzzles_dir, f)
            for f in os.listdir(puzzles_dir)
            if f.endswith(".txt")
        )

    if not files:
        print("No puzzle files found.")
        return

    print(f"Converting {len(files)} puzzle(s)...\n")
    for f in files:
        convert_file(f)

    print(f"\n✓ CNF files saved to: {os.path.abspath(CNF_DIR)}")


if __name__ == "__main__":
    main()