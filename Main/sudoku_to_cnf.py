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

The var_map (compact index -> (r,c,v)) is embedded in the CNF as comment lines:
  c MAP <dimacs_var> <r> <c> <v>
so the C solver can reconstruct the mapping without needing the original puzzle.

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

    Returns (clauses, num_vars, var_map, V0_list) where:
      - clauses   : list of lists of ints  (DIMACS literals)
      - num_vars  : number of free variables
      - var_map   : dict (r,c,v) -> dimacs_var
      - V0_list   : sorted list of (r,c,v) triples in V0  (for MAP comments)
    """
    box = int(math.sqrt(n))

    # ── partition variables ────────────────────────────────────────────────────
    # V+  : variables known TRUE  (fixed cell value)
    # V-  : variables known FALSE (same cell/row/col/block as a V+ variable)
    # V0  : unknown — what the SAT solver must decide

    V_plus  = set()
    V_minus = set()

    fixed = {}
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            v = puzzle[r - 1][c - 1]
            if v != 0:
                fixed[(r, c)] = v
                V_plus.add((r, c, v))

    def luc(i):
        return ((i - 1) // box) * box + 1

    for (r, c, v) in list(V_plus):
        for v2 in range(1, n + 1):
            if v2 != v:
                V_minus.add((r, c, v2))
        for c2 in range(1, n + 1):
            if c2 != c:
                V_minus.add((r, c2, v))
        for r2 in range(1, n + 1):
            if r2 != r:
                V_minus.add((r2, c, v))
        br, bc = luc(r), luc(c)
        for r2 in range(br, br + box):
            for c2 in range(bc, bc + box):
                if (r2, c2) != (r, c):
                    V_minus.add((r2, c2, v))

    V0 = set()
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v in range(1, n + 1):
                triple = (r, c, v)
                if triple not in V_plus and triple not in V_minus:
                    V0.add(triple)

    # Compact mapping: (r,c,v) -> 1-indexed DIMACS variable
    V0_list  = sorted(V0)
    var_map  = {triple: idx + 1 for idx, triple in enumerate(V0_list)}
    num_vars = len(var_map)

    def lit(r, c, v, neg=False):
        """
        Return the DIMACS literal (int), or sentinel string:
          "TRUE"  -> clause is satisfied (skip whole clause)
          "FALSE" -> literal is false    (skip this literal only)
        """
        if (r, c, v) in V_plus:
            return "FALSE" if neg else "TRUE"
        if (r, c, v) in V_minus:
            return "TRUE" if neg else "FALSE"
        idx = var_map[(r, c, v)]
        return -idx if neg else idx

    clauses = []

    def add_clause(literals):
        resolved = []
        for (r, c, v, neg) in literals:
            l = lit(r, c, v, neg)
            if l == "TRUE":
                return
            if l == "FALSE":
                continue
            resolved.append(l)
        if resolved:
            clauses.append(resolved)

    # ── Cell definedness ───────────────────────────────────────────────────────
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            add_clause([(r, c, v, False) for v in range(1, n + 1)])

    # ── Cell uniqueness ────────────────────────────────────────────────────────
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
                cells = [
                    (roffs + dr, coffs + dc)
                    for dr in range(1, box + 1)
                    for dc in range(1, box + 1)
                ]
                for i in range(len(cells)):
                    for j in range(i + 1, len(cells)):
                        r1, c1 = cells[i]
                        r2, c2 = cells[j]
                        add_clause([(r1, c1, v, True), (r2, c2, v, True)])

    return clauses, num_vars, var_map, V0_list


# ── DIMACS writer ──────────────────────────────────────────────────────────────

def write_dimacs(filepath, clauses, num_vars, n, source_file, V0_list, fixed_cells):
    """
    Write DIMACS CNF.

    Extra comment lines for the C solver:
      c SIZE <N>                      — board dimension
      c MAP <dimacs_var> <r> <c> <v> — free-variable mapping
      c FIXED <r> <c> <v>            — pre-assigned cells
    """
    with open(filepath, "w") as f:
        # Standard header
        f.write(f"c Optimised CNF encoding for {n}x{n} Sudoku\n")
        f.write(f"c Source: {os.path.basename(source_file)}\n")
        f.write(f"c Variables: {num_vars}  Clauses: {len(clauses)}\n")

        # Board size (easy to parse)
        f.write(f"c SIZE {n}\n")

        # Variable map: one line per free variable
        # format:  c MAP <var_idx> <row> <col> <val>   (all 1-indexed)
        for idx, (r, c, v) in enumerate(V0_list):
            f.write(f"c MAP {idx + 1} {r} {c} {v}\n")

        # Fixed cells: so the solver can fill them in the grid directly
        # format:  c FIXED <row> <col> <val>
        for (r, c), v in sorted(fixed_cells.items()):
            f.write(f"c FIXED {r} {c} {v}\n")

        # DIMACS problem line
        f.write(f"p cnf {num_vars} {len(clauses)}\n")

        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")


# ── main conversion ────────────────────────────────────────────────────────────

def convert_file(puzzle_path, verbose=True):
    basename = os.path.splitext(os.path.basename(puzzle_path))[0]
    cnf_path = os.path.join(CNF_DIR, basename + ".cnf")

    t0 = time.time()
    n, puzzle = read_puzzle(puzzle_path)

    # Collect fixed cells for the FIXED comments
    fixed_cells = {}
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            v = puzzle[r - 1][c - 1]
            if v != 0:
                fixed_cells[(r, c)] = v

    clauses, num_vars, var_map, V0_list = encode(n, puzzle)
    write_dimacs(cnf_path, clauses, num_vars, n, puzzle_path, V0_list, fixed_cells)
    elapsed = time.time() - t0

    if verbose:
        print(f"  {os.path.basename(puzzle_path)} → {os.path.basename(cnf_path)}")
        print(f"    N={n}  vars={num_vars}  clauses={len(clauses)}  time={elapsed:.3f}s")

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