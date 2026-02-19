"""
optimized_sudoku_generator.py
Fast Sudoku generator for 4x4 up to 36x36 (perfect square sizes).
Uses deterministic base pattern + random permutations.
"""

import random
import math
import os
import argparse
import time

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PUZZLES_DIR = os.path.join(SCRIPT_DIR, "..", "Puzzles")
os.makedirs(PUZZLES_DIR, exist_ok=True)

VALID_SIZES = [4, 9, 16, 25, 36]


# ───────────────────────────────────────────────────────────────
# 1. BASE PATTERN CONSTRUCTION (O(n²))
# ───────────────────────────────────────────────────────────────

def pattern(r, c, base, side):
    return (base * (r % base) + r // base + c) % side


def shuffle(s):
    return random.sample(s, len(s))


def generate_solution(n):
    """
    Generate a full valid Sudoku solution instantly.
    """
    base = int(math.sqrt(n))
    side = n

    rows  = [g * base + r for g in shuffle(range(base)) for r in shuffle(range(base))]
    cols  = [g * base + c for g in shuffle(range(base)) for c in shuffle(range(base))]
    nums  = shuffle(range(1, side + 1))

    grid = [
        [nums[pattern(r, c, base, side)] for c in cols]
        for r in rows
    ]

    return grid


# ───────────────────────────────────────────────────────────────
# 2. REMOVE CELLS
# ───────────────────────────────────────────────────────────────

def remove_cells(grid, n, num_clues):
    puzzle = [row[:] for row in grid]
    cells  = [(r, c) for r in range(n) for c in range(n)]
    random.shuffle(cells)

    for r, c in cells[: n * n - num_clues]:
        puzzle[r][c] = 0

    return puzzle


def default_clues(n):
    clue_map = {
        4: 8,
        9: 30,
        16: 90,
        25: 220,
        36: 500,
    }
    return clue_map.get(n, int(n * n * 0.4))


# ───────────────────────────────────────────────────────────────
# 3. SAVE
# ───────────────────────────────────────────────────────────────

def save_puzzle(puzzle, solution, n, puzzle_id):
    filename = os.path.join(
        PUZZLES_DIR,
        f"sudoku_{n}x{n}_{puzzle_id:03d}.txt"
    )

    with open(filename, "w") as f:
        f.write(f"SIZE {n}\n")
        f.write("PUZZLE\n")
        for row in puzzle:
            f.write(" ".join(str(v) for v in row) + "\n")
        f.write("SOLUTION\n")
        for row in solution:
            f.write(" ".join(str(v) for v in row) + "\n")

    return filename


# ───────────────────────────────────────────────────────────────
# 4. DRIVER
# ───────────────────────────────────────────────────────────────

def generate_puzzles_for_size(n, count=1, seed=None):
    if n not in VALID_SIZES:
        raise ValueError(f"Size {n} not supported.")

    if seed is not None:
        random.seed(seed)

    clues = default_clues(n)
    saved = []

    for i in range(count):
        print(f"Generating {n}x{n} puzzle {i+1}/{count}...", end=" ", flush=True)
        t0 = time.time()

        solution = generate_solution(n)
        puzzle   = remove_cells(solution, n, clues)

        fname = save_puzzle(puzzle, solution, n, i + 1)
        print(f"done ({time.time()-t0:.2f}s)")

        saved.append(fname)

    return saved


def main():
    parser = argparse.ArgumentParser(description="Optimized Sudoku Generator")
    parser.add_argument("--sizes", nargs="+", type=int, default=VALID_SIZES)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    for size in args.sizes:
        print(f"\n── {size}x{size} ──")
        generate_puzzles_for_size(size, args.count, args.seed)

    print("\nSaved to:", os.path.abspath(PUZZLES_DIR))


if __name__ == "__main__":
    main()
