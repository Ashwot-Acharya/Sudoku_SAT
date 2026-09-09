# Sudoku SAT — New Experiment: Practitioner Analysis

> **Date:** September 9, 2026
> **Analyst:** Senior practitioner review
> **Scope:** 75-run benchmark (5 sizes × 5 puzzles × 3 repeats), dual CNF encoding (Naive vs K&J Compact), satch + custom CDCL + MRV/FC backtracking, 4-method uniqueness suite.
> **Grounding:** All claims below verified against `Results/benchmark_results.csv`, `Results/STATISTICAL_ANALYSIS.md`, and the `experiment/Main/*.py` sources.

---

## 0. What the Data Actually Says (verified)

Before any opinion, the ground truth, because three headline numbers in the summary tables are materially misleading:

| Claim in summary | Reality in CSV |
|---|---|
| "36×36 SAT Compact: 0.002s" | True for **solve time only**. Encoding takes **1.05–1.10s** (compact) and **1.85–2.02s** (naive). End-to-end, SAT compact ≈ **1.05s** vs backtracking **0.012s** → SAT is ~87× **slower** wall-clock. |
| "36×36 BT very fast because 72–80% filled" | Confirmed. 937–1037 clues of 1296 (72–80%). The generator **never reaches its own 500-clue target** — the 60s generation timeout fires first. These are near-trivial puzzles. |
| "25×25 speedup 8.80×" | `calc_stats()` **drops timeouts from the mean**. 3 of 15 BT runs (puzzle04, 315 clues) are `inf` (600s) and excluded. The 0.026s mean reflects 12 non-timeout runs. |
| "3 repeats" | **Not** 3 independent datasets. `assemble_dataset()` is called once; repeat 2/3 re-solve the same 25 puzzles (seed `rep_seed` is computed and never used). Repeat-to-repeat variance is pure measurement noise (~±10%). |
| "100% validation pass rate" | Real, but `validate_solution()` only checks row/col/box set equality. It does **not** verify the solution honors the puzzle's given clues, nor that both SAT and BT found the *same* solution. |
| "Non-parametric statistical suite (Friedman/Wilcoxon/Kendall's W)" | Not in this codebase. `statistical_analysis.py` imports only `numpy`; it computes means/medians/std/speedups. The README's claim is aspirational. |
| "4 uniqueness methods" | Method 2 (unavoidable sets) only finds size-4 digit-swap rectangles → usually `None` (inconclusive). Method 3 (deducibility) is a necessary-condition check for uniqueness, and `_check_unique_sat()` silently returns `True` for n>9 when no SAT solver is available. |

**The compact-encoding scaling story is real, but it is a story about CNF size and I/O, not search.**
At 25×25 the compact formula is 8.8k clauses vs 753k naive; at 36×36 3.2k vs 3.27M. Once the instance is tiny, the "182× speedup" is dominated by avoiding a ~50MB DIMACS file parse + subprocess startup — not by cleverer search. That's still a legitimate result, but it must be *framed* as an encoding/engineering win, not as "SAT solves faster."

The one honest scaling signal in the whole run: **25×25 puzzle04 (315 clues, the sparsest instance) is the only backtracking timeout.** Difficulty is driven by clue density, not by grid size. Across these puzzles, SAT is invariant (~2ms) because every instance it saw was nearly full; BT varies by 4 orders of magnitude (0.04ms → 600s) with free-cell count.

---

## 1. Viable Approaches

What "this research" could become. Five concrete directions, with effort-to-value tradeoffs.

| # | Approach | What it is | Complexity | Cost | Timeline | Risk | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **Educational artifact (status quo)** | Clean repo, correct K&J encoding, working pipeline, honest internal benchmarks. Course credit. | Low | ~$0 | Done | Low | **Best fit for B.Sc.** |
| 2 | **Methodologically-honest empirical paper** | Fix stats (include timeouts, report medians + CIs), add clue-density axis, add Z3/CVC5 + PySAT baselines, benchmark custom CDCL, correct results tables. | Medium | ~$500–2k, 2–4 weeks human | 4–6 wks | Medium — reviewers will still flag "edge solvers" | **Only viable publication path** |
| 3 | **Novel encoding/hardness research** | Attack a genuinely open question (e.g., minimal-clue uniqueness for n=5+ boxes, encoding-threshold bounds, 📏 49×49/64×64 feasibility). | High | Low $, high skill | 2–4 mo | High (novelty uncertain) | Not advisable for undergrad deadline |
| 4 | **Framework/library for Sudoku-CNF research** | Turn `dual_encoder.py` + `uniqueness.py` into a reusable pip package (PySAT API instead of shelling out) for the community. | Medium | ~$1–3k | 3–6 wks | Medium (redundant w/ existing tools) | Marginal |
| 5 | **Deployable solver web-app / product** | "Solved problem with abundant free tools" — no market. | High (scaling, productization) | Unknown | Unknown | **Very high** | **Don't** |

**Recommended practical path:** Approach **2** for any publication ambition (SIGCSE / undergraduate journal / arXiv preprint), framed narrowly: *"An empirically honest comparison of two CNF encodings and a CSP backtracking solver for generalized Sudoku, with a clue-density difficulty model."* If the goal is the degree and defense, Approach **1** (with the corrections in §5) is sufficient and correct to deliver.

---

## 2. Engineering Bottlenecks

### 2.1 Compute & Runtime
- **Encoding dominates solving above 9×9.** 36×36: encode 1.05–2.0s vs solve 2–340ms. Nothing in the pipeline or paper separates these two phases — every timing claim conflates them. Must split "encode" and "solve" columns.
- **Naive CNF size explodes.** 36×36 naive = 3.27M clauses ≈ 50MB DIMACS; 49×49 ≈ 16.8M clauses (~250MB); 64×64 ≈ 64M (~1GB) — unsustainably large and slower to parse than to solve. The compact encoding is the only thing keeping ≥25×25 tractable, and it is not optional.
- **`_constraint_propagate()` and uniqueness checks during generation** are the real bottleneck of the dataset pipeline: each cell removal at n≥16 re-solves nearly the whole board. The generator's 60s timeout is what produced the clue-dense 36×36 set. Generation-time budget and dataset density are **not controlled variables**; they are coupled artifacts.

### 2.2 Data pipeline & correctness
- **Clue-density is an uncontrolled confound.** Sizes land at wildly different clue fractions: 4×4≈63%, 9×9≈19%, 16×16≈45%, 25×25≈53%, 36×36≈77%. Any "scaling" read is mixed with "fill ratio" differences.
- **Timeout censorship is inconsistent.** Backtracking uses a 600s timeout; `save_solution()` in backtracking_solver.py still hard-codes ">300" in its output header. Stats drop `inf` from means — so a run that times out is silently converted into "not present."
- **Repeats don't vary puzzles.** If the intent was randomness, `rep_seed` must actually reach `assemble_dataset()`. If the intent was timing variance on fixed instances, say so and report medians/IQR instead of means.
- **Duplicate/legacy scripts** (`benchmark.py`, `run_pipeline.py`, `cnf_comparision.py`, `rerun_9x9_only.py`, `sudoku_generator.py`, `puzzle_fetcher.py`) coexist with the new pipeline; `decoder.c` is an empty 0-byte file; old results live in `Results/archive/`. Maintenance drift risk.

### 2.3 Integration & infrastructure
- **SAT is via subprocess → DIMACS round-trip.** `run_solver()` shells out to satch, parses text `v` lines, then **re-encodes the puzzle in Python** to reconstruct the var_map (`decode_solution`). Fragile, slow, and a second source of encoding bugs.
- **Documentation gaps:** no hardware specs, OS, satch version, or Python/C compiler versions recorded in the results. A reviewer (or future you) cannot reproduce the 0.002s number.
- **Custom CDCL (C) is absent from the benchmark.** The solver is the most impressive deliverable but has zero measured results. Worse, it has no watched literals, no VSIDS, linear propagation — it would be 10–100× slower than satch on the same CNF and cannot be held up as "our solver beats backtracking" without qualification.
- **No PySAT usage** anywhere in the runnable pipeline despite the README's mention.

---

## 3. Success / Failure Analysis

### 3.1 Why the run "passed" (100% validation)
Genuinely good design, in three specific places:
1. **The K&J encoding is implemented correctly** — V⁺/V⁻/V₀ partitioning (sudoku_to_cnf.py) plus deletion of satisfied clauses and false literals is faithful to the 2006 paper. A correct encoding + a correct solver ⇒ valid solutions, which is why validation passes.
2. **The solver contract is sound** — IPASIR return codes (10/20) parsed correctly, with the "check UNSATISFIABLE before SATISFIABLE" substring-order bug explicitly avoided (line 67 of sat_solver_runner.py).
3. **Validation is wired into the pipeline, not bolted on** — pre-generation uniqueness + post-solve checks form an actual guard.

### 3.2 Why the "SAT scales better" narrative passed
Mostly favorable conditions, not superiority on the merits at large sizes:
- **Clue-dense instances** (the 60s gen timeout) gave SAT trivial search spaces at 25×25/36×36. A fill-ratio-controlled comparison would shrink the gap sharply.
- **Mean-vs-median + timeout-dropping statistics** flatter the compact encoding at 25×25 (hiding the 3×600s BT timeouts) and flatter SAT at 16×16 (where one puzzle, 101 clues, carries 45% of BT mean).
- **Encoding time excluded** — the single biggest contributor to "SAT wins" is being measured away.

### 3.3 Why 25×25 puzzle04 (315 clues) failed — the only failure, and the most instructive
This is **good design meeting a hard instance honestly**. MRV+FC without arc consistency hits a wide, weakly-constrained search tree (25×25, sparsest puzzle). It is the one data point where BT's combinatorial blowup is real, and it's exactly what the paper *should* be about. That it shows up in puzzle04 and nowhere else tells you the dataset is otherwise too easy to demonstrate anything about backtracking limits.

### 3.4 Why 4×4 SAT loses
No encoding, no subprocess, no clause parsing needed for an 8-row problem; BT's 0.04ms beats SAT's ~1ms of pure pipeline overhead. Overhead, not algorithm, decides 4×4. This result is comfortably generalizable and correctly reported.

### 3.5 Skill, luck, or design?
- **Skill:** the K&J implementation, CDCL-in-C, and pipeline discipline are real engineering skill.
- **Luck:** the generator's timeout accidentally produced "easy" 36×36 puzzles — this is the luckiest accident in the dataset and currently drives two of the five headline rows.
- **Design:** correctness guards (validation, uniqueness) are genuine good design. The statistical treatment of timeouts is *not*; it is the weakest methodological choice in the experiment.

---

## 4. Top 10 Failure Modes (Real-World/Extended Deployment)

| # | Failure | Probability | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **End-to-end times misreported** (encode excluded; "0.002s" quoted without 1.05s encode) | High | Critical | Report `encode + solve` separately and together; never headline solve-time alone. |
| 2 | **Dataset difficulty uncontrolled** (clue density 19–77% across sizes; gen-timeout artifact) | High | Critical | Fix clue targets to a controlled fill fraction; record and report generation metadata; separate "density" from "size" in the design. |
| 3 | **Non-unique puzzles admitted silently** (`_check_unique_sat` returns True for n>9 without solver; deducibility is only a necessary check) | Medium | Critical | Always use SAT blocking-clause check pre-generation when claiming uniqueness; record which puzzles were actually verified by which method. |
| 4 | **Timeout censorship** (inf dropped from mean; inconsistent headers) | High | Major | Report median, IQR, and timeout count; use survival-style analysis or impute timeouts explicitly. Never compute a mean over non-timeout runs alone. |
| 5 | **False confidence from repeated runs** (repeats = same puzzles, ±10% noise) | High | Major | Either vary seeds across repeats or frame repeats as timing-variance measurement on fixed instances. |
| 6 | **Encoding blow-up at 49×49/64×64** (naive ~250MB–1GB; even compact encoding time grows) | Medium | Major | Make compact the default, drop naive ≥49, stream clause generation, or cap sizes claimed. |
| 7 | **Solution validation misses clue-preservation** (checks only row/col/box sets) | Low | Major | Add a clue-consistency check and cross-checks across solvers (SAT grid == BT grid). |
| 8 | **Custom CDCL over-claimed** (no watched literals/VSIDS; linear propagation; unbenchmarked) | Medium | Major | Either benchmark it honestly on the same puzzles or drop it from claims; add watched literals + VSIDS if kept. |
| 9 | **Subprocess/DIMACS round-trip fragility** (output parsing, re-encoding for decode, solver path fallbacks) | Medium | Moderate | Move to PySAT's Python API (no DIMACS, no parsing) or IPASIR bindings. |
| 10 | **Reproducibility gaps** (no hardware/solver-version metadata, legacy scripts preserved alongside new) | Medium | Moderate | Add a `benchmark_meta.json` (CPU, OS, satch version, compiler, Python/pip versions); archive dead scripts; delete `decoder.c`. |

---

## 5. Practical Tips

**What I would do differently (highest leverage → lowest):**

1. **Add a clue-density axis before re-running anything.** Generate puzzles at controlled fill ratios (e.g., 25/35/45% of cells filled per size) and report solve time vs *free cells*, the variable that actually drives difficulty. The 25×25-puzzle04 timeouts become a *headline* instead of an awkward outlier.
2. **Fix the statistics layer in one sitting.**
   - Keep timeouts as `600s` in the distribution (or use median).
   - Report median + IQR, not mean, for solvers whose distributions are 4-orders-of-magnitude wide.
   - Actually implement the Friedman/Wilcoxon/Kendall's W the README already promises (scipy is one import) — or delete the claims.
   - Make repeats genuinely repeat: pass `rep_seed` into `assemble_dataset()`.
3. **Split timing into encode / solve / decode** and report all three. This single change neuters the biggest criticism of the results.
4. **Replace the subprocess+DIMACS round-trip with PySAT.** Dropping the `run_solver()` text parsing and the Python-side re-encoding (`decode_solution`) removes the two most fragile parts of the pipeline and makes runs ~100× cheaper at small sizes. Keep satch as an external-executable option.
5. **Benchmark the custom CDCL** — it's the differentiator. Add watched literals (2 weeks, biggest single win) and VSIDS (~100 lines). Even at 10× slower than satch, a *measured* comparison is far more compelling than an unmeasured one.
6. **Harden the generator.**
   - Fix the double-increment of `current_clues`/`removal_failures` in the `not is_complete` branch of `generate_puzzle()` (puzzle_manager.py ~lines 383–392) — clue bookkeeping is currently wrong in that path.
   - Remove the silent `return True` uniqueness fallback for n>9; fail loudly or omit the claim.
   - Decouple "generation timeout" from "target clue count" — today the 60s budget silently decides puzzle difficulty.
7. **Make `validate_solution()` verify the given clues** and cross-check SAT vs BT grids agree. Also validate that the CNF's `c MAP` decode path matches the Python decode path.
8. **Record environment metadata** (`satch --version`, uname, gcc/python versions) into the CSV or a sidecar. 30 seconds of work, saves a Chapter of "can you reproduce this?"
9. **Stop storing/regenerating duplicate legacy puzzles** (`sudoku_16x16_001.txt` vs `_01.txt`, etc.). One canonical dataset dir with a manifest.

**Common mistakes to avoid:**
- Quoting solver time without encode time (biggest risk as this gets graded/presented).
- Comparing an industrial solver binary against a hand-written Python CSP script *as if* the comparison were algorithm-vs-algorithm (say explicitly: "satch is an approximation of the practical SAT state of the art; the CSP solver is a minimal MRV+FC baseline").
- Using "mean" for distributions containing timeouts.
- Claiming uniqueness from `deducibility_check` alone.
- Letting the 36×36 "0.002s" become a poster number — it will not survive a reviewer.

---

## 6. Worth-It Assessment

| Question | Answer |
|---|---|
| Effort-to-impact ratio (as-is) | Poor as **research**; excellent as **degree deliverable**. The codebase already exists and is correct — the remaining effort is reporting discipline, not engineering. |
| Maintenance burden | Low (self-contained, no external deps besides matplotlib/satch). Moderate once `Results/archive/` and 5 legacy scripts accumulate. |
| Opportunity cost | The 4–6 weeks to reach publishable is cheap *relative to a B.Sc.\ time budget* but is real. Anything beyond that (encoding novelty, deployment) is a different project. |
| Simpler alternative achieving 80% with 20% effort | **Yes:** drop the CDCL-claims, drop the "4 methods" framing, keep K&J encoding vs naive encoding + BT, fix the statistics, and publish the corrected table. That is 80% of the paper's usable contribution at a fraction of the rework. |
| Strategic advice | If the degree needs a paper: take Approach 2 (4–6 weeks, low cost, clear roadmap). If not: hand in the project as-is after the §5 correctness fixes. Do **not** pursue deployment or encode-novelty research — the frontier is elsewhere and the reward per hour is negative. |

---

## PRACTITIONER VERDICT: **Prototype Only**

The engineering (K&J encoding, CDCL-in-C, validation discipline, modular pipeline) is genuinely good and worth keeping; the *results* are not yet trustworthy as reported, because the 36×36 headline includes only solve-time (encoding is 500× larger), the 25×25 speedup hides dropped timeouts, and clue density is an uncontrolled artifact of the generator's 60s budget. As a course deliverable it is complete and defensible with minor fixes; as a publishable claim it needs major rework of statistics, timing granularity, and dataset control — none of which is expensive, all of which is required. Build nothing further; invest 2–4 weeks in reporting discipline if external credit is sought, or ship as-is for the degree.