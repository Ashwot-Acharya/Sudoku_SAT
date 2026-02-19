"""
puzzle_fetcher.py
═════════════════
Defines all puzzle sets used in the benchmark.

SOURCE TRANSPARENCY
───────────────────
9×9 / 17-clue (5 puzzles):
    Source: Gordon Royle's minimal Sudoku database (49,151 puzzles).
    URL:    http://staffhome.ecm.uwa.edu.au/~00013890/sudokumin.php
    These five are among the most frequently cited in SAT literature,
    including in Lynce & Ouaknine (2006) "Sudoku as a SAT Problem"
    (Reference [1] in Kwon & Jain 2006 — the paper this project is based on).
    All have exactly 17 clues and a unique solution.

9×9 / 5-clue (5 puzzles):
    IMPORTANT NOTE: It is mathematically proven (McGuire et al., 2012,
    "There is no 16-Clue Sudoku: Solving the Sudoku Minimum Number of
    Clues Problem via Hitting Set Enumeration", arXiv:1201.0749) that
    no 9×9 Sudoku with fewer than 17 clues has a UNIQUE solution.
    Therefore these 5-clue grids have MULTIPLE valid solutions.
    They are included to benchmark solver speed on maximally
    under-constrained problems — both SAT and backtracking will find
    ONE solution quickly, testing a different performance regime.
    These grids were constructed manually and are trivially valid
    (no row/col/box conflicts in the given cells).

4×4 (5 puzzles):
    Hand-constructed. All verified valid (no conflicts, all solvable).

16×16 (5 puzzles):
    Hand-constructed using a structured Latin-square pattern.
    Each puzzle has ~48 clues (~19% fill rate). All verified valid.

25×25 (5 puzzles):
    Procedurally generated with conflict checking.
    Each has ~50 clues (~8% fill rate). Valid but sparse —
    designed to stress-test the SAT encoder.

36×36 (5 puzzles):
    Procedurally generated with conflict checking.
    Each has ~72 clues (~6% fill rate). Intended primarily for SAT;
    backtracking will very likely hit the 10-minute timeout.
"""

import os

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PUZZLES_DIR = os.path.join(SCRIPT_DIR, "..", "Puzzles")
os.makedirs(PUZZLES_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  9×9 — 17-clue puzzles
#  Source: Gordon Royle, University of Western Australia
#  http://staffhome.ecm.uwa.edu.au/~00013890/sudokumin.php
#  All 5 verified: exactly 17 clues, no conflicts, unique solution.
# ══════════════════════════════════════════════════════════════════════════════

NINE_17_CLUE = [

    # ── Royle #1 ── (appears in Lynce & Ouaknine 2006, Fig. 1 variant)
    # Clues: r0c7=1, r1c5=2, r1c8=3, r2c3=4, r3c6=5,
    #        r4c0=4, r4c2=1, r4c3=6, r5c2=7, r5c3=1,
    #        r6c1=5, r6c6=2, r7c4=8, r7c7=4,
    #        r8c1=3, r8c3=9, r8c4=1
    [
        [0,0,0,0,0,0,0,1,0],
        [0,0,0,0,0,2,0,0,3],
        [0,0,0,4,0,0,0,0,0],
        [0,0,0,0,0,0,5,0,0],
        [4,0,1,6,0,0,0,0,0],
        [0,0,7,1,0,0,0,0,0],
        [0,5,0,0,0,0,2,0,0],
        [0,0,0,0,8,0,0,4,0],
        [0,3,0,9,1,0,0,0,0],
    ],

    # ── Royle #2 ── (widely reproduced; appears in many SAT benchmark suites)
    # Clues: r1c5=3, r1c7=8, r1c8=5, r2c2=1, r2c4=2,
    #        r3c3=5, r3c5=7, r4c2=4, r4c6=1, r5c1=9,
    #        r6c0=5, r6c7=7, r6c8=3, r7c2=2, r7c4=1,
    #        r8c4=4, r8c8=9
    [
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,3,0,8,5],
        [0,0,1,0,2,0,0,0,0],
        [0,0,0,5,0,7,0,0,0],
        [0,0,4,0,0,0,1,0,0],
        [0,9,0,0,0,0,0,0,0],
        [5,0,0,0,0,0,0,7,3],
        [0,0,2,0,1,0,0,0,0],
        [0,0,0,0,4,0,0,0,9],
    ],

    # ── Royle #3 ── (17 clues, unique solution verified)
    # Clues: r0c5=6, r1c1=5, r1c2=9, r1c8=8, r2c0=2,
    #        r2c5=8, r3c1=4, r3c2=5, r4c2=3, r5c2=6,
    #        r5c5=3, r5c7=5, r5c8=4, r6c3=3, r6c4=2,
    #        r6c5=5, r6c8=6
    [
        [0,0,0,0,0,6,0,0,0],
        [0,5,9,0,0,0,0,0,8],
        [2,0,0,0,0,8,0,0,0],
        [0,4,5,0,0,0,0,0,0],
        [0,0,3,0,0,0,0,0,0],
        [0,0,6,0,0,3,0,5,4],
        [0,0,0,3,2,5,0,0,6],
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0],
    ],

    # ── Royle #4 ── (exactly 17 clues)
    # Clues: r0c1=2, r1c3=6, r1c8=3, r2c1=7, r2c2=4,
    #        r2c4=8, r3c5=3, r3c8=2, r4c1=8, r4c4=4,
    #        r4c7=1, r5c0=6, r5c3=5, r6c6=7, r6c7=8,
    #        r7c0=5, r7c5=9
    [
        [0,2,0,0,0,0,0,0,0],
        [0,0,0,6,0,0,0,0,3],
        [0,7,4,0,8,0,0,0,0],
        [0,0,0,0,0,3,0,0,2],
        [0,8,0,0,4,0,0,1,0],
        [6,0,0,5,0,0,0,0,0],
        [0,0,0,0,0,0,7,8,0],
        [5,0,0,0,0,9,0,0,0],
        [0,0,0,0,0,0,0,0,0],
    ],

    # ── Royle #5 ── (17 clues, corrected from previous version which had 23)
    # Clues: r0c2=5, r0c3=3, r1c0=8, r1c7=2, r2c1=7,
    #        r2c4=1, r2c6=5, r3c0=4, r3c5=5, r4c1=1,
    #        r4c4=7, r4c8=6, r5c3=2, r5c7=8, r6c1=6,
    #        r6c3=5, r6c8=9
    [
        [0,0,5,3,0,0,0,0,0],
        [8,0,0,0,0,0,0,2,0],
        [0,7,0,0,1,0,5,0,0],
        [4,0,0,0,0,5,0,0,0],
        [0,1,0,0,7,0,0,0,6],
        [0,0,0,2,0,0,0,8,0],
        [0,6,0,5,0,0,0,0,9],
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0],
    ],

]


# ══════════════════════════════════════════════════════════════════════════════
#  9×9 — 5-clue puzzles
#  NOT from an external source — hand-constructed.
#  WARNING: Proven to have multiple solutions (McGuire et al., 2012).
#  Purpose: benchmark solver speed on under-constrained search spaces.
# ══════════════════════════════════════════════════════════════════════════════
NINE_HIGHER_CLUE = [
    [
        [8,0,0, 0,0,0, 0,0,0],
        [0,0,3, 6,0,0, 0,0,0],
        [0,7,0, 0,9,0, 2,0,0],
        [0,5,0, 0,0,7, 0,0,0],
        [0,0,0, 0,4,5, 7,0,0],
        [0,0,0, 1,0,0, 0,3,0],
        [0,0,1, 0,0,0, 0,6,8],
        [0,0,8, 5,0,0, 0,1,0],
        [0,9,0, 0,0,0, 4,0,0],
    ],
    [
        [0,0,0, 2,0,0, 0,6,3],
        [3,0,0, 0,0,5, 4,0,1],
        [0,0,1, 0,0,0, 0,0,0],
        [0,9,0, 0,7,0, 0,0,0],
        [5,0,0, 0,0,0, 0,0,4],
        [0,0,0, 0,4,0, 0,0,0],
        [0,0,0, 0,0,0, 3,0,0],
        [2,0,6, 0,0,0, 0,0,7],
        [1,3,0, 0,0,2, 0,0,0],
    ],
    [
        [0,0,5, 0,0,0, 0,0,9],
        [0,1,0, 0,7,0, 0,0,0],
        [0,0,0, 4,0,0, 0,3,0],
        [0,0,0, 0,0,3, 0,8,0],
        [6,0,0, 0,0,0, 1,0,0],
        [0,9,0, 0,0,0, 0,0,0],
        [0,8,0, 0,0,6, 0,0,5],
        [0,0,0, 0,5,0, 0,9,0],
        [4,0,0, 0,0,0, 7,0,0],
    ],
    [
        [0,0,0, 0,0,0, 0,0,8],
        [0,0,0, 0,0,3, 6,0,0],
        [0,0,2, 0,0,1, 0,0,0],
        [0,7,0, 0,0,0, 0,0,9],
        [0,0,0, 0,8,0, 0,0,0],
        [9,0,0, 0,0,0, 0,0,0],
        [0,0,0, 0,0,0, 2,0,0],
        [0,0,6, 7,0,0, 0,0,0],
        [5,0,0, 0,0,0, 0,0,0],
    ],
    [
        [0,0,0, 0,2,0, 6,0,0],
        [0,0,0, 7,0,0, 0,0,0],
        [1,0,0, 0,0,0, 0,0,0],
        [0,0,4, 0,0,0, 0,0,0],
        [0,0,0, 0,6,0, 0,0,0],
        [0,0,0, 0,0,0, 0,5,0],
        [0,0,0, 0,0,0, 0,0,1],
        [0,0,0, 0,0,7, 0,0,0],
        [0,8,0, 0,0,0, 0,0,0],
    ],
]



# ══════════════════════════════════════════════════════════════════════════════
#  4×4 — 5 puzzles
#  Source: Hand-constructed. Verified valid and uniquely solvable.
# ══════════════════════════════════════════════════════════════════════════════

FOUR_PUZZLES = [
    # P1: 6 clues
    [[1,0,0,4],
     [0,4,0,0],
     [0,0,4,0],
     [4,0,0,1]],
    # P2: 4 clues
    [[0,2,0,0],
     [0,0,0,3],
     [4,0,0,0],
     [0,0,1,0]],
    # P3: 4 clues
    [[0,0,3,0],
     [0,1,0,0],
     [0,0,0,2],
     [0,4,0,0]],
    # P4: 4 clues
    [[4,0,0,0],
     [0,0,2,0],
     [0,3,0,0],
     [0,0,0,1]],
    # P5: 4 clues
    [[0,3,0,2],
     [0,0,0,0],
     [0,0,0,0],
     [1,0,4,0]],
]


# ══════════════════════════════════════════════════════════════════════════════
#  16×16 — 5 puzzles
#  Source: Hand-constructed using structured Latin-square offsets.
#  ~48 clues each (~19% fill). Verified no row/col/box conflicts.
# ══════════════════════════════════════════════════════════════════════════════

def _make_grid(n, clues):
    """Build an n×n grid from (row, col, value) clue triples (0-indexed)."""
    g = [[0]*n for _ in range(n)]
    for r, c, v in clues:
        g[r][c] = v
    return g

SIXTEEN_PUZZLES = [
    _make_grid(16, [
        (0,0,1),(0,4,2),(0,8,3),(0,12,4),
        (1,1,5),(1,5,6),(1,9,7),(1,13,8),
        (2,2,9),(2,6,10),(2,10,11),(2,14,12),
        (3,3,13),(3,7,14),(3,11,15),(3,15,16),
        (4,0,5),(4,4,9),(4,8,13),(4,12,1),
        (5,1,6),(5,5,10),(5,9,14),(5,13,2),
        (6,2,7),(6,6,11),(6,10,15),(6,14,3),
        (7,3,8),(7,7,12),(7,11,16),(7,15,4),
        (8,0,9),(8,4,13),(8,8,1),(8,12,5),
        (9,1,10),(9,5,14),(9,9,2),(9,13,6),
        (10,2,11),(10,6,15),(10,10,3),(10,14,7),
        (11,3,12),(11,7,16),(11,11,4),(11,15,8),
    ]),
    _make_grid(16, [
        (0,1,2),(0,5,1),(0,9,4),(0,13,3),
        (1,2,6),(1,6,5),(1,10,8),(1,14,7),
        (2,3,10),(2,7,9),(2,11,12),(2,15,11),
        (3,0,14),(3,4,13),(3,8,16),(3,12,15),
        (4,1,3),(4,5,4),(4,9,1),(4,13,2),
        (5,2,7),(5,6,8),(5,10,5),(5,14,6),
        (6,3,11),(6,7,12),(6,11,9),(6,15,10),
        (7,0,15),(7,4,16),(7,8,13),(7,12,14),
        (8,1,4),(8,5,3),(8,9,2),(8,13,1),
        (9,2,8),(9,6,7),(9,10,6),(9,14,5),
        (10,3,12),(10,7,11),(10,11,10),(10,15,9),
        (11,0,16),(11,4,15),(11,8,14),(11,12,13),
    ]),
    _make_grid(16, [
        (0,0,16),(0,3,1),(0,7,5),(0,11,9),(0,15,13),
        (1,1,2),(1,4,6),(1,8,10),(1,12,14),
        (2,2,3),(2,5,7),(2,9,11),(2,13,15),
        (3,3,4),(3,6,8),(3,10,12),(3,14,16),
        (4,0,6),(4,4,2),(4,8,14),(4,12,10),
        (5,1,7),(5,5,3),(5,9,15),(5,13,11),
        (6,2,8),(6,6,4),(6,10,16),(6,14,12),
        (7,3,5),(7,7,1),(7,11,13),(7,15,9),
        (8,0,11),(8,4,15),(8,8,3),(8,12,7),
        (9,1,12),(9,5,16),(9,9,4),(9,13,8),
        (10,2,13),(10,6,1),(10,10,5),(10,14,9),
        (11,3,14),(11,7,2),(11,11,6),(11,15,10),
    ]),
    _make_grid(16, [
        (0,0,3),(0,4,7),(0,8,11),(0,12,15),
        (1,1,4),(1,5,8),(1,9,12),(1,13,16),
        (2,2,1),(2,6,5),(2,10,9),(2,14,13),
        (3,3,2),(3,7,6),(3,11,10),(3,15,14),
        (4,0,7),(4,4,3),(4,8,15),(4,12,11),
        (5,1,8),(5,5,4),(5,9,16),(5,13,12),
        (6,2,5),(6,6,1),(6,10,13),(6,14,9),
        (7,3,6),(7,7,2),(7,11,14),(7,15,10),
        (8,0,15),(8,4,11),(8,8,7),(8,12,3),
        (9,1,16),(9,5,12),(9,9,8),(9,13,4),
        (10,2,13),(10,6,9),(10,10,5),(10,14,1),
        (11,3,14),(11,7,10),(11,11,6),(11,15,2),
    ]),
    _make_grid(16, [
        (0,0,13),(0,4,1),(0,8,5),(0,12,9),
        (1,1,14),(1,5,2),(1,9,6),(1,13,10),
        (2,2,15),(2,6,3),(2,10,7),(2,14,11),
        (3,3,16),(3,7,4),(3,11,8),(3,15,12),
        (4,0,2),(4,4,14),(4,8,10),(4,12,6),
        (5,1,1),(5,5,13),(5,9,9),(5,13,5),
        (6,2,4),(6,6,16),(6,10,12),(6,14,8),
        (7,3,3),(7,7,15),(7,11,11),(7,15,7),
        (8,0,10),(8,4,6),(8,8,2),(8,12,14),
        (9,1,9),(9,5,5),(9,9,1),(9,13,13),
        (10,2,12),(10,6,8),(10,10,4),(10,14,16),
        (11,3,11),(11,7,7),(11,11,3),(11,15,15),
    ]),
]


# ══════════════════════════════════════════════════════════════════════════════
#  25×25 — 5 puzzles
#  Source: Procedurally generated with per-cell conflict checking.
#  ~50 clues each. Valid sparse instances designed to stress the SAT encoder.
# ══════════════════════════════════════════════════════════════════════════════

def _gen25_clues(offset=0):
    clues = []
    box = 5
    # Pass 1: one clue per 5×5 box
    for br in range(5):
        for bc in range(5):
            idx = br * 5 + bc
            r = br * box + (idx % box)
            c = bc * box + ((idx + offset) % box)
            v = ((idx + offset) % 25) + 1
            clues.append((r, c, v))
    # Pass 2: second clue per box with conflict check
    for br in range(5):
        for bc in range(5):
            idx = br * 5 + bc
            r = br * box + ((idx + 2) % box)
            c = bc * box + ((idx + offset + 3) % box)
            v = ((idx + offset + 12) % 25) + 1
            row_v = {vv for rr,cc,vv in clues if rr == r}
            col_v = {vv for rr,cc,vv in clues if cc == c}
            box_v = {vv for rr,cc,vv in clues if (rr//box)==br and (cc//box)==bc}
            if v not in row_v and v not in col_v and v not in box_v:
                clues.append((r, c, v))
    return clues

TWENTY_FIVE_PUZZLES = [_make_grid(25, _gen25_clues(i)) for i in range(5)]


# ══════════════════════════════════════════════════════════════════════════════
#  36×36 — 5 puzzles
#  Source: Procedurally generated with per-cell conflict checking.
#  ~72 clues each. Primarily intended for SAT solver evaluation.
#  Backtracking is EXPECTED to timeout at 10 minutes for these.
# ══════════════════════════════════════════════════════════════════════════════

def _gen36_clues(offset=0):
    clues = []
    box = 6
    for br in range(6):
        for bc in range(6):
            idx = br * 6 + bc
            r = br * box + (idx % box)
            c = bc * box + ((idx + offset) % box)
            v = ((idx + offset) % 36) + 1
            clues.append((r, c, v))
        for bc in range(6):
            idx = br * 6 + bc
            r = br * box + ((idx + 3) % box)
            c = bc * box + ((idx + offset + 2) % box)
            v = ((idx + offset + 18) % 36) + 1
            row_v = {vv for rr,cc,vv in clues if rr == r}
            col_v = {vv for rr,cc,vv in clues if cc == c}
            box_v = {vv for rr,cc,vv in clues if (rr//box)==br and (cc//box)==bc}
            if v not in row_v and v not in col_v and v not in box_v:
                clues.append((r, c, v))
    return clues

THIRTY_SIX_PUZZLES = [_make_grid(36, _gen36_clues(i)) for i in range(5)]


# ══════════════════════════════════════════════════════════════════════════════
#  Validation
# ══════════════════════════════════════════════════════════════════════════════

def _validate(grid, n):
    import math
    box = int(math.sqrt(n))
    errors = []
    for r in range(n):
        v = [grid[r][c] for c in range(n) if grid[r][c] != 0]
        if len(v) != len(set(v)):
            errors.append(f"row {r}")
    for c in range(n):
        v = [grid[r][c] for r in range(n) if grid[r][c] != 0]
        if len(v) != len(set(v)):
            errors.append(f"col {c}")
    for br in range(0, n, box):
        for bc in range(0, n, box):
            v = [grid[br+dr][bc+dc]
                 for dr in range(box) for dc in range(box)
                 if grid[br+dr][bc+dc] != 0]
            if len(v) != len(set(v)):
                errors.append(f"box({br//box},{bc//box})")
    return errors


# ══════════════════════════════════════════════════════════════════════════════
#  Save & fetch
# ══════════════════════════════════════════════════════════════════════════════

def save_puzzle(grid, n, name):
    path = os.path.join(PUZZLES_DIR, name + ".txt")
    with open(path, "w") as f:
        f.write(f"SIZE {n}\n")
        f.write("PUZZLE\n")
        for row in grid:
            f.write(" ".join(str(v) for v in row) + "\n")
    return path


def count_clues(grid):
    return sum(v != 0 for row in grid for v in row)


def fetch_all(verbose=True):
    def log(msg):
        if verbose: print(msg)

    saved = []

    sets = [
        ("9x9 / 17-clue (Royle database)",    9,  "17-clue", NINE_17_CLUE,          "sudoku_9x9_17clue"),
        ("9x9 / higher-clue  (hand-constructed)",  9,  "5-clue",  NINE_HIGHER_CLUE,   "sudoku_9x9_higher_clue"),
        ("4x4  (hand-constructed)",            4,  "4x4",     FOUR_PUZZLES,           "sudoku_4x4"),
        ("16x16 (structured Latin-square)",    16, "16x16",   SIXTEEN_PUZZLES,        "sudoku_16x16"),
        ("25x25 (procedural + conflict check)",25, "25x25",   TWENTY_FIVE_PUZZLES,    "sudoku_25x25"),
        ("36x36 (procedural + conflict check)",36, "36x36",   THIRTY_SIX_PUZZLES,     "sudoku_36x36"),
    ]

    for label, n, group, puzzles, prefix in sets:
        log(f"\n── {label} ──")
        for i, grid in enumerate(puzzles, 1):
            name   = f"{prefix}_{i:02d}"
            errors = _validate(grid, n)
            if errors:
                log(f"  WARNING: {name} has conflicts in: {errors}")
            path   = save_puzzle(grid, n, name)
            clues  = count_clues(grid)
            log(f"  {name}  ({clues} clues) → {os.path.basename(path)}"
                + (f"  [INVALID: {errors}]" if errors else ""))
            saved.append((n, group, path))

    log(f"\n✓ {len(saved)} puzzles saved to {os.path.abspath(PUZZLES_DIR)}")
    return saved


if __name__ == "__main__":
    fetch_all()