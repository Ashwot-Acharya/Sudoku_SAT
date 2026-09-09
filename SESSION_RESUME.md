# Session Resume — Sudoku SAT Paper Verification (save point)

Saved 2026-09-09. Task not yet *fully* complete: remaining steps at bottom.

## What has been done

### 1. Citation verification (all web-checked)
- Kwon & Jain, "Optimized CNF Encoding for Sudoku Puzzles", LPAR 2006 (short paper) — REAL
  (http://www.cs.cmu.edu/~hjain/papers/sudoku-as-SAT.pdf). Previous `KwonJain2016`
  (FedCSIS) was the WRONG paper and has been replaced.
- Mašulović, "Deducibility in Sudoku", arXiv:2212.01053 (2022) — REAL (was wrong title/JAR).
- McGuire, Tugemann & Civario, "There is no 16-Clue Sudoku", Exp. Math. 23(2):190–217, 2014 — REAL.
- Eppstein & Zhang, "Sudoku grids that require many clues", arXiv:2607.05728 (2026) — REAL.
- Demaine, F. Ma, Schvartzman, E. Waingarten, Aaronson, "The Fewest Clues Problem",
  TCS 748:28–39, 2018 — REAL (Σ2^P-complete).
- GRASP: Marques-Silva & Sakallah, ICCAD 1996, 220–227 — REAL.
- DPLL 1962, Chaff DAC 2001, MiniSat SAT 2003, Sinz CP 2005 — all REAL.
- satch = Armin Biere's SATCH v0.5.6rc (github.com/arminbiere/satch) — REAL.
- `Vardi2006`, `Gomes2006`, `Bockmayr2003` — NO verifying evidence; treated as fabricated.

### 2. references.bib (Paper/report/references.bib) — EDITED
- Key `KwonJain2016` → `KwonJain2006` (authors Gihwon Kwon, Himanshu Jain).
- `Masulovic2022` retitled "Deducibility in Sudoku", arXiv:2212.01053, type misc.
- Deleted `Vardi2006`, `Gomes2006`, `Bockmayr2003`.
- Added: `DPLL1962`, `GRASP1996`, `Chaff2001`, `MiniSat2003`, `Sinz2005`,
  `Weber2005`, `Simonis2005`, `McGuire2014`, `EppsteinZhang2026`,
  `DemaineFewestClues`, `Satch`.

### 3. statistical_analysis.py (experiment/Main) — EDITED
- Fixed stale Key Finding "Backtracking times out on large grids (≥16×16)" →
  data-driven: sums `timeout_count` across groups; emits accurate scaling text.
- NOT yet re-run: `Results/STATISTICAL_ANALYSIS.md` still has the stale text.

### 4. paper.tex (Paper/report/paper.tex) — EDITED (in progress)
- Title page authors: last "Bishesh Bohora" → "Lakki Thapa".
- §1.1 Complexity: dropped Vardi2006, cite Yato2003 + added ASP⇒#P sentence.
- §1.6 SAT Solvers: added DPLL/GRASP/Chaff/MiniSat/Satch/Sinz citations.
- Solution Using SAT Solvers: Satch v0.5.6rc attributed (`\citep{Satch}`).
- Final Formula: attributed to Kwon & Jain 2006 (building on SuSAT).
- Notation remark added (math n = box size vs code n = grid size, box=√n).
- All remaining `KwonJain2016` → `KwonJain2006`.
- Dataset: added real clue counts {6,4,4,4,4}/{17,17,17,17,16(one 16-clue)}/{161,181,201,141,151}/{381,411,381,351,381}/{1041,931,1041,951,991}, density %, McGuire2014 + EppsteinZhang2026.
- Benchmark Protocol: hardware note (Ryzen 5 7235HS, 8c, 16GB, Linux 6.18.45-1-MANJARO x86_64) + "no run hit timeout".
- Table 1: speedup-ratio semantics note; "12× slower" → "≈4.8× slower"; observation corrected (BT wins 4×4 & 16×16 solve-only).
- Stats methodology: "occasional timeouts" → "none occurred".
- Wilcoxon paragraph: direction corrected (BT significantly faster at 4×4 & 16×16; SAT-C faster at 25×25 & 36×36).
- Friedman key findings: Kendall W = perfect agreement WITHIN size; rankings listed per size.
- Solution Correctness: added Mašulović2022 citation.
- Discussion: added "Limitations" subsection (single solver Satch, n=5 puzzles/size, dense-clue regime, E2E caveat).
- Abstract: "significant at 4 of the 5 grid sizes".

## Remaining steps (not done)
1. **paper.tex**: Appendix D (CDCL Solver Core, ~line 1060) — add note that the custom
   C CDCL core is a standalone study component, NOT used in benchmark timings.
2. **paper.tex**: Conclusion bullet ~line 816 — "Kendall's W = 1.0 … SAT Compact
   outperforms alternatives at larger sizes" needs the same truthful correction
   (rankings: BT < SAT-C < SAT-N at 16×16; SAT-C < BT < SAT-N at 25/36).
3. Regenerate `Results/STATISTICAL_ANALYSIS.md` (run statistical_analysis.py against
   Results/benchmark_results.csv) so stale key-finding text is gone.
4. Recompile: in `Paper/report`:
   `pdflatex -interaction=nonstopmode paper.tex && bibtex paper && pdflatex -interaction=nonstopmode paper.tex && pdflatex -interaction=nonstopmode paper.tex`
   Check for BibTeX warnings/unmatched keys; verify ~32-page paper.pdf. Note: appended
   text (Dataset, Limitations, notation remark) may grow page count beyond 32.
5. Final read-through pass → "call it end".

## Key data (final benchmark_results.csv)
- No timeouts anywhere (all [timeouts] empty).
- Solve-only means: BT 4×4 0.05ms → 36×36 0.012s; SAT-C flat ≈2ms; SAT-N 1ms→347ms.
- Speedups BT/SAT-C: 0.04×, 1.71×, 0.59×, 4.04×, 4.81×; N/C: 0.94×, 1.33×, 8.38×, 31.95×, 144.33×.
- Wilcoxon significant (p<0.001) at 4×4, 16×16, 25×25, 36×36; NOT at 9×9 (p=0.421).
- Friedman χ²=10.00 p=0.0067 W=1.000 at 16/25/36; χ²=7.60 p=0.0224 W=0.760 at 4×4;
  χ²=2.80 p=0.2466 W=0.280 at 9×9.
- Encoding: 36×36 naive 46,656 vars / 3,272,095 clauses → compact 607 vars / 3,194 clauses.
- E2E: 36×36 compact enc 1.046s, naive 1.911s; BT always fastest E2E (no encoding step).

## Notes
- No git commit yet (repo was `git add -A`'d earlier). Do not commit unless asked.
- Delete this file when no longer needed (and remove from staging if it got added).