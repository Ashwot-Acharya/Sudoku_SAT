import math


def bit_width(n):
    if n < 1:
        raise ValueError("Sudoku size must be positive")
    return max(1, math.ceil(math.log2(n)))


def bit_var(r, c, bit, n):
    width = bit_width(n)
    return ((r - 1) * n + (c - 1)) * width + bit + 1


def _value_bits(value, width):
    code = value - 1
    return [(code >> bit) & 1 for bit in range(width)]


def _forbid_code(cell_bits, code, width):
    return [bit if ((code >> index) & 1) == 0 else -bit for index, bit in enumerate(cell_bits)]


def _peer_pairs(n):
    box = math.isqrt(n)
    if box * box != n:
        raise ValueError(f"Sudoku size {n} must have an integral box side")
    pairs = set()

    def add_unit(cells):
        for index, first in enumerate(cells):
            for second in cells[index + 1:]:
                pairs.add(tuple(sorted((first, second))))

    for row in range(1, n + 1):
        add_unit([(row, col) for col in range(1, n + 1)])
    for col in range(1, n + 1):
        add_unit([(row, col) for row in range(1, n + 1)])
    for row in range(1, n + 1, box):
        for col in range(1, n + 1, box):
            add_unit([(row + dr, col + dc) for dr in range(box) for dc in range(box)])
    return sorted(pairs)


def encode_log(n, puzzle):
    if len(puzzle) != n or any(len(row) != n for row in puzzle):
        raise ValueError("Puzzle dimensions do not match Sudoku size")

    width = bit_width(n)
    clauses = []
    num_vars = n * n * width

    # Domain constraints: forbid binary codes >= n (each cell then encodes
    # exactly one value in 1..n, so "at least one" and "at most one" value
    # per cell are implicit).
    for row in range(1, n + 1):
        for col in range(1, n + 1):
            bits = [bit_var(row, col, bit, n) for bit in range(width)]
            for code in range(n, 1 << width):
                clauses.append(_forbid_code(bits, code, width))
            value = puzzle[row - 1][col - 1]
            if value:
                if not 1 <= value <= n:
                    raise ValueError(f"Invalid clue {value} at ({row}, {col})")
                for bit, expected in zip(bits, _value_bits(value, width)):
                    clauses.append([bit if expected else -bit])

    # Pairwise inequality (log-support style, zero auxiliary variables):
    # for each peer pair and each value code, forbid both cells taking that
    # code.  A minterm "cell = code" is negated by the direct clause of its
    # bit literals, so no Tseitin/XOR auxiliaries are needed.
    for (r1, c1), (r2, c2) in _peer_pairs(n):
        bits_a = [bit_var(r1, c1, bit, n) for bit in range(width)]
        bits_b = [bit_var(r2, c2, bit, n) for bit in range(width)]
        for code in range(n):
            clauses.append(
                _forbid_code(bits_a, code, width) + _forbid_code(bits_b, code, width)
            )

    return clauses, num_vars, width


def decode_log_assignment(assignment, puzzle, n):
    width = bit_width(n)
    true_vars = set(assignment)
    grid = [row[:] for row in puzzle]
    for row in range(1, n + 1):
        for col in range(1, n + 1):
            code = sum(
                1 << bit
                for bit in range(width)
                if bit_var(row, col, bit, n) in true_vars
            )
            value = code + 1
            if not 1 <= value <= n:
                raise ValueError(f"Solver produced an out-of-domain value at ({row}, {col})")
            grid[row - 1][col - 1] = value
    return grid


def write_dimacs_log(filepath, clauses, num_vars, n, puzzle):
    width = bit_width(n)
    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write(f"c Logarithmic binary Sudoku CNF encoding for {n}x{n} Sudoku\n")
        handle.write("c ENCODING logarithmic\n")
        handle.write(f"c SIZE {n}\n")
        handle.write(f"c BITS_PER_CELL {width}\n")
        for row in range(1, n + 1):
            for col in range(1, n + 1):
                for bit in range(width):
                    handle.write(f"c BIT {bit_var(row, col, bit, n)} {row} {col} {bit}\n")
                value = puzzle[row - 1][col - 1]
                if value:
                    handle.write(f"c FIXED {row} {col} {value}\n")
        handle.write(f"p cnf {num_vars} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")
