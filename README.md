# SAT-Based Approach to Solving Generalized Sudoku ($n^2 \times n^2$)

> Reducing generalized Sudoku to Boolean Satisfiability (SAT) — from theoretical ASP-completeness to dual CNF encodings, uniqueness verification theorems, non-parametric statistical hypothesis testing, and empirical evaluation against CSP backtracking.

**Authors**: Ashwat Acharya, Bishesh Bohora, Supreme Chaudhary, Lakki Thapa  
**B.Sc. Computational Mathematics, Kathmandu University (2025)**

---

## 📌 Overview & Theoretical Foundations

Sudoku generalized to an $n^2 \times n^2$ grid is **NP-complete** (Yato & Seta, 2003). Furthermore, the **Another Solution Problem (ASP)** — deciding whether a given Sudoku puzzle has a second distinct solution — is **ASP-complete** under parsimonious reduction. This implies that uniqueness verification is inherently NP-hard, and counting Sudoku solutions is **#P-complete**.

This project presents a rigorous, reproducible framework for:
1. **Uniqueness Verification**: Implementing 4 distinct verification paradigms (SAT blocking clause, Unavoidable Sets, Deducibility Theorem, Solution Validation).
2. **Dual CNF Encodings**: Comparing Naive Full Encoding ($\phi$, $O(n^3)$ variables) against Kwon & Jain's Compact Optimized Encoding ($\phi'$, variable pruning via fixed-cell propagation).
3. **Procedural Dataset Generation & Benchmark**: Seed-controlled generator supporting sizes up to $64 \times 64$, curating Gordon Royle's 17-clue 9×9 minimum-clue dataset alongside procedurally generated instances.
4. **Non-Parametric Statistical Suite**: Applying Friedman rank-sum tests, Wilcoxon signed-rank tests, Kendall's W, and rank-biserial effect sizes to evaluate solver scaling and encoding performance.

---

## 📁 Repository Structure

```
Sudoku_SAT/
├── README.md                    ← this file
├── LICENSE
├── Paper/
│   ├── report/                  ← LaTeX project report (paper.tex, references.bib, graphs/)
│   └── presentation/            ← LaTeX presentation
├── experiment/
│   ├── Main/                    ← Complete Python benchmarking and verification pipeline
│   │   ├── unified_benchmark.py ← Main CLI orchestrator
│   │   ├── uniqueness.py        ← Uniqueness verification (SAT blocking, unavoidable sets, deducibility)
│   │   ├── puzzle_manager.py    ← Seed-based generator & Gordon Royle 17-clue dataset manager
│   │   ├── dual_encoder.py      ← Dual CNF encoder (Naive φ vs Compact φ')
│   │   ├── statistical_analysis.py ← Non-parametric hypothesis testing (Friedman, Wilcoxon, effect sizes)
│   │   ├── sudoku_to_cnf.py     ← Compact CNF encoder (Kwon & Jain)
│   │   ├── sat_solver_runner.py ← Subprocess wrapper for external SAT solvers (satch, minisat)
│   │   ├── backtracking_solver.py ← MRV + Degree + Forward Checking CSP solver
│   │   ├── plot_results.py      ← Plotting suite (14 PNG visualization types)
│   │   └── executable/          ← External SAT solver binaries (satch)
│   ├── CDCL/                    ← Custom CDCL solver in C (cdcl_implementation.c)
│   ├── CNF/                     ← Generated DIMACS CNF files
│   ├── Puzzles/                 ← Generated/curated input puzzle .txt files
│   ├── encoder.txt              ← Encoding specification snippet
│   └── decoder.txt              ← Decoding specification snippet
├── Results/
│   ├── benchmark_results.csv    ← Raw empirical data (75 benchmark runs across 3 repeats)
│   ├── STATISTICAL_ANALYSIS.md  ← Full statistical report with hypothesis tests & effect sizes
│   ├── Sol/                     ← Decoded solution grids for all solver runs
│   └── *.png                    ← Generated visualization plots
└── Analysis/
    ├── analysis.md              ← Comprehensive multi-agent research analysis
    └── RESEARCH_ANALYSIS.md     ← Synthesizer meta-analysis
```

---

## 🔍 Uniqueness Verification Theorems & Methods

`uniqueness.py` implements four distinct verification paradigms:

1. **SAT-Based Blocking Clause Method**:
   - Finds first solution assignment $A = \{x_1, x_2, \dots, x_k\}$.
   - Appends blocking clause $\neg A = (\neg x_1 \lor \neg x_2 \lor \dots \lor \neg x_k)$.
   - Solves again: **UNSAT** $\iff$ puzzle solution is **unique**; **SAT** $\iff$ multiple solutions exist (returns counterexample).

2. **Deducibility Theorem** (Mašulović, 2022):
   - *Theorem*: A Sudoku puzzle has a unique solution $\iff$ its solution is logically deducible using constraint propagation alone.
   - Implements Naked Singles, Hidden Singles (row, column, block), and Locked Candidates.
   - If constraint propagation fully solves the grid without branching $\implies$ **guaranteed unique**.

3. **Unavoidable Sets** (McGuire et al., 2012):
   - Identifies digit-pair swap sets $U \subset G$ where swapping values preserves grid validity.
   - Verifies that every minimal unavoidable set is hit by at least one clue ($U \cap P \neq \emptyset$).

4. **Post-Solve Solution Validation**:
   - Verifies that every solved grid satisfies all row, column, and block row/column permutations ($1 \dots n^2$).
   - Reaches **100% validation pass rate** across all benchmark runs.

---

## ⚡ Dual CNF Encoding ($\phi$ vs $\phi'$)

| Encoding | Formulation | Variables | Clauses | Description |
|---|---|---|---|---|
| **Naive ($\phi$)** | Extended | $n^3$ | $O(n^4)$ | Full propositional encoding without clue propagation. Includes all definedness and cell/row/col/block uniqueness clauses. |
| **Compact ($\phi'$)** | Kwon & Jain | $|V_0| < n^3$ | Pruned | Partitions variables into $V_+$ (known true), $V_-$ (known false), $V_0$ (unknown). Deletes satisfied clauses and false literals. |

### Empirical Reduction (36×36 Grid Example):
- **Naive $\phi$**: 46,656 variables, 3,272,093 clauses.
- **Compact $\phi'$**: 613 variables, 3,224 clauses.
- **Reduction**: **98.7% variable reduction**, **99.9% clause reduction**, resulting in a **182.38× speedup** in SAT solve time!

---

## 📊 Empirical Results & Statistical Summary

Evaluated across **75 benchmark runs** (3 repeats, 25 puzzles, 5 sizes: $4\times4$, $9\times9$ 17-clue, $16\times16$, $25\times25$, $36\times36$):

| Grid Size | Group | Naive Vars | Compact Vars | Var Red. (%) | SAT Compact (mean) | SAT Naive (mean) | Backtracking (mean) | Speedup (Naive / Compact) |
|---|---|---|---|---|---|---|---|---|
| $4\times4$ | 4x4 | 64 | 21 | 66.2% | 0.001s | 0.001s | 0.05ms | 0.93x |
| $9\times9$ | 17-clue | 729 | 318 | 56.3% | 0.002s | 0.003s | 0.003s | 1.40x |
| $16\times16$ | 16x16 | 4,096 | 976 | 76.2% | 0.004s | 0.014s | 0.090s | 3.88x |
| $25\times25$ | 25x25 | 15,625 | 1,030 | 93.4% | 0.003s | 0.078s | 0.026s | 26.07x |
| $36\times36$ | 36x36 | 46,656 | 613 | 98.7% | 0.002s | 0.340s | 0.012s | **182.38x** |

> Complete statistical report available in [`Results/STATISTICAL_ANALYSIS.md`](Results/STATISTICAL_ANALYSIS.md).

---

## 🚀 How to Run

### Prerequisites

- **Python 3.8+**
- **matplotlib** (`pip install matplotlib`)
- **scipy** (optional, for accelerated statistical tests: `pip install scipy`)
- **A SAT solver** — precompiled `satch` binary included in `experiment/Main/executable/`

### Execution Commands

1. **Run Full Unified Benchmark** (Dataset assembly + dual encoding + SAT + BT + Validation + Stats + Plots):
   ```bash
   cd experiment/Main
   python3 unified_benchmark.py --sizes 4 9 16 25 36 --puzzles-per-size 5 --repeats 3 --seed 42 --timeout 30
   ```

2. **Run Uniqueness Verification Standalone**:
   ```bash
   python3 -c "
   from puzzle_manager import ROYLE_17_CLUE, parse_oneline
   from uniqueness import full_uniqueness_check
   from sat_solver_runner import find_solver
   grid = parse_oneline(ROYLE_17_CLUE[0])
   print(full_uniqueness_check(grid, 9, solver_path=find_solver()))
   "
   ```

3. **Compare Dual Encodings Standalone**:
   ```bash
   python3 -c "
   from puzzle_manager import ROYLE_17_CLUE, parse_oneline
   from dual_encoder import compare_encodings
   grid = parse_oneline(ROYLE_17_CLUE[0])
   print(compare_encodings(9, grid))
   "
   ```

4. **Re-generate Plots & Statistical Report**:
   ```bash
   python3 plot_results.py --csv ../../Results/benchmark_results.csv --out ../../Results/
   ```