# SAT Based Approach to Solving Sudoku

> Reducing generalized Sudoku to Boolean Satisfiability (SAT) — from constraints to CNF, solved with modern SAT solvers and a custom CDCL implementation.

**Authors**: Ashwat Acharya, Bishesh Bohora, Supreme Chaudhary, Lakki Thapa  
**B.Sc. Computational Mathematics, Kathmandu University (2025)**

---

## 📌 Overview

Sudoku (generalized to an \(n^2 \times n^2\) grid) is NP‑complete. This project encodes the puzzle as a propositional formula in **Conjunctive Normal Form (CNF)** and solves it using SAT solvers. The encoding uses Boolean variables \(x_{i,j,k}\) meaning *cell \((i,j)\) contains digit \(k\)*.

We implement the full pipeline:
- CNF generation (Python) — `experiment/Main/sudoku_to_cnf.py`
- Solving via **existing SAT solvers** (PySAT, Satch) and a **custom CDCL solver** (C) — `experiment/CDCL/`
- Performance comparison against **classical backtracking** (MRV + forward checking) — `experiment/Main/backtracking_solver.py`

---

## 📁 Repository Structure

```
Sudoku_SAT/
├── README.md                    ← this file (the only file at repo root)
├── LICENSE
├── Paper/
│   ├── report/                  ← LaTeX project report (paper.tex, references.bib, graphs/)
│   └── presentation/            ← LaTeX presentation
├── experiment/
│   ├── Main/                    ← Python pipeline (encoder, solver runner, benchmark, generator)
│   ├── CDCL/                    ← custom CDCL solver in C (cdcl_implementation.c)
│   ├── CNF/                     ← generated DIMACS CNF files
│   ├── Puzzles/                 ← input puzzle .txt files
│   ├── encoder.txt              ← encoding snippet
│   └── decoder.txt              ← decoding snippet
├── Results/
│   ├── benchmark_results.csv    ← the raw benchmark data
│   ├── Sol/                     ← solution files for SAT & backtracking (solved/unsat/timeout)
│   └── *.png                    ← generated plots
└── Analysis/
    ├── analysis.md              ← full multi-agent research analysis & paper roadmap
    └── RESEARCH_ANALYSIS.md
```

---

## 🔧 Encoding – From Sudoku to CNF

All constraints are expressed as clauses:

### 1. Definedness (at least one)
- Each cell: \(\bigvee_{k} x_{i,j,k}\)
- Each row: \(\bigvee_{j} x_{i,j,k}\) for every digit \(k\)
- Each column: \(\bigvee_{i} x_{i,j,k}\)
- Each subgrid: \(\bigvee_{i,j \in \text{block}} x_{i,j,k}\)

### 2. Uniqueness (at most one)
- Cell: \(\neg x_{i,j,k_1} \lor \neg x_{i,j,k_2}\) for \(k_1 \neq k_2\)
- Row: \(\neg x_{i,j_1,k} \lor \neg x_{i,j_2,k}\)
- Column: \(\neg x_{i_1,j,k} \lor \neg x_{i_2,j,k}\)
- Subgrid: similarly for all pairs within a block

### 3. Clues
- Unit clause \(x_{i,j,k}\) for each given clue.

The formula \(\phi\) is the conjunction of all clauses above, then simplified (Kwon & Jain optimized encoding).

---

## 🛠️ Implementation Details

### 🔢 Variable Mapping
Each \((i,j,k)\) is mapped to a unique integer:
\[
V(i,j,k) = (i-1)n^4 + (j-1)n^2 + k
\]
Inverse mapping recovers \((i,j,k)\) from the SAT solver’s satisfying assignment.

### 📄 DIMACS Output
The CNF is written in standard DIMACS format (`.cnf` file).  
Example header: `p cnf <vars> <clauses>`

### 🐍 Python CNF Generator
- Reads puzzle from text file.
- Generates all clauses using the above constraints.
- Outputs DIMACS file ready for any SAT solver.

### ⚙️ Solving
- **PySAT** – used for debugging and validation.
- **Satch** – primary SAT solver for performance tests.
- **Custom CDCL Solver in C** – implements conflict‑driven clause learning with unit propagation, conflict analysis, and non‑chronological backtracking. Works for small/medium puzzles.

### 📊 Comparison with Backtracking
Classical backtracking (MRV heuristic + forward checking) was implemented and tested on the same puzzles.

---

## 📈 Experimental Results

The full benchmark data lives in `Results/benchmark_results.csv` (with per-puzzle solve times, encoding sizes, and status codes). The headline result: SAT solving scales steadily and stays under ~1 s even for \(36 \times 36\) grids, while naive backtracking becomes impractical for large instances.

| Grid Size | SAT Solver | Backtracking |
|-----------|-----------|--------------|
| \(4\times4\)   | < 1 ms   | < 1 ms   |
| \(9\times9\)   | ~5 ms    | ~15 ms   |
| \(16\times16\) | ~40 ms   | competitive |
| \(25\times25\) | ~120 ms  | sometimes times out |
| \(36\times36\) | ~450 ms  | > 10 min (fail) |

> **Note:** See `Results/benchmark_results.csv` for the authoritative per-puzzle measurements.

**Key insight:** Clause learning, unit propagation, and non‑chronological backjumping allow SAT solvers to prune the search space far more effectively than naive CSP backtracking.

---

## 🚀 How to Run

### Prerequisites

- **Python 3.8+** – required for CNF generation and benchmark scripts
- **Git** – to clone the repository
- **A SAT solver** – the pipeline was tested with `satch` (included in `experiment/Main/executable/`), but any DIMACS‑compatible solver (MiniSat, Glucose, PicoSAT) will work
- **matplotlib** – only needed for plotting (`pip install matplotlib`)
- **GCC** (optional) – only needed to compile the basic CDCL solver in C

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ashwot-Acharya/Sudoku_SAT
   cd Sudoku_SAT/experiment/Main
   ```

2. **Place a SAT solver executable**
   The scripts expect a solver named `satch` inside `experiment/Main/executable/`.
   You can also use any other solver and pass its path via the `--solver` flag.

3. **Install Python dependencies**
   (required packages are all in the standard library; only matplotlib is needed for plotting)
   ```bash
   pip install matplotlib
   ```

4. **Run**
   ```bash
   python run_pipeline.py
   ```

### Optional: Compile the CDCL solver

```bash
cd ../../experiment/CDCL
gcc -O2 cdcl_implementation.c -o cdcl_solver
./cdcl_solver ../../experiment/CNF/sudoku_9x9_001.cnf
```