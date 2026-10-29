# Sudoku_SAT — Session Diagnosis & Pending Decisions (Context File)

> **Purpose:** Full record of the diagnosis performed on the 3-encoding benchmark
> pipeline (native/naive φ, optimized/compact φ′, logarithmic φ_log), the two open
> questions awaiting user instruction, and the postponed work plan.
> **Status:** **RESOLVED 2026-10-23** — Part 1 implemented and verified; Part 2
> decisions taken (propagation-only n≥16, graduated sparsity); unique-sparse
> feasibility researched. See §7 below.
> **Date:** 2026-10-19
> **Related:** `Analysis/SUDOKU_PAPERS_EVALUATION.md` (31-source papers audit by research agent).

---

## 1. Requirements (restated by user)

1. Implementation of the **Log encoding** to solve the Sudoku CSP.
2. **Clause-reduction comparison** across native (naive), optimized (compact), and logarithmic encodings.
3. **Time evaluation**: which encoding CaDiCaL solves fastest; solve-time comparison of all
   three encodings **together with backtracking (MRV + forward checking)**.
4. `Results/benchmark_results.csv` must contain, per run:
   - CNF **variables and clauses** for all 3 encodings,
   - **solve time** for all 3 encodings,
   - **CNF conversion (encoding) time** for all 3 encodings.

All four are implemented in `experiment/Main/unified_benchmark.py` (CSV columns:
`naive_vars/clauses/enc_time`, `compact_vars/clauses/enc_time`, `log_vars/clauses/enc_time`,
`sat_naive_time`, `sat_compact_time`, `sat_log_time` (+ e2e + status each), `bt_time`,
`bt_status`). Entry point: `experiment/Main/run_pipeline.py` → `run_benchmark_pipeline()`.

---

## 2. Diagnosis — Issue by Issue

### 2.1 Log encoding: functionally correct, structurally bloated (CRITICAL)

**Symptom:** naive ~729 vars (9×9) vs log ~3564 vars — log must be *smaller*, not 5× larger.

**Root cause** — `experiment/Main/log_encoder.py:75-87` (`encode_log`):
for every peer pair (~3·n·C(n,2) pairs) it allocates `width` **auxiliary XOR-difference
variables** (4 clauses each + 1 OR clause). Cost = Θ(n³·log n) auxiliary variables,
which destroys the entire point of the log encoding.

- 9×9: 324 bit-vars + 972 pairs × 4 aux = **3564 vars vs naive 729** (user saw ~3800).
- Semantics were still *correct* (XOR gadget verified truth-table-wise; domain forbids
  codes ≥ n; validation passed) — the defect is size, not correctness.

**Approved fix (not yet applied):** replace the per-pair XOR machinery with
**minterm support clauses** (Gavanelli-style), zero auxiliary variables:
for each peer pair (A,B) and each value v, emit one clause forbidding *both* cells = v,
written directly over the 2·width bit literals.

**Verified size projection** (computed, dummy puzzle):

| n | naive vars | log vars NOW | **log vars FIXED** | naive clauses | log clauses NOW | **log clauses FIXED** |
|---|-----------:|-------------:|-------------------:|--------------:|----------------:|----------------------:|
| 4  | 64     | 144    | **32**   | 448       | 504       | **288**     |
| 9  | 729    | 3564   | **324**  | 11,988    | 14,337    | **9,315**   |
| 16 | 4,096  | 20,992 | **1,024**| 123,904   | 84,864    | **92,160**  |
| 25 | 15,625 | 103,125| **3,125**| 752,500   | 424,375   | **566,875** |
| 36 | 46,656 | 377,136| **7,776**| 3,271,104 | 1,575,288 | **2,485,728** |

Fixed log beats naive on **both vars and clauses at every size**.
Semantics unchanged: pairwise distinctness within each unit over n values ⇒ permutation
(allDefinedness is implicit; one code per cell by domain forbids).

### 2.2 Naive & compact encodings — VERIFIED OK

Read line-by-line:
- **Naive** (`dual_encoder.py:36-152`): cell/row/col/box definedness + uniqueness
  (pairwise AMO) + clue unit clauses. Correct. Vars = n³.
- **Compact φ′** (`sudoku_to_cnf.py:55-203`, Kwon & Jain): V⁺/V⁻/V0 partition,
  satisfied clauses deleted, false literals dropped, unit clues for fixed cells.
  Correct (`lit()` sentinel logic verified).

### 2.3 "Impossible" 0.007s backtracking on 36×36 — DATASET bug, solver is fine

**Symptom:** after the user's run, BT solved 36×36 in 0.007s; historical records had all
36×36 timing out >10 min.

**Root cause — the puzzles themselves are nearly solved:**

| Puzzle set | Fill measured |
|---|---|
| `sudoku_36x36_01` | 1041/1296 = **80.3%** |
| `sudoku_25x25_01` | 381/625 = **61%** |
| `sudoku_16x16_01` | 161/256 = **63%** |
| `sudoku_9x9_17clue_01` (Royle) | 17/81 = 21% (genuinely hard) |

Historical ">10 min" records came from `puzzle_fetcher.py` sparse sets (25×25 ≈ 50 clues
= 8%, 36×36 ≈ 72 clues = 5.6%), which were **silently overwritten** by the generator
(identical filenames written into the same directory by `puzzle_fetcher.py:465` and
`puzzle_manager.py:693` — execution-order dependent; confirmed by agent audit).

**Why generation stalls dense** (reproduced live):
`generate_puzzle(25, target_clues=150, ensure_unique=True, timeout=45)` burned the full
budget and stopped at **401 clues**; one SAT uniqueness check on 25×25 costs **~0.51s**
and returns *not-unique* for most removals → removal reverted → generator spins until
timeout. Targets (`_default_clues`): 16→90, 25→220, 36→500 — never reached.

**Deeper mechanism (agent audit):** the "check every 10 removals, revert only the probe
cell" logic (`puzzle_manager.py:415, 424-432`) lets up to 9 blind removals empty an
unavoidable set → base state becomes non-unique → every subsequent probe (subset of base)
fails forever → permanent stall at clue-count ≡ 1 (mod 10) — observed in **all 15**
committed generated large puzzles, which are all **provably non-unique** (verified with
two SAT solvers) yet labeled `uniqueness_verified=True` (flag computed from parameters,
not outcomes: `puzzle_manager.py:447`).

**Also explains "16×16 faster than 9×9 median":** 9×9 = Royle 17-clue (brutal), 16×16 =
63% fill (trivial). Dataset inconsistency, not a solver bug.

**Backtracking verdict: NO rewrite needed.** Logic verified correct
(MRV + degree heuristic `backtracking_solver.py:104`, forward checking `:119-126`,
validation PASSED). Its strange timings are purely dataset-driven.
Also fixed during session: BT timing now uses `time.perf_counter()` (sub-ms display,
`0.079ms` instead of `0.000s`).

### 2.4 Plot duplication — CONFIRMED BUG

`plot_results.py` `plot_group` (:196), `plot_group_line` (:257), `plot_cnf_stats` (:621)
draw **one bar cluster per CSV row** — with `--repeats 3`, each puzzle appears 3×
(x-labels "#1…#5, #1…#5, #1…#5"). Fix: aggregate repeats → mean per puzzle
(timeout if any repeat timed out).

Other plot defects:
- Legends say "(satch)" but the solver is **CaDiCaL**.
- `TIMEOUT_LABEL = ">10 min"` but timeout is now **15 min** (900s).
- `plot_speedup` hardcodes `600.0` (`plot_results.py:572`).
- Group `9x9-generated` missing from `GROUP_ORDER` → dropped from overview/scaling plots.
- `plot_cnf_stats` mixes "Log clauses" into a "vars" chart with wrong colors (minor).

### 2.5 CSV / pipeline status

- Old CSV on disk (10-column schema `group,size,puzzle,cnf_vars,...`) was produced by
  legacy `benchmark.py` — **deleted**; `run_pipeline.py` rewritten to call
  `unified_benchmark.run_benchmark_pipeline()` (flags: `--solver --sizes
  --puzzles-per-size --repeats --seed --timeout --no-plot --no-stats`).
- `Results/STATISTICAL_ANALYSIS.md` banned — all stats computed in memory; the
  `--from-csv` path write was removed.

---

## 3. The Two Questions Asked (ANSswers deferred — ASK AGAIN when instructed)

### Q1 — Puzzle hardness / uniqueness policy for large grids (16/25/36)
Options presented:
1. **Sparse, uniqueness off (recommended at the time):** for n≥16 stop enforcing SAT
   uniqueness per removal (accept multi-solution, like the original hard sets);
   reaches target density in seconds → 25/36 become genuinely hard again;
   metadata honestly marked `uniqueness_verified=False`.
2. **Keep strict uniqueness:** generation stays dense/slow (hours for 36×36) or never
   reaches sparse targets — results stay "easy puzzle" as today.
3. **Propagation-only for large n:** remove a cell only if naked-single propagation
   finds no contradiction — fast and sparse, no SAT overhead; multi-solution possible.

**User response:** *"Wait for further instruction I will message then."*

### Q2 — Clue-density targets (`_default_clues`) for 16/25/36
Options presented:
1. **Graduated sparsity (recommended at the time):** 16→64 (25% fill), 25→125 (20%),
   36→180 (14%) — bigger grids relatively sparser; BT likely minutes/timeout at 25/36.
2. **Match old hard sets:** 25×25 ≈ 50 clues (8%), 36×36 ≈ 72 clues (5.6%) —
   maximally hard; BT times out everywhere ≥16; even SAT gets heavier.
3. **Keep current targets** (16→90, 25→220, 36→500), only fix the stall —
   ~35-39% fill; BT may still be fast on 36×36.

**User response:** *"ask this question again when the further instruction is given."*

**⚠ Evidence to weigh when re-asking (from research agent):**
- Published ceilings for *unique* large puzzles: median fill **43% @25×25, 52% @36×36**
  (Lagerkvist, ModRef 2026); Stojadinović (2015) generated **no** 36×36 in hours.
  → **5–20% fill targets are unsupported by any verified published generator.**
- **Sparse ≠ hard:** hardness peaks near critical density ≈32% fill for 9×9 and
  *decreases* below it (Prates & Lamb, ICTAI 2018). Hardness ladders
  (clue-addition walks from a minimal base) are the recommended way to get 10+ graded
  puzzles per seed.

---

## 4. Postponed Work Plan (Part 1 ready; Part 2 blocked on user)

### Part 1 — ready to execute (no dataset policy needed)
1. Rewrite `encode_log` → minterm support clauses (zero aux; §2.1 table).
2. Cross-verify all 3 encodings: solve sample puzzles with CaDiCaL, decode, validate
   solutions, print vars/clauses table (unit test, not the pipeline).
3. Fix `plot_results.py`: repeat aggregation, `9x9-generated` in GROUP_ORDER,
   "CaDiCaL" labels, ">15 min" timeout label, speedup 600→900.
4. **Puzzles per size 5 → 10**: defaults in `unified_benchmark.py` + `run_pipeline.py`;
   extend 4×4 branch in `assemble_dataset` (only 5 hardcoded `FOUR_PUZZLES` exist;
   9×9 gets 5 Royle + 5 generated = 10 automatically).
5. Static verify: `py_compile` + encoding test.

### Part 2 — waiting for user instruction
- Generation hardness policy (Q1) and density targets (Q2) — re-ask both.
- Any generator rewrite (see recommendations below).
- Backtracking rewrite — **not needed** (diagnosis §2.3).

### Key recommendations from the 3-agent system (for when work resumes)
**Generator fix (Agent 1):** verify every removal OR roll back to last *verified*
checkpoint; terminal uniqueness gate before return; `uniqueness_verified` from outcomes
not parameters; record `target_clues/reached_target/stall` in metadata; namespace
generated vs curated puzzle filenames (D4 collision); replace blanket
`except Exception: pass`; use unavoidable sets as a deletion filter; extend benchmark
validator to check uniqueness + SAT/BT agreement.
**Faster generation (Agent 2):** cache φ′ CNF once per size + delta unit clauses per
check (biggest ROI); unavoidable-set feedback for free rejections; hitting-set-first
design if sub-40% fill is required; difficulty ladders for "10+ puzzles per seed";
difficulty labels from solver-observable metrics. 21 references in its report.

---

## 5. Companion Documents

| File | Content |
|---|---|
| `Analysis/SUDOKU_PAPERS_EVALUATION.md` | 31 papers/sources evaluated with DOI/URL references + repo bibliography audit (fabricated co-author in `references.bib:235`, wrong venues, 16-clue Royle contradiction in `paper.tex:481`). |
| `Analysis/UNIQUE_SPARSE_SUDOKU_RESEARCH.md` | Feasibility of unique sparse generalized Sudoku (<50% fill): verdict, known sparse records (16×16 21.5%, 25×25 23.4%, 36×36 25% by construction), methods, references. |
| Agent 1 report (in session) | Full generator audit: 21 defects table (D1-D21) with file:line + severity; cost/stall analysis; recommendations. |
| Agent 2 report (in session) | Alternative generation techniques: DLX, incremental SAT + blocking clues, unavoidable/hitting-set, #SAT/XOR, difficulty-vs-sparsity, corpora; comparison table; algorithm sketch; 21 references. |

*Note: Agent 1 and 2 reports exist only in the session transcript; this file summarizes
their critical findings. The papers evaluation is a full file on disk.*

---

## 6. Session Change Log (already applied, not postponed)

- `time.time()` → `time.perf_counter()` in `backtracking_solver`, `sat_solver_runner`,
  `dual_encoder` (encode timers), `sudoku_to_cnf`, `cnf_comparision`.
- BT/enc time display precision raised (ms for sub-ms, 6 decimals).
- Backtracking timeout 600 → **900s (15 min)** everywhere
  (`unified_benchmark.py:42`, `statistical_analysis.py` TIMEOUT_VAL, `uniqueness.py`
  defaults, `rerun_9x9_only.py`).
- Legacy `benchmark.py` **deleted**; `run_pipeline.py` rewritten to unified pipeline.
- `Results/STATISTICAL_ANALYSIS.md` deleted; no code path writes it anymore.
- `cadical` added first in `find_solver` candidates (`sat_solver_runner.py`).
- `log_encoder.py` created (log encoding + decode + DIMACS writer) — pending the §2.1
  rewrite.
- CaDiCaL installed at `/usr/sbin/cadical` (user-installed).

---

## 7. Resolution (2026-10-23)

### Decisions taken
- **Q1 (uniqueness, n≥16):** propagation-only policy, multi-solution allowed.
  Deleting clues from a grid that still contains the known full solution can never
  contradict, so per-removal propagation is skipped; one propagation pass runs after
  generation for metadata (`propagation_solved`, `propagation_contradiction`).
  `uniqueness_verified=False` is now reported honestly at n≥16.
- **Q2 (density):** graduated sparsity — 16→64 (25%), 25→125 (20%), 36→180 (14%),
  49→280, 64→380.
- Follow-up research task launched and delivered: `Analysis/UNIQUE_SPARSE_SUDOKU_RESEARCH.md`
  (unique <50% is constructively possible; best known 21.5% @16×16, 23.4% @25×25,
  25% @36×36; generic generators median 52.2% @36×36; 36×36 uniqueness proof is costly).

### Implemented & verified
- **Log encoder rewritten** (`log_encoder.py`): zero-auxiliary minterm support clauses.
  Measured: 9×9 log now 324 vars (was 3564); log now beats naive on vars *and* clauses
  at every size (36×36: 7,776 vars / 2.26M clauses vs naive 46,656 / 3.27M).
- **All 3 encodings cross-verified** with CaDiCaL on 4×4, 9×9, 16×16: SAT, decoded,
  validated. All PASS.
- **Generation**: instant at every size (16×16 0.00s, 25×25 0.01s, 36×36 0.03s),
  targets reached exactly; clues are a subset of a valid full solution; metadata honest.
- **10 puzzles/size** defaults; 4×4 tops up from 5 hardcoded to 10 generated;
  9×9 = 10 validated 17-clue puzzles.
- **Royle data repaired**: old list had a duplicate, a 16-clue and an 18-clue entry;
  only 2/7 distinct 17-clue entries were actually unique. Replaced with 10 entries from
  the sudoku17 mirror, each re-verified unique with CaDiCaL. `assemble_dataset` now also
  filters non-17-clue/duplicate entries defensively.
- **Plots fixed**: repeats aggregated (mean; any timeout ⇒ timeout), `9x9-generated`
  group added, "(satch)" → "(CaDiCaL)", timeout label 15 min, speedup constant 900,
  CNF chart split into Variables/Clauses panels.
- **Verified**: `py_compile` on all touched modules; synthetic-CSV plot run (16 PNGs,
  aggregation asserted); assemble_dataset test (20 puzzles, 10 per group).

### Measured hardness after the changes (one seed, informative)
| size (fill) | CaDiCaL compact | naive | log | BT |
|---|---|---|---|---|
| 16×16 (25%) seed7 | 0.01 s | 0.03 s | 0.65 s | >30 s |
| 25×25 (20%) seed7 | 0.08 s | 0.19 s | >30 s | >30 s |
| 36×36 (14%) seed7 | 0.37 s | 0.89 s | >60 s | >60 s |

Log encoding now wins on size but loses on propagation strength under CaDiCaL — a
legitimate empirical result, not a bug. Backtracking is genuinely hard/timeout at these
densities (seed variance is high: 16×16 seed99 solved in 2.1 s).
