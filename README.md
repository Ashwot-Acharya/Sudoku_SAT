#SAT Based Approach to Solving Sudoku

> Reducing generalized Sudoku to Boolean Satisfiability (SAT) — from constraints to CNF, solved with modern SAT solvers and a custom CDCL implementation.

**Authors**: Ashwat Acharya, Bishesh Bohora, Supreme Chaudhary, Lakki Thapa  
**B.Sc. Computational Mathematics, Kathmandu University (2025)**

---

## 📌 Overview

Sudoku (generalized to an \(n^2 \times n^2\) grid) is NP‑complete. This project encodes the puzzle as a propositional formula in **Conjunctive Normal Form (CNF)** and solves it using SAT solvers. The encoding uses Boolean variables \(x_{i,j,k}\) meaning *cell \((i,j)\) contains digit \(k\)*.

We implement the full pipeline:
- CNF generation (Python)
- Solving via **existing SAT solvers** (PySAT, Satch) and a **custom CDCL solver** (C)
- Performance comparison against **classical backtracking** (MRV + forward checking)

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

The formula \(\phi\) is the conjunction of all clauses above, then simplified.

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

| Grid Size | SAT Solver (ms) | Backtracking (ms) |
|-----------|----------------|-------------------|
| \(4\times4\)  | < 1           | < 1              |
| \(9\times9\)  | ~5            | ~15              |
| \(16\times16\) | ~40          | ~850             |
| \(25\times25\) | ~120         | > 60000          |
| \(36\times36\) | ~450         | > 10 min (fail)  |

> SAT solving scales steadily, remaining under 1 second even for \(36 \times 36\).  
> Backtracking becomes impractical beyond \(16 \times 16\).

**Key insight:** Clause learning, unit propagation, and non‑chronological backjumping allow SAT solvers to prune the search space far more effectively than naive CSP backtracking.

---

## 🚀 How to Run

### Prerequisites

- **Python 3.8+** – required for CNF generation and benchmark scripts
- **Git** – to clone the repository
- **A SAT solver** – the pipeline was tested with `satch` (included in `executable/`), but any DIMACS‑compatible solver (MiniSat, Glucose, PicoSAT) will work
- **MATLAB** (optional) – only needed for the basic CDCL solver implemented in C (source code provided, but compilation is optional)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ashwot-Acharya/Sudoku_SAT
   cd Sudoku_SAT/Main ``` 
2.  Place a SAT solver executable
  The scripts expect a solver named satch inside Main/executable/.
  You can also use any other solver and pass its path via the --solver flag.
  Install Python dependencies (required packages are all in the standard library; only matplotlib is needed for plotting)  
3. install Python dependencies (required packages are all in the standard library; only matplotlib is needed for plotting)
  ```pip install matplotlib ```
4. Lastly run
   ``` python run_pipeline.py ```
6. 
