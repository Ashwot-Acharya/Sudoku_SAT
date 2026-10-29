# Sudoku Papers Evaluation & Repository Bibliography Audit

**Date:** 2026-10-19
**Scope:** 3 research themes — (A) SAT encodings for Sudoku/CSPs, (B) Sudoku generation, hardness & uniqueness, (C) backtracking/search heuristics — plus a full audit of this repository's own bibliography and citation claims.

---

## 1. Scope & Method

**What was evaluated.** 31 sources total: **29 papers**, **1 dataset** (Royle 17-clue collection), **1 software artifact** (Satch). Each was checked against primary material: the paper's own PDF/abstract, DOI or arXiv resolution, and — where a venue was in doubt — the reference lists of independent citing papers.

**Verification policy.** Only sources that were located and confirmed are included below. Eight candidate citations that circulated in earlier working notes could **not** be found in any database or by author; they are excluded from the source count and listed explicitly at the end of §7 with the verified substitute, if one exists. One *included* source has an unverified publication venue (⚠ marked). No citation in this document was invented.

**Local artifacts audited.**

- `Paper/report/references.bib` (28 entries) and its use in `Paper/report/paper.tex`
- `README.md` provenance/complexity claims
- `experiment/encoder.txt`, `experiment/Main/{sudoku_to_cnf,log_encoder,dual_encoder,uniqueness,puzzle_fetcher,puzzle_manager,cnf_comparision,run_pipeline}.py`
- Prior internal analyses: `Analysis/RESEARCH_ANALYSIS.md`, `Analysis/research_analysis_2026-09-09_21-15.md`, `Analysis/analysis.md`, `Analysis/NEW_EXPERIMENT_ANALYSIS.md`

**Counts:** 31 sources evaluated · 29 papers · **1 ⚠ UNVERIFIED venue** (Cazenave, [24]) · **8 candidate citations excluded as unverifiable** (§7 end) · 9 bibliography issues found in the repo (§5).

**Corrections to earlier working notes made during verification:** meSAT is by Stojadinović & Marić (not Feldmann et al.); McGuire et al. arXiv is 1201.0749 (not 1201.0785); Haralick & Elliott's title is "Increasing Tree Search Efficiency for Constraint Satisfaction Problems"; Walsh's "SAT v CSP" is **CP 2000**, not CP 2002; Weber's venue is LPAR-12 (not the SMT/SWP workshop).

---

## 2. SAT Encodings for Sudoku and CSPs

### 2.1 Foundations: minimal vs. extended, and clue-based optimization

- **[1] Lynce & Ouaknine (2006)** draw the baseline distinction the whole project rests on: a *minimal* encoding (definedness + pairwise row/column/box distinctness) that is equisatisfiable with Sudoku, versus an *extended* encoding with redundant clauses that substantially strengthens unit propagation — with the extended encoding, unit propagation alone solves about half of a set of very hard 9×9 puzzles; the minimal encoding does not. This is the direct ancestor of the repo's naive φ: `paper.tex:390` correctly states that φ′ "builds on the extended encoding of Lynce and Ouaknine" and cites `SuSAT`.
- **[2] Kwon & Jain (2006)** give the clue-aware optimization the repo re-implements as φ′: eliminate variables for cells/values fixed by givens and prune the corresponding peer clauses. Crucially for interpreting this repo's own results, Kwon & Jain observed that the reduction depends strongly on the number of givens — the reason φ′ looks best precisely on the repo's clue-dense n ≥ 16 instances (`paper.tex:461,481`). The repo's implementation (`experiment/encoder.txt`, `experiment/Main/sudoku_to_cnf.py`) and all six `paper.tex` citations match this paper; this is the single most faithful attribution in the bibliography.
- **[4] Weber (2005)** is an independent early encoding worth citing as corroboration (verified from the full text): 9 Boolean variables per cell (729 vars), one length-9 definedness clause and 36 length-2 pairwise-uniqueness clauses per cell, plus a lemma turning each 9-unit "all-different" into 324 binary clauses — explicitly chosen because short clauses enable unit propagation, which he equates to the human "crosshatching" technique. He reports zChaff solving publisher-"hard" puzzles in milliseconds, notes the encoding generalizes to arbitrary n²×n² grids, and sketches exactly the **blocking-clause + incremental SAT solution enumeration** that the repo implements in `uniqueness.py:27` — a useful priority claim. The repo's `references.bib:207` entry has the **wrong venue** (see §5.1).

### 2.2 Logarithmic / bit-vector encodings

- **[3] Gavanelli (CP 2007)** introduced the log-support encoding of a CSP into SAT: each domain value is mapped to ⌈log₂|D|⌉ bits, with *support-based* clauses per constraint. This is what the repo's φ_log is labeled after (`cnf_comparision.py:8`, `run_pipeline.py:28`). **Attribution caveat:** `log_encoder.py:54–81` actually encodes per-cell bit-codes (forbidding codes ≥ n²) plus XOR-difference ≠ 0 clauses per peer pair — i.e., a bit-coded *alldifferent*, not Gavanelli's constraint-support clause generation. It is a Gavanelli-*style* log encoding; either the label or the implementation should be adjusted (§5.5), and the Gavanelli entry is **missing from the bib** (§5.3).
- **[10] Biere & Brummayer (FMCAD 2008)** is the natural related-work partner for φ_log: dedicated bit-vector encodings of the `alldifferent`/`adc` constraint over the kinds of XOR-difference clauses `log_encoder.py:24,80` emits, with efficient consistency checking inside a SAT loop. Citing [3] **and** [10] would correctly position φ_log between the CSP-encoding and the bit-vector-CNF literature.
- **[9] Walsh (CP 2000), "SAT v CSP"**, is the classic argument that formulation matters: SAT and CSP encodings of the same combinatorial problems are not performance-equivalent, and translation can destroy structure. It is the intellectual justification for this project's core design — benchmarking φ (SAT) against MRV+forward-checking backtracking (CSP) on identical instances — and is currently **not cited anywhere** in the repo.

### 2.3 Multi-encoding frameworks and large instances

- **[5] Stojadinović & Marić (2014), meSAT** (*Constraints* 19:261–294): a framework that pluggably generates *multiple alternative* CSP→SAT encodings (including Sudoku) and empirically compares them; encoding choice, not solver choice, often dominates. This is the closest published analogue of the repo's three-encoding benchmark and the strongest candidate addition to the related-work section. Not in the bib.
- **[6] Pfeiffer, Karnagel & Scheffler (LPAR-17, 2010)** — "A Sudoku-Solver for Large Puzzles using SAT" — establishes that SAT encodings scale to generalized large grids, i.e., the exact regime (16×16–36×36) this project benchmarks. Not in the bib.
- **[7] Davis & Ji (2025, arXiv:2501.08569)** — "Evaluating SAT and SMT Solvers on Large-Scale Sudoku Puzzles" — a contemporary SAT-vs-SMT comparison on large instances; useful because `paper.tex:729` concedes no modern CDCL baseline was benchmarked.
- **[8] Schlachter (BSc thesis, Univ. Basel, 2022)** shows the CNF pattern generalizes beyond classical Sudoku to diverse variants (Killer, etc.) — relevant to any generalization claim. The bib entry exists but is malformed (§5.2).

**Synthesis (§2):** the repo's three encodings sit squarely on verified prior art — φ ≈ [1] minimal/extended, φ′ = [2] exactly, φ_log ≈ [3] in spirit and [10] in mechanism. What is missing is citation, not novelty: [3], [5], [6], [9], [10] are all absent from `references.bib`, and one attribution (φ_log) is stronger than the implementation warrants.

---

## 3. Sudoku Generation, Hardness, and Uniqueness

### 3.1 Complexity foundations

- **[11] Yato & Seta (2003)**: parsimonious reduction from Partial Latin Square Completion to Number Place establishes **ASP-completeness** (and hence NP-completeness of solving, plus #P-hardness of counting). The README (`README.md:12`) and `paper.tex:97` use this correctly in substance — but the prose says "Yato and Seta" while the bib entry is Yato's **single-authored MSc thesis**, and the name is misspelled "Takayushi" (§5.1). The journal version (IEICE Trans. Inf. & Syst., E86-A(5):1052–1060) is the better citation and is missing.
- **[12] Hoexum (2020, MSc thesis, Univ. Groningen)** expands Yato's compressed proof into a full constructive treatment and compares solving algorithms — the right pedagogical citation for the complexity paragraph. Present in the bib but **never cited**, and typed as an `@article` with no venue (§5.2).
- Colbourn (1984) — NP-completeness of partial Latin square completion, the reduction source — is correctly present and cited (`references.bib:11`, `paper.tex:97`).

### 3.2 Minimum clues, critical sets, uniqueness

- **[13] McGuire, Tugemann & Civario (2014)** — "There is no 16-Clue Sudoku": every 9×9 Sudoku needs ≥ 17 clues, proved by enumerating unavoidable sets and reducing to hitting-set search (restricted to unavoidable sets of size ≤ 12, giving *candidate* puzzles afterwards re-verified). Correctly cited at `paper.tex:481`. Two repo claims interact with it:
  - `README.md:76` says uniqueness checking "verifies that **every minimal unavoidable set** is hit" — but `uniqueness.py:199–251` enumerates only size-4 **digit-pair swap rectangles** and returns `None` (inconclusive) when none are found (`uniqueness.py:280`). That is a *necessary-condition* check for n ≥ 4, not McGuire's criterion. Relabel or broaden the enumerator (§5.5).
  - A digit-pair-only enumerator is exactly the "restricted subtype" caveat McGuire et al. themselves raise; the internal note `research_analysis_2026-09-09_21-15.md:41` already states this correctly.
- **[14] Royle 17-clue dataset**: 49,151 essentially different 17-clue puzzles (UWA, Gordon Royle). Used by the repo (`puzzle_fetcher.py:9`, `README.md:17`, `paper.tex:477`) and **has no bib entry** (§5.3). ⚠ Original host (`csse.uwa.edu.au/~gordon/sudokumin.php`) may be offline; McGuire et al. [13] cite it and are the durable secondary reference. Also: `paper.tex:481` reports one "Royle" sample puzzle with **16 clues** — that would contradict [13] if genuine, so it is almost certainly a clue-counting/parse artifact worth re-checking against `puzzle_manager.py` (which already documents a prior "corrected from 23 clues" bug in `puzzle_fetcher.py:130`).
- **[16] Demaine, Ma, Schvartzman, Waingarten & Aaronson (2018), "The Fewest Clues Problem"** (*TCS* 748:28–39; FUN 2016): worst-case bounds on how few clues can force a unique solution across grids — the general-n complement of [13]'s exact 9×9 result. In the bib, **never cited**.
- **[17] Eppstein & Zhang (2026, arXiv:2607.05728)** — "Sudoku grids that require many clues": for large n almost every grid needs n⁴ − O(n⁴/log n) clues, i.e., *sparse* uniquely-solvable large grids are atypical. `paper.tex:481,729` uses this exactly right — to argue that the benchmark's clue-dense large instances are typical rather than cherry-picked. **Author correction:** the second author is **Xinyu (Cindy) Zhang**, not "Linglong Zhang" (`references.bib:235`) — the most serious mis-citation in the file (§5.1).
- **[15] Lin, Wu & Wei (2013)**, "On specific 17-clue sudoku puzzles" (*ICGA Journal* 36(3):131–138): structural analysis of particular 17-clue instances — a natural follow-up citation alongside [13]/[14] for the 9×9 group.
- **[18] Hatami & Qian (2018)**, "Teaching dimension, VC dimension, and critical sets in Latin squares" (*J. Combinatorics* 9(1)): minimum critical-set sizes for Latin squares — the abstract generalization of "minimum clues for uniqueness" beyond Sudoku, and the right theoretical anchor if the paper claims novelty for uniqueness checking. (Co-author is Yingjie Qian.)
- **[19] Simonis (2005)** (ModRef workshop, CP 2005): the canonical constraint-modelling treatment of Sudoku (decision variables, all-different structure, modeling vs. solving) — the CSP-side anchor for the backtracking baseline. The repo bib carries a **title no database returns** (§5.1).

### 3.3 Difficulty metrics and generation

- **[20] Coelho (2007)** — a published *quantitative scale* for Sudoku difficulty (RCC 2(2):39–55, DOI 10.34627/rcc.v2i0.60); **[21] Henz & Truong (TAAI 2009)** — SudokuSat, a tool that analyzes hard instances via search-tree/propagation analysis; **[27] Chen (2009)** (§4) adds an information-theoretic complexity metric on the puzzle graph. Together these are the available options for the paper's "hardness" claims; the repo currently reports only SAT/backtracking runtimes, so citing one metric paper would harden that section.
- **[22] Nishikawa & Toda (2020, arXiv:2005.14098)** — exact construction of clue sets for **strategy-solvable** puzzles (generatable along a chosen human solving path). This is the principled alternative to the repo's procedural generator (`sudoku_generator.py`: fill then dig), and directly relevant if the paper discusses puzzle *quality* rather than only uniqueness.

**Synthesis (§3):** the theory chain (Colbourn → Yato/Seta → Lynce & Ouaknine → Kwon & Jain → Mašulović → McGuire → Eppstein & Zhang) is accurately stated in `paper.tex` and correctly cited — with two real defects: the Eppstein co-author is wrong, and the Royle dataset underpinning the 9×9 group is uncited while one of its reported puzzles contradicts McGuire's theorem. The unavoidable-sets uniqueness claim in the README overstates what `uniqueness.py` implements.

---

## 4. Backtracking and Search Heuristics

- **[23] Haralick & Elliott (1980)**, "Increasing Tree Search Efficiency for Constraint Satisfaction Problems" (*AIJ* 14(3):263–313): the origin of **MRV / most-constrained-variable + failure-directed backtracking** — precisely the strategy implemented in `experiment/Main/backtracking_solver.py` and named at `paper.tex:106` (which instead cites Russell & Norvig and Dechter; adding [23] gives the primary source).
- **[25] San Segundo & Jiménez (ICTAI 2009)** derive CSP variable-ordering heuristics from **graph structure** and demonstrate them on Sudoku — the closest published relative of the repo's MRV ordering and a natural related-work bridge between §2 (graph/CSP) and this section.
- **[29] Chi & Lange (2013, arXiv:1203.2295)** directly compare the three algorithm families on Sudoku — **backtracking vs. simulated annealing vs. alternating projections** — and find plain backtracking wins. This is the single most relevant external result for the repo's headline finding ("backtracking remains fastest end-to-end", `paper.tex:729`) and should be cited there.
- **[24] Cazenave (n.d.)** ⚠ **UNVERIFIED VENUE**: "A search based Sudoku solver" (author's LAMSADE page PDF) compares forward checking with limited-discrepancy search and reports phase-transition-like difficulty behaviour, incl. for 25×25 grids. The PDF carries no publication venue and no DOI/record was found — cite by URL only or drop.
- **[26] Lewis (2007)**, "Metaheuristics can solve sudoku puzzles" (*J. Heuristics* 13(4):387–401): metaheuristic local search is competitive on Sudoku — the strongest published counterpoint to the repo's backtracking-first conclusion (and a better substitute than the unfindable "Lewis & Thornton, Sudoku setter and solver", §7).
- **[27] Chen (2009, arXiv:0903.1659)**, "Heuristic Reasoning on Graph and Game Complexity of Sudoku": formalizes Sudoku as a graph, proves r-reduction/inference theorems, and proposes an information-theoretic difficulty metric that discriminates puzzle levels experimentally — simultaneously a heuristic paper (this section) and a metric paper (§3.3).
- **[28] Crook (2009)** (*Notices AMS* 56(4):460–468): the peer-reviewed pencil-and-paper algorithm (forced cells + trial-and-error) — the human-strategy baseline, and the reason unit propagation in [1]/[4] is "crosshatching".
- **[30] Pillay (2012)** (*South African Computer Journal*): human intuitive heuristics formalized as a solving procedure — complements [28] for the human-techniques paragraph.
- **[31] Satch (Biere, software, v0.5.6rc)**: the CDCL solver used throughout (`paper.tex:449,493`); cited as software via GitHub, which is acceptable, though a peer-reviewed Satch publication should be substituted if one is available at submission time.

**Synthesis (§4):** the repo's MRV + forward-checking baseline is textbook ([23], and correctly attributed in-house to Russell & Norvig/Dechter), and its empirical conclusion — backtracking beats SAT end-to-end at these sizes/densities — is independently supported by [29] and anticipated (for discrepancy search vs. propagation) by [24]. What's missing from the paper: [23] as the primary MRV citation, [29] as external confirmation, and [26] as the honest counterpoint.

---

## 5. Repository Bibliography Audit

File: `Paper/report/references.bib` — **28 entries**. All keys referenced by `paper.tex` resolve (Cook1971 and Dechter2003 are present; note `references.bib:68` has a stray leading space before `@article{Cook1971`, which some parsers reject).

### 5.1 Mis-citations — fix before submission

| # | Location | Problem | Correction |
|---|----------|---------|------------|
| 1 | `references.bib:235` (`EppsteinZhang2026`) | Second author **"Zhang, Linglong"** is wrong (fabricated-looking name) | Second author is **Xinyu (Cindy) Zhang** (verified: arXiv:2607.05728) |
| 2 | `references.bib:210` (`Weber2005`) | Venue "Proc. Tenth Int. Workshop on Satisfiability Modulo Theories (SMT) / SWP" — **no such venue for this paper**; also `@incollection` | Actual: **LPAR-12, Short Paper Proceedings, pp. 11–15, 2005** (verified from PDF + citing works); use `@inproceedings` |
| 3 | `references.bib:215` (`Simonis2005`) | Title **"AER: A CP Model for Sudoku"** returns no record in any index; the verified CP-2005 ModRef paper by Simonis is **"Sudoku as a Constraint Problem"** | ⚠ Verify: replace title with "Sudoku as a Constraint Problem", 4th Int. Workshop on Modelling and Reformulating CSPs (ModRef), CP 2005, or supply a source for "AER" |
| 4 | `references.bib:27` (`Yato2003`) | Author misspelled **"Takayushi"** → "Takayuki"; error propagates into the rendered bibliography (`paper.bbl:130`) | Fix spelling; note the prose says "Yato **and Seta**" (`paper.tex:97`) while this entry is single-authored — add the journal version (Yato & Seta, *IEICE Trans. Inf. & Syst.* E86-A(5):1052–1060, 2003) and cite it |

### 5.2 Malformed / non-standard entries

- `Thesis2022` (`:53`): `author = {Bachelor Thesis and Sebastian Schlachter}` — the degree text landed in the author field → `author = {Sechlachter, Sebastian}` + `type = {Bachelor Thesis}`; `url` points at the group homepage, not the PDF (`https://ai.dmi.unibas.ch/papers/theses/schlachter-bachelor-22.pdf`).
- `Hoexum2020` (`:45`): declared `@article` with **no journal**, no URL → `@mastersthesis`, add `https://fse.studenttheses.ub.rug.nl/22745/`.
- `Cook1971` (`:68`): `@article` whose "journal" is the STOC proceedings → `@inproceedings` (and drop the leading space).
- `Yato2003` (`:23–34`): JabRef import residue — non-standard `key`, `type`, `date_added`, `date_published`, `urls`, `collections` fields; thesis misfiled as `@article` with `journal = {Master's Thesis, ...}` → use `@mastersthesis` + `school`.
- `DemaineFewestClues` (`:243`): "Fermi Ma" not in `Last, First` form (renders as surname "Ma" inconsistently) → `Ma, Fermi`.
- `wikiSAT` (`:60`): Wikipedia is cited for the SAT definition **and for Levin's 1973 result** (`paper.tex:110,116`) — replace with Huth & Ryan (already in the bib) or a primary source.

### 5.3 Missing entries (claims made without a citation)

1. **Gavanelli (CP 2007)** — φ_log is attributed to Gavanelli in `cnf_comparision.py:8` and `run_pipeline.py:28`, but there is no Gavanelli entry in the bib at all. DOI 10.1007/978-3-540-74970-7_59.
2. **Royle 17-clue dataset** — used by `puzzle_fetcher.py:9`, `README.md:17`, `paper.tex:477`; no citation. Cite the UWA page and/or McGuire et al. [13] as secondary.
3. **Yato & Seta journal version (IEICE 2003)** — required by the prose "Yato and Seta" (`paper.tex:97`, `presentation.tex:87,562`).
4. Optional but recommended for §2: **meSAT [5]**, **Pfeiffer et al. [6]**, **Biere & Brummayer [10]**, **Walsh [9]**.

### 5.4 Dead weight (in bib, never cited in `paper.tex`)

`Weber2005`, `Simonis2005`, `Hoexum2020`, `Thesis2022`, `DemaineFewestClues`, `junttila2020cdcl` — six entries unused. The first two are Sudoku-specific related work whose *absence from the prose* (not the bib) is the actual gap; the related-work section currently never mentions Weber or Simonis.

### 5.5 Attribution & claim-integrity issues (code/paper vs. literature)

1. **φ_log is "Gavanelli-style", not Gavanelli.** `log_encoder.py:54–81` implements bit-codes + per-peer XOR-difference ≠ 0 (a bit-coded alldifferent, mechanism = [10]), whereas Gavanelli [3] uses constraint-support clauses. Either relabel (`"log-support encoding (after Gavanelli [3]); pairwise XOR-difference form"`) or re-implement support clauses — and add [3] to the bib either way.
2. **README overclaims the unavoidable-sets test.** `README.md:76` "verifies that every minimal unavoidable set is hit" vs. `uniqueness.py:199–251` which enumerates only size-4 digit-pair rectangles and returns `None` when none are found (`:280`). Necessary, not sufficient, for n ≥ 4 — reword to "necessary-condition check over digit-swap unavoidable rectangles" or enumerate general sets (McGuire's own restriction to |U| ≤ 12 is the precedent).
3. **A "16-clue Royle puzzle" appears in the results** (`paper.tex:481`). Given [13], no 16-clue 9×9 Sudoku exists; re-verify the clue count (a prior bug of exactly this kind is documented at `puzzle_fetcher.py:130`).
4. **Prior internal analyses are outdated and should not be trusted on bib state:** `RESEARCH_ANALYSIS.md:22` describes a 12-entry `Final_paper/references.bib` missing Kwon & Jain / McGuire / Mašulović; the current `Paper/report/references.bib` has 28 entries including all three (`:111,221,120`), and all three are cited in `paper.tex:49,481,711`. The claim in `research_analysis_2026-09-09_21-15.md:41` that McGuire is "asserted, not cited" no longer holds. Conversely, the gap *has* widened elsewhere (§5.3).
5. **Royle provenance note:** `puzzle_manager.py:657` hardcodes `verified_unique: True  # proven unique (Royle database)` for all bundled 9×9 puzzles — uniqueness for Royle puzzles is inherited from [13]'s proof *about the collection*, which the paper should cite (missing, §5.3) rather than assert inline.

---

## 6. Synthesis

1. The repo's technical lineage is real and correctly described in prose: minimal/extended CNF [1] → Kwon & Jain clue-pruning [2] (faithfully re-implemented as φ′) → log-support/bit-vector alternatives [3][10], benchmarked against textbook MRV+FC backtracking [23] — no invented prior work was found in the paper's main claims.
2. The bibliography's three worst defects are concrete and fixable in minutes: the fabricated-looking co-author "Linglong Zhang" [17], Weber's wrong venue [4], and Simonis's unlocatable title [19] — plus the "Takayushi Yato" typo that reaches the printed `.bbl`.
3. Attribution outruns implementation in exactly one place: φ_log is labeled Gavanelli but implemented as XOR-difference alldifferent, and Gavanelli is simultaneously uncited — the easiest fix is a relabel plus a real entry (or, better, cite [3] and [10] together).
4. The strongest under-cited external results for the paper's own conclusions are Chi & Lange [29] (backtracking beats SA/alternating projections — supports the headline), meSAT [5] (encoding choice dominates — justifies the three-encoding design), and Walsh [9] (SAT-vs-CSP comparison — justifies the baseline); the honest counterpoint to cite is Lewis [26].
5. One data-integrity item must be resolved before submission: a reported "16-clue" Royle puzzle contradicts McGuire's theorem [13], and the Royle dataset itself — the backbone of the 9×9 group — has no citation at all.

---

## 7. References

### 7.1 SAT encodings

1. **[1]** I. Lynce and J. Ouaknine. *Sudoku as a SAT Problem.* Proceedings of the 9th International Symposium on Artificial Intelligence and Mathematics (ISAIM), 2006. http://anytime.cs.umass.edu/aimath06/proceedings/P34.pdf
2. **[2]** G. Kwon and H. Jain. *Optimized CNF Encoding for Sudoku Puzzles.* 13th International Conference on Logic for Programming, Artificial Intelligence and Reasoning (LPAR-13), Short Papers, 2006. http://www.cs.cmu.edu/~hjain/papers/sudoku-as-SAT.pdf (mirror: https://www.lix.polytechnique.fr/~hermann/LPAR2006/short/submission_153.pdf)
3. **[3]** M. Gavanelli. *The Log-Support Encoding of CSP into SAT.* Principles and Practice of Constraint Programming (CP 2007), LNCS 4741, pp. 815–822, Springer, 2007. DOI: [10.1007/978-3-540-74970-7_59](https://doi.org/10.1007/978-3-540-74970-7_59)
4. **[4]** T. Weber. *A SAT-based Sudoku Solver.* Proceedings of the 12th International Conference on Logic for Programming, Artificial Intelligence and Reasoning (LPAR-12), Short Paper Proceedings, pp. 11–15, 2005. https://user.it.uu.se/~tjawe125/publications/weber05satbased.pdf
5. **[5]** D. Stojadinović and F. Marić. *meSAT: Multiple Encodings of CSP to SAT.* Constraints, 19(3):261–294, Springer, 2014. DOI: [10.1007/s10601-014-9165-7](https://doi.org/10.1007/s10601-014-9165-7)
6. **[6]** J. Pfeiffer, S. Karnagel and H. Scheffler. *A Sudoku-Solver for Large Puzzles using SAT.* Logic for Programming, Artificial Intelligence and Reasoning (LPAR-17), pp. 52–57, 2010. DOI: [10.29007/79mc](https://doi.org/10.29007/79mc) (mirror: https://www21.in.tum.de/~lammich/2015_SS_Seminar_SAT/resources/A_Sudoku-Solver_for_Large_Puzzles_using_SAT.pdf)
7. **[7]** R. Davis and Z. Ji. *Evaluating SAT and SMT Solvers on Large-Scale Sudoku Puzzles.* arXiv:2501.08569, 2025. https://arxiv.org/abs/2501.08569
8. **[8]** S. Schlachter. *Encoding Diverse Sudoku Variants as SAT Problems.* Bachelor's thesis, Department of Mathematics and Computer Science, University of Basel, 20 July 2022. https://ai.dmi.unibas.ch/papers/theses/schlachter-bachelor-22.pdf
9. **[9]** T. Walsh. *SAT v CSP.* Principles and Practice of Constraint Programming (CP 2000), LNCS 1894, pp. 441–456, Springer, 2000. DOI: [10.1007/3-540-45349-0_32](https://doi.org/10.1007/3-540-45349-0_32)
10. **[10]** A. Biere and R. Brummayer. *Consistency Checking of All Different Constraints over Bit-Vectors within a SAT Solver.* Formal Methods in Computer-Aided Design (FMCAD), 2008. DOI: [10.1109/FMCAD.2008.ECP.32](https://doi.org/10.1109/FMCAD.2008.ECP.32); PDF: https://fmv.jku.at/papers/BiereBrummayer-FMCAD08.pdf

### 7.2 Generation, hardness, uniqueness

11. **[11]** T. Yato and T. Seta. *Complexity and Completeness of Finding Another Solution and Its Application to Puzzles.* IEICE Transactions on Information and Systems, E86-A(5):1052–1060, 2003. (Related: T. Yato, master's thesis, University of Tokyo, 2003 — the entry currently in `references.bib`.)
12. **[12]** E. S. Hoexum. *Revisiting the Proof of the Complexity of the Sudoku Puzzle.* Master's thesis, University of Groningen, June 2020. https://fse.studenttheses.ub.rug.nl/22745/
13. **[13]** G. McGuire, B. Tugemann and G. Civario. *There Is No 16-Clue Sudoku: Solving the Sudoku Minimum Number of Clues Problem via Hitting Set Enumeration.* Experimental Mathematics, 23(2):190–217, 2014. DOI: [10.1080/10586458.2013.870056](https://doi.org/10.1080/10586458.2013.870056); arXiv:1201.0749.
14. **[14]** G. Royle. *17-Clue Sudoku Puzzles* (dataset; 49,151 essentially different solutions). School of Computer Science & Software Engineering, University of Western Australia. https://www.csse.uwa.edu.au/~gordon/sudokumin.php (⚠ original host may be offline; cited in [13])
15. **[15]** C.-M. Lin, M.-C. Wu and C.-C. Wei. *On Specific 17-Clue Sudoku Puzzles.* ICGA Journal, 36(3):131–138, 2013. DOI: [10.3233/ICG-2013-36302](https://doi.org/10.3233/ICG-2013-36302)
16. **[16]** E. D. Demaine, F. Ma, A. Schvartzman, E. Waingarten and S. Aaronson. *The Fewest Clues Problem.* Theoretical Computer Science, 748:28–39, 2018. DOI: [10.1016/j.tcs.2018.01.020](https://doi.org/10.1016/j.tcs.2018.01.020) (earlier: FUN 2016, DOI: [10.4230/LIPIcs.FUN.2016.12](https://doi.org/10.4230/LIPIcs.FUN.2016.12))
17. **[17]** D. Eppstein and X. (Cindy) Zhang. *Sudoku Grids That Require Many Clues.* arXiv:2607.05728, 2026. https://arxiv.org/abs/2607.05728
18. **[18]** H. Hatami and Y. Qian. *Teaching Dimension, VC Dimension, and Critical Sets in Latin Squares.* Journal of Combinatorics, 9(1):61–77, 2018. DOI: [10.4310/JOC.2018.v9.n1.a2](https://doi.org/10.4310/JOC.2018.v9.n1.a2); arXiv:1606.00032.
19. **[19]** H. Simonis. *Sudoku as a Constraint Problem.* 4th International Workshop on Modelling and Reformulating Constraint Satisfaction Problems (ModRef), at CP 2005. https://archive.modref.org/files/papers/2005/ModRef2005-02-Sudoku-as-a-Constraint-Problem.pdf
20. **[20]** A. B. Coelho. *A Scale to Measure the Difficulty of Sudoku Puzzles.* Revista de Ciências da Computação, II(2):39–55, 2007. DOI: [10.34627/rcc.v2i0.60](https://doi.org/10.34627/rcc.v2i0.60)
21. **[21]** M. Henz and M. S. Truong. *SudokuSat — A Tool for Analyzing Difficult Sudoku Puzzles.* In: Tools and Applications with Artificial Intelligence, SCI 166, pp. 25–35, Springer, 2009. DOI: [10.1007/978-3-540-88069-1_3](https://doi.org/10.1007/978-3-540-88069-1_3); PDF: https://www.comp.nus.edu.sg/~henz/publications/pdf/TAAI2009.pdf
22. **[22]** H. Nishikawa and H. Toda. *Exact Method for Generating Strategy-Solvable Sudoku Clues.* arXiv:2005.14098, 2020. https://arxiv.org/abs/2005.14098

### 7.3 Search heuristics

23. **[23]** R. M. Haralick and G. L. Elliott. *Increasing Tree Search Efficiency for Constraint Satisfaction Problems.* Artificial Intelligence, 14(3):263–313, 1980. https://haralick.org/journals/haralick_elliot.pdf
24. **[24]** ⚠ **UNVERIFIED VENUE.** X. Cazenave. *A Search Based Sudoku Solver.* (manuscript, LAMSADE — no venue/DOI located; cite by URL or omit.) https://www.lamsade.dauphine.fr/~cazenave/papers/sudoku.pdf
25. **[25]** P. San Segundo and V. Jiménez. *Using Graphs to Derive CSP Heuristics and Its Application to Sudoku.* IEEE ICTAI 2009. DOI: [10.1109/ICTAI.2009.78](https://doi.org/10.1109/ICTAI.2009.78)
26. **[26]** R. Lewis. *Metaheuristics Can Solve Sudoku Puzzles.* Journal of Heuristics, 13(4):387–401, 2007. DOI: [10.1007/s10732-007-9012-8](https://doi.org/10.1007/s10732-007-9012-8)
27. **[27]** Z. Chen. *Heuristic Reasoning on Graph and Game Complexity of Sudoku.* arXiv:0903.1659, 2009. https://arxiv.org/abs/0903.1659
28. **[28]** D. J. Crook. *A Pencil-and-Paper Algorithm for Solving Sudoku Puzzles.* Notices of the American Mathematical Society, 56(4):460–468, 2009. https://www.ams.org/notices/200904/tx090400460p.pdf
29. **[29]** S. Chi and D. Lange. *Techniques for Solving Sudoku Puzzles.* arXiv:1203.2295, 2013. https://arxiv.org/abs/1203.2295
30. **[30]** A. Pillay. *Finding Solutions to Sudoku Puzzles Using Human Intuitive Heuristics.* South African Computer Journal, no. 49, 2012. DOI: [10.18489/sacj.v49i0.111](https://doi.org/10.18489/sacj.v49i0.111)
31. **[31]** A. Biere. *SATCH — A SAT Solver Written in C* (software, v0.5.6rc). https://github.com/arminbiere/satch

### 7.4 Candidate citations searched for and NOT found (⚠ EXCLUDED — do not add without a new source)

| Candidate (from earlier notes) | Status | Verified substitute |
|---|---|---|
| Pope (2011), "A SAT-based approach for solving Sudoku" | No such paper located | [1], [2], [4] |
| Robson, "Sudoku satisfiability and its application to test compression" | No such J. M. Robson Sudoku work exists | [1] (extended encoding) |
| Qian & Sze, Sudoku complexity report | Not found (Y. Qian = Latin squares [18]; no Sze Sudoku report) | [11], [12] |
| Walsh, "Bit-Vector Encoding for Constraint Satisfaction" | Not found | [9] "SAT v CSP", [10] bit-vector ADC |
| Lewis & Thornton, "Sudoku Setter and Solver" | Not found | [26] Lewis 2007 |
| Kordík, Sudoku heuristics (P. Kordík) | No Sudoku paper by this author found | [25], [27] |
| Gordon & Traustason, "Unavoidable Sets of Sudoku Patterns" | Paper not found (Gordon's *data files* exist; concept documented in [13]) | [13] |
| Kinber, inference-based search heuristics for Sudoku | Not found | [19], [25], [27] |
