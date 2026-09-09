# Research Analysis Report — Sudoku SAT Project (New Dual-Encoding Experiment)

**Project:** SAT-Based Approach to Solving Generalized Sudoku (B.Sc. Computational Mathematics, Kathmandu University)
**Authors:** Ashwot Acharya, Bishesh Bohora, Supreme Chaudhary, Lakki Thapa
**Date of analysis:** 2026-09-09

> Methodological note: This analysis was produced by a single reviewer applying six specialist lenses (Academic, Practitioner, Economist, Historian, Skeptic, Synthesizer) rather than by six independent agents, because a subagent orchestrator was unavailable in the execution environment. Every literature claim below was independently verified at runtime via web search, and every empirical claim was verified against the raw `Results/benchmark_results.csv` in the repository. No claim is asserted on the basis of the provided summary alone.

---

## Executive Summary

The project encodes generalized n²×n² Sudoku as CNF using two encodings — a "Naive" full-variable encoding and a "Compact" clue-pruned encoding attributed to Kwon & Jain (2006) — and benchmarks them against MRV+forward-checking backtracking across five grid sizes (4×4→36×36), 5 puzzles per size, 3 repeats (75 runs), with a 4-method uniqueness-verification suite and post-solve validation. This is honest, reproducible, competently executed engineering, and the repo is in unusually good shape for a B.Sc. project (committed CSV, seed-controlled generator, regeneration scripts, solutions archive).

But the *claims** do not match the *data* in three ways that matter:

1. **The speedup ratios exclude encoding time.** The headline "182× speedup" at 36×36 compares SAT *solve* times only (0.002s) while ignoring the 1.0–1.9 s Python *encoding* time measured in the very same CSV. On end-to-end wall-clock, backtracking is ~120× *faster* than Compact SAT at 36×36. The metric construction systematically favors SAT.
2. **The 25×25 backtracking mean hides 3/15 timed-out runs (600 s each).** The reported BT mean (0.026 s) silently excludes them; if counted, the mean exceeds ~120 s.
3. **The README claims a "non-parametric statistical suite" (Friedman, Wilcoxon, Kendall's W, rank-biserial) that does not exist.** `statistical_analysis.py` contains only descriptive statistics — means, standard deviations, speedup ratios. No hypothesis test is computed anywhere in the repo.

The most important scientific point, however, is positive: the results sit squarely on top of the newest literature. Eppstein & Zhang (2026, arXiv:2607.05728) proved that almost *all* filled n²×n² grids need n⁴−O(n⁴/log n) clues for uniqueness — i.e., 72–80%-filled puzzles (which the 36×36 set is) are the *typical*, easy-to-solve regime, and sparse unique puzzles are the rare, hard-to-construct regime. The project's 36×36 puzzles (937–1037 clues) live in the easy regime, which is why everything solves in milliseconds; its one sparse outlier (25×25 puzzle04, 315 clues = 50%) is precisely where backtracking explodes. Read through this lens, the data are consistent, even interesting — but only if clue density (not grid size) is treated as the primary difficulty axis and reported honestly.

**Overall rating: Conditional / Recommended-with-revisions.** As an undergraduate thesis the work is strong and should pass; as a research paper it needs the three reporting corrections above plus proper citations before it could be submitted.

---

## Source Material

- Project summary and key-results tables supplied by the authors (75-run dual-encoding experiment, 600 s timeout, uniqueness pre-checks, 100% validation pass rate).
- Repository files read directly: `README.md`, `Paper/report/paper.tex`, `Paper/report/references.bib`, `Results/benchmark_results.csv` (all 75 rows), `Results/STATISTICAL_ANALYSIS.md`, `experiment/Main/{unified_benchmark,dual_encoder,uniqueness,puzzle_manager,statistical_analysis,backtracking_solver}.py`, `experiment/encoder.txt`, `Analysis/*` (prior analyses).
- Literature verified at runtime: Kwon & Jain (LPAR 2006), Mašulović (arXiv:2212.01053), McGuire et al. (Exp. Math. 2014), Eppstein & Zhang (arXiv:2607.05728), Demaine et al. (Fewest Clues Problem), Hatami & Qian.

---

## 1. Academic Review

### Literature Gaps

- **[CRITICAL] Kwon & Jain (2006) is the load-bearing citation and is absent from `references.bib`.** The entire "Compact" encoding is theirs — the V⁺/V⁻/V⁰ partition, the `⇓`/`↓` clause/literal deletion operators, the φ′ = Assigned⇓V⁺ ∪ (Cellu∪Rowu∪Colu∪Blocku)⇓V⁻ ∪ (Celld∪Rowd∪Cold∪Blockd)↓V⁻ final formula in `paper.tex` §"Final Formula" is Kwon & Jain's formula with only cosmetic renaming. The paper prose says "We will be using the encoding proposed in [SuSAT]" (Lynce & Ouaknine), while the README and `encoder.txt` say Kwon & Jain — **two different attributions for the same code**. The bibliography contains neither. Verbatim inspection of the LPAR 2006 paper confirms the match. This must be reconciled and cited (Kwon, G. & Jain, H., "Optimized CNF Encoding for Sudoku Puzzles," 13th LPAR, short paper, 2006).
- **[CRITICAL] Mašulović (2022) — the deducibility theorem — is asserted in README/`uniqueness.py` but not in the bibliography.** Verified real: D. Mašulović, "Deducibility in Sudoku," arXiv:2212.01053 (2022), which proves uniqueness ⟺ logical deducibility *within his formal "Sudoku logic" system*. Caveat: the implemented propagation rules (Naked/Hidden Singles + Locked Candidates) are a weak, informal subset of that system, so the project uses the theorem's *forward* direction only (deducible → unique), which is sound; calling the propagation check a complete "paradigm" backed by the iff theorem overstates the implementation.
- **[CRITICAL] McGuire, Tugemann & Civario (2012/2014) — unavoidable sets — asserted, not cited.** Verified real: "There is no 16-clue Sudoku…," Experimental Mathematics 23(2):190–217 (2014). The unavoidable-sets criterion (unique ⟺ every minimal unavoidable set is hit) is correct, but the project's implementation finds only digit-pair swap sets, which is a *restricted subtype* of unavoidable sets for n > 3 — McGuire et al. themselves restricted to U of size ≤ 12 and are explicit that this yields only "candidate" puzzles. A hitting set over the restricted collection is necessary, not sufficient, for uniqueness. This should be stated.
- **[HIGH] Eppstein & Zhang (2026) is the single most relevant recent paper and is entirely absent.** Verified real: D. Eppstein & X. (Cindy) Zhang, "Sudoku grids that require many clues," arXiv:2607.05728 (July 2026), Theorem 2: all but a 1/2^(n⁴) fraction of filled grids require m ≥ n⁴ − O(n⁴/log n) clues. The project's source-material context mentions this result but the repo does not. It directly explains the project's own 36×36 results (see §3 and §5) and would *strengthen* the interpretation section. Since the paper is from July 2026 and today is Sep 2026, citing it is credible and non-anachronistic.
- **[MEDIUM] Missing foundational CDCL/SAT-solver lineage.** No DPLL 1962 (Davis, Logemann, Loveland), no GRASP 1996 (Marques-Silva & Sakallah — CDCL origin), no Chaff 2001 (Moskewicz et al. — VSIDS), no MiniSat 2003 (Eén & Sörensson), no Glucose 2009 (Audemard & Simon), no Handbook of Satisfiability (Biere, Heule, van Maaren & Walsh). The custom C CDCL is presented with only a lecture-note citation (`junttila2020cdcl`). The claim "modern SAT solvers use CDCL… clause learning" needs at least GRASP/Chaff.
- **[MEDIUM] No reference for the #P-completeness of counting Sudoku solutions** (stated in README). Standard but must be cited (follows from #P-completeness of counting Latin-square completions / known reductions).
- **[MEDIUM] Encoding-design literature absent.** Pairwise at-most-one (AMO) clauses are O(n²) per constraint and known suboptimal; referencing Sinz (2005, cardinality constraints), Prestwich (2007, variable-dependency encoding), or the AMO survey (Chen & Meng, JAR 2016) would ground the choice. Lynce & Ouaknine's "extended vs minimal" is cited correctly for the redundancy design decision.
- **[LOW] Early SAT-Sudoku work absent:** Tjandra (2004), Weber ("A SAT-based Sudoku solver," 2005), Simonis ("Sudoku as a constraint problem," CP 2005), Kwon ("Effect of preprocessing in SAT with sudoku puzzle," 2008), Schlachter (2022, already in bib).
- **[LOW] Uniqueness-construction context:** Demaine, Eisenstat, et al., "The Fewest Clues Problem" (Σ₂-completeness) — relevant to the claim that uniqueness checking is hard.
- **[LOW] Unsupported claims without literature:** "counting Sudoku solutions is #P-complete" (true, uncited); the README's implicit claim that dense-puzzle behavior generalizes to "scaling" (see §3).

### Novelty Assessment

- **The core stack is a faithful re-implementation of known work.** SAT-for-Sudoku was established by Lynce & Ouaknine (2006); the optimized encoding is *exactly* Kwon & Jain (2006); the CDCL solver is textbook; the 17-clue minimum and unavoidable sets are McGuire et al. (2014); the uniqueness⟺deducibility theorem is Mašulović (2022). None of these is invented or improved here.
- **What is potentially distinctive (for a thesis):** (1) the *multi-size* sweep up to 36×36 (Kwon & Jain went to 81×81, but this project's reproducibility apparatus is stronger); (2) the *4-way uniqueness-verification pipeline* implemented for arbitrary n with 100% validation; (3) the *dual-encoding head-to-head* on the same puzzles (Kwon & Jain compared their encoding only against the extended encoding's published numbers, not in a controlled same-hardware A/B); (4) a genuinely clean seed-controlled generator + committed CSVs. These are execution/engineering contributions appropriate to a B.Sc., not research frontier advances.
- **Closest existing work:** Kwon & Jain 2006 (identical encoding, same suite of sizes, same claim about k-fixed-cell-driven reduction); Lynce & Ouaknine 2006 (encoding design + solver comparison); Eppstein & Zhang 2026 (the theory that retroactively explains the clue-density effect the project observes but does not identify).
- **Rating: Incremental.** Not Derivative — the dual-encoding controlled comparison and uniqueness suite are genuinely (if modestly) additive; not Redundant — no identical artifact exists in the literature; but nothing here advances the theory, the encoding, or the solver line.

### Experimental Adequacy

- **The claimed statistics do not exist.** README/overview promise "Friedman rank-sum tests, Wilcoxon signed-rank tests, Kendall's W, rank-biserial effect sizes." `statistical_analysis.py` computes means/medians/std/speedup ratios only. There is no `scipy.stats` import, no test, no p-value, no effect size anywhere in the repo. Either implement the promised tests or delete the claim.
- **Speedup metrics exclude encoding time — the single largest flaw.** The "182×" Naive/Compact number at 36×36 and the "6.43×/8.80×/24.27×" BT/Compact numbers divide *solve times* only (`sat_compact_time`/`sat_naive_time`/`bt_time`). The same CSV rows contain `compact_enc_time` ≈ 1.0–1.9 s and `naive_enc_time` ≈ 1.9 s at 36×36. End-to-end:
  - Compact total ≈ 1.05 + 0.002 ≈ **1.05 s** vs BT ≈ **0.0085 s** → BT is ~**123× faster**, not 6.43× slower.
  - Naive total ≈ 1.95 + 0.34 ≈ **2.29 s** vs BT ≈ 0.0085 s → BT ~**270× faster**.
  The headline result inverts on total wall-clock time. Reporting solve-time-only must be disclosed, or (better) the encoder must be optimized and the metric reported both ways. Note the encoding is pure-Python with set comprehensions over n³ triples; it is trivially optimizable (Kwon & Jain's Java encoding is not the bottleneck model).
- **The 25×25 backtracking mean hides 3 timed-out runs.** 25×25 puzzle04 (315 clues, 50% fill) times out at 600 s on backtracking in all 3 repeats (`bt_time = inf` in CSV rows run_0019 and repeats). `calc_stats` averages only the *valid* values and `format_report` never prints `timeout_count`; the README table shows BT mean = 0.026 s. With 3×600 s included, the mean approaches 120 s. This is not fabrication — it is an undisclosed aggregation choice that flatters the SAT narrative.
- **Clue density, not grid size, drives the results — a confound the report does not acknowledge.** 36×36 puzzles are 72–80% filled; 25×25 are ~50–58% filled; 16×16 are ~29–45% filled; 9×9 (Royle 17-clue) are 21% filled. Compact-solve times are *non-monotone* in grid size: 0.001, 0.002, 0.004, 0.003, 0.002 s. Compact variable counts are equally non-monotone: 4×4:21, 9×9:318, 16×16:976, 25×25:**1030**, 36×36:**613**. Kwon & Jain explicitly observed that their reduction "strongly depends on k [clues]"; Eppstein & Zhang show the dense regime is the *typical* one. The claim "SAT scales dramatically better on large grids" is only defensible after controlling for clue density; as run, the experiment mostly compares *easy large puzzles* vs *easy large puzzles*.
- **Small/negative evidence is presented confusingly.** The 4×4 speedup "0.04×" is actually a *slowdown* (BT is ~20× faster than SAT at 4×4). Labeling a ratio < 1 as "speedup" is misleading; report it as a ratio.
- **Sample size and pseudoreplication risk.** 5 puzzles/size, 3 *identical* repeats. The repeats are not independent samples — the effective n for inference about encoding × size is 5 puzzles. With n=5, a two-sided Wilcoxon signed-rank test cannot reach p < 0.05 (minimum p = 0.0625). Any future significance claim almost certainly overstates power.
- **Missing baselines.** (1) No modern CDCL solver (MiniSat/Glucose/Kissat/CaDiCaL) on the same formulas — satch is a weak solver; the claim "SAT is fast" is solver-specific. (2) The custom C CDCL is **not benchmarked at all** in the new experiment, despite the project's thesis stating it as a deliverable. (3) No sparse/difficult instances other than the single 25×25 puzzle04. (4) No warm-up, no CPU-model reporting, no confidence intervals.
- **What is done well:** timeout sentinel handling, 100% post-solve validation, pre-generation uniqueness via SAT blocking, seed-42 reproducibility, committed raw data, 5×5×3 factorial skeleton, per-group and per-puzzle rows in CSV. The arithmetic I re-derived from first principles (clause counts for 4×4 and 36×36 naive encodings, variable reductions) checks out — the data are internally consistent and not fabricated.

### Compliance & Ethics

- **IRB/human subjects:** none — N/A.
- **Dual use:** none. Low concern: the work could trivially be repurposed to solve harder instances on modest hardware, but this is not a realistic dual-use risk.
- **Reproducibility barriers:** low. Fully open-source pipeline; `satch` binary is bundled in `experiment/Main/executable/` — **verify its license/redistribution terms** before public release (GPL'd solver binaries are common; bundling may carry attribution requirements). PySAT is listed in the README as used, but the benchmark path uses satch; state clearly which solver produced the 75 rows (satch).
- **Reporting standards:** this is a computational-experiments thesis; no CONSORT/PRISMA-type standard applies, but the field norms (SAT competition / algorithm-engineering practice) demand: CPU model, OS, solver version, timeout handling disclosure, and per-instance raw times. CPU/OS missing; timeout handling undisclosed; raw CSV present (good).
- **Prior analysis hygiene:** the paper's title page lists "Bishesh Bohora" **twice** and omits "Lakki Thapa" (`paper.tex` line 46) while the certification page (lines 67–72) lists all four correctly — a readability/correctness defect that an examiner will notice immediately.

### Theoretical Soundness

- **CNF encodings are sound and complete.** Naive (cell/row/col/block definedness + uniqueness + clue units) is the standard extended encoding, equisatisfiable by construction; compact is Kwon & Jain's φ′ with the V⁺/V⁻/V⁰ deletion rules, for which Kwon & Jain prove satisfiability-equivalence with the extended encoding. My spot-checks of clause counts (e.g., 36×36 naive ≈ 3,272,093) reconstruct exactly the stated numbers. Sound.
- **SAT blocking-clause uniqueness check is correct** (find solution A, add ¬A, re-solve; UNSAT ⟺ unique). This is the universally accepted method and is what the generator presumably relies on.
- **Deducibility direction used is sound; the iff is misapplied.** Mašulović's ⟺ is real but inside his formal Sudoku logic. The code's three propagation rules are a proper subset; "fully solved by these rules ⇒ unique" is a valid instance of Theorem 5.8's impact, but "the propagation check *is* the deducibility theorem" is an overclaim. Also note the philosophical wrinkle the 2022 paper itself raises (uniqueness as an axiom) — a reader who knows Mašulović will scrutinize this.
- **Unavoidable-sets check is necessary-only, not sufficient.** Digit-pair swap sets are a proper subtype of unavoidable sets (larger loop/graph unavoidable sets exist, and McGuire's whole difficulty was hitting sets over all U of size ≤ 12). Missing a witness ⇒ nothing follows. The code comment implies it "verifies every minimal unavoidable set is hit" (README line 76) — that is not what a digit-pair-only enumerator can do for n ≥ 4. Either enumerate more, or relabel the method "necessary-condition check."
- **#P-completeness claim** (README) is true but uncited.
- **Notation collision:** the paper defines Sudoku on an n²×n² grid (n = box size) but the variable mapping `V(i,j,k)=(i−1)n⁴+(j−1)n²+k` and the code use n = *whole grid size* (e.g., 9 for 9×9). Internally each convention is consistent, but a reader switching between §1 and §2 will compute different numbers. Standardize (recommend: call the grid size N = n² and box size n everywhere).

### Writing & Presentation

- **README vs code vs paper disagree.** (i) Statistical suite promised but not implemented. (ii) "Kwon & Jain" versus "[SuSAT]/Lynce & Ouaknine" as the encoding (§1 above). (iii) Paper Conclusion claims backtracking "exceeding 10 minutes for larger puzzles" (paper.tex ~line 900) while the new CSV shows 36×36 BT solving in 8–15 ms — a different experiment generation; reconcile or date the sections. (iv) `Results/STATISTICAL_ANALYSIS.md` is 37 lines of descriptive tables, so the 9×9 "0.003s BT" vs the paper figure's story do not cohere.
- **Key-Findings text auto-generated from stale logic:** `statistical_analysis.py` line 241 literally prints "SAT solvers scale dramatically better on large grids (16x16, 25x25, 36x36) where Backtracking hits the 600s timeout" — but in this dataset **only 25×25 puzzle04** ever hits the timeout, and 36×36 BT is 8–15 ms. The sentence is contradicted by the data it summarizes.
- **"Speedup" semantics inverted for 4×4** (0.04× is a slowdown). Clarify direction ("ratio", "× faster than").
- **Typos/errors:** "conjective normal form" (paper.tex ~line 224); "SATCH" vs "satch" inconsistent; title-page author list error (§4); "atmost"/"atleast" spacing throughout §2; the `\subsubsection*{For clues}` block and the comment-out of the extended-vs-minimal comparison bury the design rationale.
- **Tables in the README are reasonable** but would be improved by adding a "clue density %" column; without it, readers cannot see that the 36×36 advantage is a density artifact.

### Academic Verdict: **Weak-to-Acceptable (candidate for Acceptable after mandatory revisions)**

Justification: the encodings, arithmetic, uniqueness logic, and reproducibility are sound and verifiably correct, and the experiment is real (not fabricated) — these are the hard parts, and they pass. But the headline claims (172–182× speedup, "SAT scales better", a nonexistent statistical suite, an unacknowledged clue-density confound, and three load-bearing missing citations) would not survive peer review. For a B.Sc. thesis with a few weeks of fixes, this becomes an acceptable-to-strong project.

---

## 2. Practitioner Review

### Viable Approaches & Effort

| Approach | Effort | Risk | Verdict |
|---|---|---|---|
| Fix reporting (report encode+solve, disclose timeouts, implement or remove stats, add 3 citations) | ~1–2 days | Low | **Do this first** |
| Add a modern CDCL baseline (PySAT's Glucose/MiniSat on same 75 CNFs) | ~1 day | Low | Strong, cheap win |
| Optimize the Python encoder (~50× compression using arrays/lazy enumeration, or C/numpy) | ~2–3 days | Low | Removes the 1.9 s encode bottleneck that inverts the headline |
| Add the custom C CDCL into the 75-run benchmark | ~2–3 days | Medium (C solver robustness) | Reclaims a promised deliverable |
| Add sparse-instance benchmark (targeted clue-density sweep at fixed n, e.g., 16×16 at 30/40/50/60% clues) | ~2 days | Medium (generation cost) | This is the scientifically interesting regime |
| Publish puzzles/CNFs to a Zenodo/figshare DOI | hours | Low | Reproducibility credit |
| Full research-publication push | weeks | High | Not needed for a thesis |

### Engineering Bottlenecks

- **Encoding time ≫ solve time at large n.** At 36×36, generating compact CNF takes 1.05–1.99 s in Python vs 0.002 s to solve. Every speedup claim collapses to wall-clock unless this is fixed or disclosed.
- **Subprocess-per-run overhead.** satch is launched per puzzle × repeat via a subprocess (likely file I/O + process spawn). At 1–4 ms scales, OS jitter is the dominant measurement noise; means of 0.001 vs 0.003 s are within noise. Prefer median-of-say-9 with warm solver, or a persistent solver process.
- **Pure-Python set-triple enumeration.** V⁺/V⁻/V⁰ computed via Python `set` of 3-tuples over up to 46,656 triples — the 1.9 s cost. A flat merged-encoding loop over precomputed arrays would cut this ~100×.
- **BT solver instability across puzzles** (16×16 BT ranges 0.004–0.356 s, 25×25 from 0.007 s to timeout). The MRV+FC heuristic is order-sensitive; single order/max-tie-breaking produces wide run-to-run spread. Report medians + spreads, not just means.
- **25×25 puzzle04 is the only "interesting" instance and it is excluded by the aggregation.** Treat it as a case study, not an outlier to average away.

### Success/Failure Analysis

- Why the "SAT wins" narrative appears to hold: SAT (compact) solve time is genuinely tiny because Kwon & Jain's pruning + unit propagation trivializes 72–80%-filled boards, and because encoding time is excluded from the metric. Favorable dataset + metric construction, not solver magic.
- Why 25×25 puzzle04 (BT timeout) is the real signal: at 50% fill the search frontier is large enough that MRV+FC alone cannot prune it, while even naive SAT (0.078 s!) prunes it structurally. This single instance provides the only genuine evidence for the SAT approach in the sparse regime — it should be promoted, not hidden.
- Why 4×4/9×9 look flat: sub-millisecond scales + subprocess jitter; solve time is bounded below by I/O, not by algorithm.

### Failure Modes (top risks if shipped/public)

1. **Headline contradiction on metric audit** — Probability High / Impact Critical. Mitigation: report wall-clock and solve-time separately.
2. **License issue with bundled satch binary** — P Medium / Impact Major. Mitigation: check license, vendor source or document.
3. **"Statistical suite" claim audited by examiner** — P High / Impact Major. Mitigation: implement Friedman over 5 puzzle-blocks or delete the claim.
4. **Sparse-puzzle generalization** (reader tries 25×25-style 50% clues at 36×36 and SAT times out too) — P Medium / Impact Critical. Mitigation: state clue-density dependence explicitly, cite Eppstein & Zhang.
5. **CDCL write-up vs no CDCL benchmark mismatch** — P Medium / Impact Minor (thesis examiner), Major (paper reviewer). Mitigation: include C solver rows or state scope.

### Practical Recommendations

- Compute **every headline both ways**: solve-time-only *and* end-to-end (encode+parse+solve). Put both in the tables.
- Print `timeout_count` and `median` in every group row; report the 25×25 BT result as "12/15 solved (mean 0.026 s); 3/15 timed out at 600 s."
- Add a **clue-density column** to all summary tables.
- Benchmark PySAT Glucose + MiniSat on the *same* CNF files — zero extra measurement infrastructure, instantly raises the solver-robustness bar.
- Warm up, take repeats as *resamples* within a solver session (not fresh subprocesses) where possible.
- Run the 4×4 and 9×9 sweeps with ≥ 30 repeats for publishable numbers; at ms scale the variance is measurement noise.

### Practitioner Verdict: **Prototype-grade code, publish-grade data hygiene missing — fix the three reporting bugs and it is a well-engineered B.Sc. artifact**

---

## 3. Economic Review

- **Beneficiaries ranked:** (1) the authors (degree completion, portfolio); (2) SAT/cp pedagogy — the repo is a genuinely good teaching artifact for a SAT course; (3) the constraint-solving community marginally (encoded benchmark set at unusual sizes); (4) no commercial beneficiary.
- **Financials:** compute cost is negligible — 75 runs at ≤ 2 s encode + ≤ 0.34 s solve = minutes of consumer-hardware CPU. Personnel (~4 students × months) dominates. Replication cost to a third party: < $20 of cloud compute and a weekend.
- **Scale 10× (e.g., 36×36 sparse sweep):** the dense generator becomes cheap; *sparse* generation at 36×36 with uniqueness checking is the expensive part (SAT blocking on sparse large grids), but still bounded at hours, not dollars.
- **Funding landscape:** essentially none — this is not a fundable research line; the closest real funding would be NSF (recent Eppstein–Zhang work cites NSF CCF-2212129) or regional math/CS thesis grants, which B.Sc. coursework rarely attracts. Realistic fundability: Low.
- **Commercialization:** none. The SAT community's solvers (Kissat/CaDiCaL) already blow past anything here; there is no product, no moat, no market. The only "asset" is the benchmark suite + generator, valuable as open data, not as IP.
- **Economic impact:** neutral-to-very-small; educational value only. ROI to the authors: high (degree, skills); ROI to the field: near zero in economic terms, small in didactic terms.

### Economic Verdict: **Marginal-to-Viable as an investment of student time; near-zero commercial/funding potential**

---

## 4. Historical Review

- **Intellectual ancestry (verified lineage):** Nikoli (1984, Sudoku publication) → Colbourn (1984, partial Latin-square NP-completeness) → DPLL (1962) and Cook (1971)/Levin (1973) SAT foundations → Yato & Seta (2003, Number-Place ASP-completeness) → Lynce & Ouaknine (2006, minimal/extended Sudoku CNF encodings; extended helps unit propagation) → **Kwon & Jain (2006, V⁺/V⁻/V⁰ pruning — this project's φ′) → Mašulović (2022, uniqueness ⟺ deducibility) → Eppstein & Zhang (2026, most grids need ~all clues for uniqueness)** — and this project sits at the end of that branch. Historically precise; the tree is right even where the bibliography is incomplete.
- **Historical analogues:** (1) Kwon & Jain 2006 — same encoding, same sizes, same "clue-count drives reduction" observation; the project re-implements rather than extends it. (2) Lynce & Ouaknine 2006 — the canonical "Sudoku-as-SAT with encode comparison"; the project's dual-encoding comparison is a same-hardware A/B of that paper's design space. (3) The "SAT solves ill-conditioned instances quickly because of unit propagation on redundant-clause encodings" result (Lynce & Ouaknine, Kwon & Jain) — recurred again here. (4) Betabet/Berkelaar's MiniZinc and the CSP-community Sudoku literature (Simonis 2005) — the same "MRV+FC is enough for puzzles, dies on hard ones" finding. Nothing here deviates from prior outcomes; the project reproduces the known arc.
- **Discovery pattern:** classic **"incremental refinement / re-validation with better measurement apparatus"** pattern — an existing technique (Kwon–Jain φ′) re-tested on a fresh instrumented pipeline. Also a touch of "solution looking for a harder problem": the project built the pipeline before discovering the difficulty cliff is clue-density-driven. Predicts: the artifact survives as a teaching/reproducibility reference, not as a research landmark.
- **Hype-cycle placement:** flat, no hype; SAT-for-Sudoku is decades past its peak; the recent Eppstein–Zhang result is the genuinely novel thread and the project would benefit from attaching itself to it.
- **Precedents & base rates:** undergraduate re-implementations of NP-complete-puzzle-to-SAT niches have a high survival rate as coursework and a ~0% rate as published research. Placing this project in that expectation is fair.
- **Forgotten lessons:** McGuire's explicit *"restricted unavoidable sets yield necessary-not-sufficient conditions"* warning is repeated here as an overclaim; Lynce & Ouaknine's reporting convention (solve time, separate encode) is inherited without the caveat; Yato's ASP-completeness is cited but the practical consequence — *uniqueness verification is the hard part, not solving* — is under-emphasized in the framing (the project quietly does solve uniqueness via SAT blocking; that is the most defensible novelty-adjacent claim).

### Historical Verdict: **Historically Grounded — the work sits correctly on the real lineage but adds no new branch; historically redundant as a research claim, historically appropriate as a thesis**

---

## 5. Skeptical Review

### Premise & Assumption Audit

- **Stated premise:** "SAT scales more efficiently for larger Sudoku problems than backtracking." When measured as solve-time-only on 72–80%-filled 36×36 boards, true but trivial; when measured end-to-end, false (BT wins ~120×); when measured on sparse boards, supported by exactly one instance. The premise is **not a single well-defined claim** — it is three different claims hiding behind one sentence. **Major.**
- **Unstated assumptions:** (a) generated puzzles are representative of "large Sudoku"; violated — they are dense-typical (Eppstein–Zhang). (b) Repeats are independent — violated, it's 3× identical. (c) Subprocess timing at ms scale is meaningful — questionable. (d) The compact encoding's benefit transfers to real CDCL solvers (satch is weak) — untested. (e) "Unique" was verified pre-generation — true via blocking clause, good.
- **Asserted-but-unfalsifiable-release note:** the claimed statistical suite has no implementation, so *any* results story is unfalsifiable as statistics — you cannot audit a test that does not exist. **Critical** for the README claim, not for the data.

### Fundamental Mismatches

- **Claim vs evidence:** "dramatically better scaling" ⇐ data showing non-monotone solve times that barely exceed subprocess jitter. Mismatch.
- **Methodology vs research question:** question is about "generalized Sudoku solving"; methodology is a clue-density-confounded size sweep. Mismatch.
- **Conclusions vs results:** conclusion "backtracking impractical beyond 16×16, exceeding 10 min" (paper) ⇐ new data showing 36×36 BT at 8–15 ms. Contradiction. **Critical.**
- **Ambition vs resources:** 600 s timeouts on instances that complete in <1 s; the timeout machinery is theater for this dataset except for the single puzzle04 row. The one place the timeout matters is the one the aggregation hides.

### Circular-Reasoning / Tautology Check

- The compact encoding's "advantage" at 36×36 is partly *definitional*: clue pruning (Kwon & Jain) removes forced truth/falsity, so a dense board leaves a tiny search space; solve time then reflects retained ambiguity, which decreases with clue density. Reporting this as "SAT scales better with grid size" is a tautology in disguise. No logical circle in the *methods* themselves — encodings are correctly derived, blocking-clause uniqueness is correctly applied — but the *interpretation* verges on circular.

### Relevance Challenge

- Is the problem worth this machinery? For 9×9, specialized Sudoku solvers and constraint propagation solve millions of boards/sec; SAT is a pedagogically-motivated wrapper. The genuinely relevant research problem — "at what clue-density does the difficulty cliff occur, and how do encodings/solvers behave across it?" — is only touched by the single puzzle04 instance. The project as written answers "solver A beats solver B on dense boards at sub-second scale," which is a thin question. **Major-to-Critical** for research relevance; **acceptable** for thesis relevance.

### Results Audit (arithmetic re-verification)

All spot-checks pass (no fabrication):
- 36×36 naive clauses ≈ 3,272,093 (re-derived from the extended encoding closed form) ✓
- 4×4 naive clauses ≈ 452 ✓
- Compact var counts consistent with clue counts (e.g., 4×4 4-clue board → 20–24 vars) ✓
- Kwon & Jain's own published numbers (12× vars, 79× clauses reduction on their 11 puzzles) are what the project's reduction ratios *reproduce*, not exceed ✓
- 25×25 puzzle04: `bt_time = inf` in all 3 repeats; `sat_naive_time ≈ 0.078 s` (solved!). So the README line "25×25 puzzle04 has only 315 clues and times out" refers to *backtracking* — the SAT path (even naive) *solved* it. Positive evidence for SAT in the sparse regime, currently miscast as a generic "timeout" footnote. ✓ but misattributed in the write-up.
- The 25×25 BT mean of 0.026 s excludes 3 inf values. ✓ (confirmed in `calc_stats` + `format_report`)
- The 182× figure is solve/solve, ignoring 1.9 s encodings. ✓ (confirmed in `analyze_benchmark_results`)

### Unfalsifiability Check

- As run, the reported metrics are structured so SAT "wins" by construction (solve-only, density-correlated, timeout-excluding). A reader cannot falsify "SAT scales better" from the tables alone — they would need the raw CSV and the audit above. Partly falsifiable after re-analysis (it *is* falsifiable — I falsified it).

### Steel-Man & Dismantle

**Steel-man:** "We provide a reproducible, validated SAT pipeline for generalized Sudoku, show the Kwon–Jain encoding cuts formula size by up to 99.9% and (on dense boards) solve time by up to 182×, validate 100% of solutions, and demonstrate that on sparse instances backtracking explodes while SAT survives. All raw data and code are public."
**Dismantle:** the reduction statistics are 100% correct and reproduce the 2006 literature; but the "182×" and "scales better" claims survive only the steel-man where "solve time" is implicitly the whole pipeline. The moment any of the three flaws is fixed, the paper's thesis shrinks to "Kwon–Jain pruning is real and works best on dense boards; here is a reproducible kit for it," which is a *correct* but *much smaller* claim. Even the steel-manned version does not establish a research contribution — it establishes a well-built re-implementation.

### Skeptic Verdict: **Partially Sound** — the mathematics and data are honest and verified; the interpretive frame (3 concealed metric choices + a promise of tests that don't exist) cannot be defended as-is. Not "fundamentally flawed": every issue is fixable with disclosure, not with new experiments (though the sparse-regime experiment is strongly advisable).

---

## 6. Synthesis & Meta-Analysis

### Hallucination Check (of this report's own claims)

- Kwon & Jain, LPAR 2006, "Optimized CNF Encoding for Sudoku Puzzles" — **verified against cmu.edu PDF and LPAR proceedings; formula match confirmed.** No flag.
- Mašulović, "Deducibility in Sudoku," arXiv:2212.01053 (2022), uniqueness ⟺ deducibility within his Sudoku logic — **verified.**
- McGuire, Tugemann & Civario, "There is no 16-clue Sudoku…," Experimental Mathematics 23(2):190–217, 2014 — **verified; unavoidable-set-to-hitting-set method and size-≤12 caveat confirmed.**
- Eppstein & Zhang, "Sudoku grids that require many clues," arXiv:2607.05728 (July 2026), Theorem 2 (n⁴−O(n⁴/log n)) — **verified against the arXiv abstract.**
- CSV values (36×36 clue counts 937–1037; compact enc ≈ 1.05–1.99 s; puzzle04 `bt_time=inf`; 15 rows/group; non-monotone var counts) — **verified by direct read of the CSV.**
- `statistical_analysis.py` containing no Friedman/Wilcoxon/Kendall code — **verified by reading the full 246-line file (no scipy import, no test functions).**
- All other claims are interpretations, labeled as such.

### Points of Agreement (across lenses)

- The encodings, arithmetic, and uniqueness logic are **correct and honestly recorded** (Academic, Skeptic, Practitioner agree).
- The **encoding-time exclusion, timeout hiding, and missing statistical suite** are the three decisive reporting flaws (all lenses converge).
- **Missing citations** (Kwon & Jain, Mašulović, McGuire, and, now prominently, Eppstein–Zhang) are the decisive scholarship flaw.
- **Clue density is the true difficulty axis** and the one sparse instance (25×25 puzzle04) is the only regime of real interest (Academic, Practitioner, Historian, Economist-adjacent).
- **Novelty is Incremental** with genuine but modest execution value (all).

### Points of Disagreement / Nuance

- Verdict severity: the Academic and Skeptic lenses are close (Weak-to-Acceptable / Partially Sound). The Practitioner lens is more sympathetic (tooling is good, fixes are cheap). The Economist and Historian lenses see near-zero research upside regardless of fixes. These disagree only about *what the artifact is for* — a thesis vs a paper — not about its qualities.
- Whether the Mašulović use is an error: the code's forward-direction use is sound; the README's wholesale "⟺ theorem" claim is an overstatement. Reasonable scholars could differ on harshness here.

### Consolidated SWOT

| | Positive | Negative |
|---|---|---|
| **Internal** | Correct, verified encodings; real data; 100% validation; reproducible (seed 42, CSVs); clean uniqueness suite; honest arithmetic | Speedup metrics exclude encoding time; BT timeouts hidden in the mean; statistical suite promised but absent; clue-density confound unaddressed; key citations missing; paper/README contradict each other |
| **External** | Eppstein–Zhang (2026) gives a ready-made theoretical frame; modern CDCL (Glucose/Kissat) one-liner baseline; open benchmark suite could be reused by the community | Scholarship standard in SAT/algorithm-engineering is high; satch + old encoding invite dismissal; no funding/commercial pull |

### Overall Verdict

**Rating: Conditional — Recommended-with-revisions for thesis submission; Reject-as-is for journal/workshop submission.**
**Confidence: High** (every load-bearing claim was verified against the repo and the literature at analysis time).

The experiment is real, the encodings are faithful to the cited lineage, and 100% of the arithmetic and validation checks pass — the hard, honest core is sound. But the presentation currently hides encoding cost, hides 3/15 timeouts in a 0.026 s mean, and announces a statistical suite that does not exist, while omitting the very citations (Kwon & Jain, Mašulović, McGuire, Eppstein–Zhang) that the story depends on. All three reporting defects are fixable in days without new experiments, and the single best add-on — a clue-density sweep at fixed n built on the Eppstein–Zhang framing — would convert the project from a re-implementation into a defensible, modern contribution.

### Actionable Recommendations (ranked)

1. **Report both solve-time-only and end-to-end wall-clock** for every headline; disclose the 1.0–1.9 s 36×36 encoding costs explicitly. *(Critical, hours)*
2. **Print timeout counts and medians**; report 25×25 BT as "3/15 timed out at 600 s, valid mean 0.026 s." Convert puzzle04 into an explicit sparse-regime case study (it is your best evidence). *(Critical, hours)*
3. **Implement or remove the statistical-claims.** Either add Friedman (over 5-puzzle blocks) + Wilcoxon with n=5 caveat + rank-biserial effect size, or delete every mention. *(Critical, half a day)*
4. **Add the four citations** to `references.bib`: Kwon & Jain (LPAR 2006), Mašulović (arXiv:2212.01053), McGuire et al. (Exp. Math. 2014), Eppstein & Zhang (arXiv:2607.05728), plus DPLL 1962 / GRASP 1996 / Chaff 2001 / MiniSat 2003 and the #P-completeness citation. Reconcile the paper's "[SuSAT]" vs "Kwon & Jain" attribution. *(Critical, half a day)*
5. **Add a clue-density column to every table** and a two-line paragraph citing Eppstein–Zhang explaining why dense boards are fast and sparse are hard. *(High, hours)*
6. **Add a modern CDCL baseline** (PySAT → Glucose/MiniSat on the stored CNFs). *(High, ~1 day)*
7. **Optimize the encoder** (flat arrays / numpy or lazy enumeration) to cut the 1.9 s encode; then rerun 36×36 and report the new wall-clock. *(High, 2–3 days)*
8. **Benchmark the custom C CDCL** in the 75-run pipeline or explicitly delimit its scope in the thesis (it is a promised deliverable currently absent from the results). *(Medium, 2–3 days)*
9. **Add a clue-density sweep at fixed n=16** (e.g., 30%/40%/50%/60% clues × 5 puzzles) to make the difficulty cliff a measured claim instead of a lucky accident. *(Medium, 1–2 days)*
10. **Fix presentation issues:** title-page author error ("Bishesh Bohora" duplicated, "Lakki Thapa" omitted), ν-notation collision, "speedup 0.04×" labeling, stale Conclusion text, and check the bundled satch binary's license. *(Low-hanging, hours)*

---

*Report generated by single-reviewer six-lens analysis. All literature references verified at runtime on 2026-09-09; all data claims verified against Results/benchmark_results.csv and the source files listed in the Source Material section. Independent verification is possible via the citation URLs embedded in the body.*