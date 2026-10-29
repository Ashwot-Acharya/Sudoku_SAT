"""Back-circulant Sudoku puzzle generator for square sizes up to 49x49."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
import random
import statistics
import sys
import time

DEFAULT_SIZES = (4, 9, 16, 25, 36, 49)
DEFAULT_SOLVER = "/usr/sbin/cadical"
MAIN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Main")


def _base_size(n: int) -> int:
    base = math.isqrt(n)
    if base * base != n:
        raise ValueError(f"n={n} is not a perfect square")
    return base


def _canonical_solution(n: int) -> list[list[int]]:
    base = _base_size(n)
    half = (n - 1) // 2
    first_row = list(range(1, half + 1)) + list(range(n, half, -1))
    grid: list[list[int]] = []
    for r in range(n):
        band, position = divmod(r, base)
        shift = band + base * position
        grid.append([first_row[(c + shift) % n] for c in range(n)])
    return grid


def _canonical_clues(n: int) -> list[list[int]]:
    base = _base_size(n)
    half = (n - 1) // 2
    clues = [[0] * n for _ in range(n)]
    for r in range(n):
        band, position = divmod(r, base)
        shift = band + base * position
        if shift < half:
            for c in range(half - shift):
                clues[r][c] = 1 + shift + c
        elif shift > half:
            count = shift - half
            for c in range(n - count, n):
                clues[r][c] = n - (c - (n - count))
    return clues


def _random_symmetry(
    n: int, rng: random.Random
) -> tuple[list[int], list[int], list[int], bool]:
    base = _base_size(n)
    bands = list(range(base))
    rng.shuffle(bands)
    row_order: list[int] = []
    for band in bands:
        rows = [band * base + offset for offset in range(base)]
        rng.shuffle(rows)
        row_order.extend(rows)

    stacks = list(range(base))
    rng.shuffle(stacks)
    column_order: list[int] = []
    for stack in stacks:
        columns = [stack * base + offset for offset in range(base)]
        rng.shuffle(columns)
        column_order.extend(columns)

    symbols = list(range(1, n + 1))
    rng.shuffle(symbols)
    symbol_map = [0] + symbols

    return row_order, column_order, symbol_map, rng.random() < 0.5


def _apply_symmetry(
    grid: list[list[int]],
    row_order: list[int],
    column_order: list[int],
    symbol_map: list[int],
    transpose: bool,
) -> list[list[int]]:
    n = len(grid)
    result = [
        [symbol_map[grid[row_order[r]][column_order[c]]] for c in range(n)]
        for r in range(n)
    ]
    if transpose:
        result = [list(row) for row in zip(*result)]
    return result


def validate_solution(grid: list[list[int]], n: int) -> bool:
    base = _base_size(n)
    if len(grid) != n or any(len(row) != n for row in grid):
        return False
    expected = set(range(1, n + 1))
    if any(set(row) != expected for row in grid):
        return False
    if any({grid[r][c] for r in range(n)} != expected for c in range(n)):
        return False
    for br in range(0, n, base):
        for bc in range(0, n, base):
            block = {
                grid[br + r][bc + c]
                for r in range(base)
                for c in range(base)
            }
            if block != expected:
                return False
    return True


def validate_partial(grid: list[list[int]], n: int) -> bool:
    base = _base_size(n)
    expected = set(range(1, n + 1))
    allowed = expected | {0}
    if len(grid) != n or any(len(row) != n for row in grid):
        return False
    if any(not set(row) <= allowed for row in grid):
        return False
    for row in grid:
        values = [value for value in row if value]
        if len(values) != len(set(values)):
            return False
    for c in range(n):
        values = [grid[r][c] for r in range(n) if grid[r][c]]
        if len(values) != len(set(values)):
            return False
    for br in range(0, n, base):
        for bc in range(0, n, base):
            values = [
                grid[br + r][bc + c]
                for r in range(base)
                for c in range(base)
                if grid[br + r][bc + c]
            ]
            if len(values) != len(set(values)):
                return False
    return True


def _grid_hash(grid: list[list[int]]) -> str:
    payload = "\n".join(",".join(map(str, row)) for row in grid)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()[:16]


def generate_back_circulant_puzzle(
    n: int, seed: int | None = None
) -> tuple[list[list[int]], list[list[int]], dict]:
    base = _base_size(n)
    started = time.perf_counter()
    rng = random.Random(seed)

    solution = _canonical_solution(n)
    puzzle = _canonical_clues(n)
    row_order, column_order, symbol_map, transpose = _random_symmetry(n, rng)
    solution = _apply_symmetry(solution, row_order, column_order, symbol_map, transpose)
    puzzle = _apply_symmetry(puzzle, row_order, column_order, symbol_map, transpose)

    elapsed = time.perf_counter() - started
    clue_count = sum(value != 0 for row in puzzle for value in row)
    consistent = all(
        puzzle[r][c] == 0 or puzzle[r][c] == solution[r][c]
        for r in range(n)
        for c in range(n)
    )
    metadata = {
        "n": n,
        "base": base,
        "seed": seed,
        "clue_count": clue_count,
        "fill_pct": 100.0 * clue_count / (n * n),
        "transposed": transpose,
        "generation_time_s": elapsed,
        "puzzle_hash": _grid_hash(puzzle),
        "solution_hash": _grid_hash(solution),
        "valid": validate_solution(solution, n)
        and validate_partial(puzzle, n)
        and consistent
        and clue_count == (n * n) // 4,
        "choices": {
            "row_order": list(row_order),
            "column_order": list(column_order),
            "symbol_map": list(symbol_map),
            "transpose": bool(transpose),
        },
    }
    return puzzle, solution, metadata


def generate_back_circulant_solution(
    n: int, seed: int | None = None
) -> tuple[list[list[int]], dict]:
    _, solution, metadata = generate_back_circulant_puzzle(n, seed=seed)
    return solution, metadata


def _load_uniqueness_checker():
    if MAIN_DIR not in sys.path:
        sys.path.insert(0, MAIN_DIR)
    from uniqueness import sat_blocking_check

    return sat_blocking_check


def _parse_args() -> argparse.Namespace:
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(
        description="Generate randomized back-circulant Sudoku puzzles and solutions."
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=list(DEFAULT_SIZES),
        help="square sizes to generate (default: 4 9 16 25 36 49)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="puzzles per size (default: 10)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="master seed for reproducible runs (default: random each run)",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(here, "results"),
        help="directory for the CSV and saved puzzles (default: results/)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="write each puzzle and solution in the project puzzle file format",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="print the first generated puzzle and solution for each size",
    )
    parser.add_argument(
        "--verify-unique",
        action="store_true",
        help="verify uniqueness of every puzzle with CaDiCaL",
    )
    parser.add_argument(
        "--solver",
        default=DEFAULT_SOLVER,
        help=f"SAT solver path for uniqueness checks (default: {DEFAULT_SOLVER})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="per-uniqueness-check timeout in seconds (default: 120)",
    )
    return parser.parse_args()


def _format_grid(grid: list[list[int]]) -> str:
    width = max(len(str(value)) if value else 1 for row in grid for value in row)
    return "\n".join(
        " ".join((f"{value:>{width}}" if value else ".".rjust(width)) for value in row)
        for row in grid
    )


def _save_puzzle(
    path: str, puzzle: list[list[int]], solution: list[list[int]], n: int
) -> None:
    puzzle_body = "\n".join(" ".join(map(str, row)) for row in puzzle)
    solution_body = "\n".join(" ".join(map(str, row)) for row in solution)
    with open(path, "w", encoding="ascii") as handle:
        handle.write(f"SIZE {n}\nPUZZLE\n{puzzle_body}\nSOLUTION\n{solution_body}\n")


def main() -> None:
    args = _parse_args()
    if args.count < 1:
        raise SystemExit("--count must be at least 1")
    if args.verify_unique and not os.path.exists(args.solver):
        raise SystemExit(f"solver not found: {args.solver}")

    os.makedirs(args.out, exist_ok=True)
    puzzles_dir = os.path.join(args.out, "puzzles")
    if args.save:
        os.makedirs(puzzles_dir, exist_ok=True)

    checker = _load_uniqueness_checker() if args.verify_unique else None
    master = random.Random(args.seed) if args.seed is not None else None
    system = random.SystemRandom()
    rows: list[dict] = []

    print(
        f"{'n':>4} {'base':>4} {'count':>5} {'mean ms':>9} {'min ms':>8} "
        f"{'max ms':>8} {'clues':>6} {'fill%':>6} {'distinct':>8} "
        f"{'valid':>5} {'unique':>6}"
    )
    for n in args.sizes:
        base = _base_size(n)
        times: list[float] = []
        hashes: set[str] = set()
        valid_count = 0
        unique_count = 0
        for index in range(1, args.count + 1):
            seed = master.randrange(2**32) if master is not None else system.randrange(2**32)
            puzzle, solution, metadata = generate_back_circulant_puzzle(n, seed=seed)
            times.append(metadata["generation_time_s"])
            hashes.add(metadata["puzzle_hash"])
            valid_count += int(metadata["valid"])

            unique = ""
            verification_time = ""
            if checker is not None:
                result = checker(
                    puzzle,
                    n,
                    solver_path=args.solver,
                    timeout=args.timeout,
                )
                unique = int(result["unique"])
                unique_count += unique
                verification_time = f"{result['time_s']:.6f}"

            rows.append(
                {
                    "n": n,
                    "base": base,
                    "index": index,
                    "seed": seed,
                    "clue_count": metadata["clue_count"],
                    "fill_pct": f"{metadata['fill_pct']:.4f}",
                    "transposed": int(metadata["transposed"]),
                    "generation_time_s": f"{metadata['generation_time_s']:.9f}",
                    "puzzle_hash": metadata["puzzle_hash"],
                    "solution_hash": metadata["solution_hash"],
                    "valid": int(metadata["valid"]),
                    "unique": unique,
                    "verification_time_s": verification_time,
                }
            )

            if args.save:
                path = os.path.join(puzzles_dir, f"sudoku_{n}x{n}_back_circulant_seed{seed}_{index:02d}.txt")
                _save_puzzle(path, puzzle, solution, n)
            if args.show and index == 1:
                print(f"\n{n}x{n} puzzle:")
                print(_format_grid(puzzle))
                print(f"{n}x{n} solution:")
                print(_format_grid(solution))
                print()

        unique_display = str(unique_count) if checker is not None else "-"
        print(
            f"{n:>4} {base:>4} {args.count:>5} "
            f"{statistics.mean(times) * 1000:>9.3f} {min(times) * 1000:>8.3f} "
            f"{max(times) * 1000:>8.3f} {metadata['clue_count']:>6} "
            f"{metadata['fill_pct']:>6.2f} {len(hashes):>8} "
            f"{valid_count:>5} {unique_display:>6}"
        )

    csv_path = os.path.join(args.out, "back_circulant_timing.csv")
    with open(csv_path, "w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwrote {csv_path}")


if __name__ == "__main__":
    main()
