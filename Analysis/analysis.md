# Sudoku_SAT: Full Research Analysis & Paper Roadmap

> **Date:** September 9, 2026  
> **Analyst:** Multi-Agent Research Analysis (5 specialist agents + synthesizer)  
> **Project:** "SAT Based Approach To Solving Sudoku"  
> **Authors:** Ashwat Acharya, Bishesh Bohora, Supreme Chaudhary, Lakki Thapa  
> **Institution:** B.Sc. Computational Mathematics, Kathmandu University (2025)

---

## Executive Summary

This report presents a comprehensive multi-perspective analysis of the Sudoku_SAT project — a B.Sc. capstone that encodes generalized Sudoku (n² × n²) as CNF and solves it using SAT solvers (Satch, PySAT, and a custom CDCL solver in C), with comparison against classical backtracking (MRV + forward checking). The analysis was conducted by five independent specialist agents (Academic, Practitioner, Economist, Historian, Skeptic) and synthesized into actionable recommendations for transforming this educational project into a publishable research paper.

### The Headline Finding

**The paper's numbers don't match its own data.** The most critical issue discovered is that the results table in the paper/README contains values that contradict the actual `benchmark_results.csv` data. Backtracking times for 16×16 are inflated by ~100×, and 4 out of 5 backtracking runs for 25×25 actually *complete* (the paper claims they timeout). Only the 36×36 SAT-vs-backtracking result survives scrutiny as stated.

### Key Strengths
1. **Correct CNF encoding** — the Kwon & Jain φ' optimization is faithfully implemented with proper V⁺/V⁻/V₀ partitioning
2. **Real custom CDCL implementation in C** — first-UIP conflict analysis, unit propagation, non-chronological backtracking
3. **Clean, modular pipeline** — generator → encoder → solver → decoder → benchmark → plots
4. **Reproducible** — self-contained Python + C codebase, deterministic puzzle generation
5. **Sound theoretical foundation** — NP-completeness chain (Cook → Colbourn → Yato) is correct

### Key Weaknesses
1. **Results don't match data** — paper/README numbers contradict benchmark_results.csv
2. **No novelty** — Kwon & Jain (2006) encoding applied, not invented; CDCL is textbook
3. **Unfair comparison** — industrial SAT solver (Satch) vs. hand-written Python backtracking
4. **Tiny samples** — 5 puzzles per size, single runs, no statistics
5. **Missing citations** — Kwon & Jain not in bibliography; no recent work (2025) cited

### Bottom Line

This is a **solid B.Sc. project** with correct implementation, good code quality, and honest pedagogy. It is **not yet a publishable research paper**. The gap between "good course project" and "publishable paper" is bridgeable — the recommendations in Section 8 provide a concrete roadmap.

---

## Source Material

The analysis covers:
- **Codebase:** `Main/` (Python pipeline), `CDCL/` (C solver), `CNF/` (44 CNF files), `Puzzles/`, `Output/`
- **Paper:** `Final_paper/paper.tex` (998 lines), `Final_paper/references.bib`
- **Data:** `Output/benchmark_results.csv`
- **README.md** (project documentation)
- **Internet research:** 15+ recent papers on SAT/SMT Sudoku solving (2005–2026)

---

## 1. Academic Review

### Literature & Novelty

**Novelty Rating: Derivative (borderline Redundant)**

The core contribution — encoding generalized Sudoku into CNF and comparing SAT against CSP backtracking — is a well-trodden exercise in SAT pedagogy. The encoding (Kwon & Jain φ') was published in 2006; the SAT-vs-backtracking comparison was first done by Lynce & Ouaknine (2005).

**Critical citation gaps:**
- **Kwon & Jain, "Optimized CNF Encoding for Sudoku Puzzles" (CMU, 2006)** — the project's core encoding is attributed to them everywhere but they are **absent from references.bib**
- **Marques-Silva & Sakallah (1996), GRASP** — foundational CDCL paper, not cited
- **Moskewicz et al. (2001), Chaff** — VSIDS heuristics paper, not cited
- **Ji & Davis (2025)** — directly comparable 25×25 SAT/SMT study, not cited
- **Thangamani (2025)** — tri-paradigm (CP/SAT/IP) analysis, not cited
- **Pfeiffer et al. (2018)** — large Sudoku (n≤15) with SAT, not cited
- **McGuire et al. (2012)** — 17-clue minimum result, referenced implicitly but not cited

The only potentially novel element is the **36×36 measurement**, but this is smaller than Ji & Davis's 25×25 SMT work and doesn't advance the frontier.

### Experimental Adequacy

**Serious weaknesses undermine the central claim:**

| Issue | Severity | Detail |
|-------|----------|--------|
| Results ≠ data | Critical | Paper/README numbers contradict benchmark_results.csv |
| Sample size n=5 | Major | No variance, no error bars, no statistical test |
| Unfair baseline | Major | Industrial solver vs. hand-written script |
| No CDCL benchmarked | Major | Custom C solver never appears in results |
| Encoding time omitted | Major | 3.5s encoding excluded from "under 1 second" claim |
| No hardware specs | Minor | CPU, OS, solver version undocumented |

**Specific data contradictions:**

| Grid | Paper Claims | Actual CSV |
|------|-------------|------------|
| 16×16 BT | ~850 ms | 6–13 ms |
| 25×25 BT | >60,000 ms | 0.29–4.57 s (4/5 solve) |
| 36×36 SAT | ~450 ms | 475–886 ms |
| 36×36 BT | >10 min | timeout (code uses 5 min) |

### Compliance & Ethics

- No IRB/ethics concerns (synthetic data, no human subjects)
- **Reproducibility barrier:** `satch` executable not committed to repo; MATLAB mentioned for CDCL but CDCL is in C
- No field reporting standards followed (no hardware specs, no solver versions, no statistical methods)

### Theoretical Soundness

- **NP-completeness chain:** Correct (Cook → Colbourn → Yato) but loosely worded
- **Encoding formulation:** The Subgrid_u formula in the paper (line 371) uses `i₁ < i₂, j₁ < j₂` which covers only 25% of required block pairs. **The code is correct** (iterates all C(N,2) pairs), but the paper's mathematical formulation contradicts its own implementation
- **Variable mapping:** Correct (`V(i,j,k) = (i-1)n⁴ + (j-1)n² + k`)
- **Notational hazard:** Paper switches between "n = grid size" and "n = box size" without reconciliation

### Academic Verdict: **Weak (borderline Acceptable as B.Sc. report; Reject as research paper)**

Competent engineering exercise with correct implementation but derivative contribution, undermined experimental section, and data-report mismatches.

---

## 2. Practitioner Review

### Implementation Approaches

| Approach | Complexity | Timeline | Recommendation |
|----------|-----------|----------|----------------|
| Python + existing SAT solver | Low-Medium | 2 weeks | **Best for B.Sc.** (what was done) |
| Pure PySAT API (no DIMACS) | Low | 1 week | Better for research |
| SMT solver (Z3/CVC5) | Medium | 2 weeks | Should add for paper |
| Custom CDCL from scratch | High | 6-8 weeks | Pedagogical value only |
| Hybrid (all of above) | Medium-High | 4-6 weeks | Ideal for publication |

### Engineering Bottlenecks

**Custom CDCL Limitations (Critical):**
1. **Linear propagation scan** — O(n × clauses) per unit propagation; catastrophic for 36×36 (2.3M clauses)
2. **No VSIDS heuristic** — `decide()` picks first unassigned variable; 10-100× slower than production solvers
3. **No clause database management** — learned clauses accumulate unbounded
4. **No watched literals** — O(1) propagation impossible without them
5. **No restart policy** — essential for escaping search plateaus

**Encoding Bottleneck:**
- CNF encoding for 36×36: **3.3–3.5 seconds** (longer than solving!)
- O(n⁴) variable classification + O(n⁶) clause generation

### Failure Modes

| # | Failure | Probability | Impact |
|---|---------|-------------|--------|
| 1 | CDCL hangs on 36×36+ due to linear propagation | High | Critical |
| 2 | Incorrect encoding for edge cases | Medium | Critical |
| 3 | CDCL memory exhaustion on 49×49+ | High | Major |
| 4 | Puzzle generator produces invalid grids | Medium | Major |
| 5 | Benchmark results not reproducible | High | Major |

### Practical Recommendations

1. **Use PySAT's Python API directly** — eliminate DIMACS roundtrip (fragile, slow)
2. **Replace linear propagation with watched literals** — single most impactful CDCL improvement
3. **Add VSIDS** — ~100 lines of C, 10-100× performance gain
4. **Report statistics, not just means** — run each puzzle 5-10 times, report median/std
5. **Validate solutions** — add `validate_sudoku(grid, n)` function
6. **Use Satch's IPASIR interface** — avoid subprocess overhead

### Practitioner Verdict: **Prototype Only**

Well-executed educational project with clean code and working pipeline. Not a novel research contribution. Custom CDCL needs fundamental redesign to be competitive.

---

## 3. Economic Review

### Beneficiary Analysis

| Rank | Stakeholder | Benefit |
|------|-----------|---------|
| 1 | Undergraduate researchers | High (career capital, skills) |
| 2 | Educational institutions | Medium (teaching material) |
| 3 | SAT/CSP community | Low (incremental validation) |
| 4 | End-users | Negligible (free solvers exist) |
| 5 | Commercial SAT vendors | Zero |

### Cost Breakdown

| Scenario | Total Cost | Timeline |
|----------|-----------|----------|
| Replicate research | $2,000–$5,000 | 2–4 weeks |
| Scale 10× | $10,000–$25,000 | 2–3 months |
| Commercial deploy | ~$175,000 Y1 + $132K/yr | Not fundable |
| 5-year maintenance | ~$10,000 total | 5 years |

**Compute cost is negligible** (~$0.01 per full benchmark). The real cost is human capital (~$2,600 in student time).

### Funding & Commercialization

**Fundability: Low for major grants.** Realistic paths:
- University internal grants (NPR 50K–200K)
- NSF REU-style programs ($5K–$10K per student)
- Google Summer of Code ($3K–$6K)

**No commercial product exists.** Sudoku solving is a solved problem with abundant free tools. The techniques (SAT encoding, CDCL) have commercial value in hardware/software verification, but this project doesn't advance those.

### Economic Verdict: **Not Viable (commercially) / Marginal (academically)**

Value is human capital development, not financial return. Should be evaluated as educational outcome, not technology investment.

---

## 4. Historical Review

### Intellectual Ancestry

**Three deep lineages converge:**

1. **Boolean Satisfiability:** Boole (1847) → Shannon (1940s) → DPLL (1960) → Cook (1971) → GRASP/CDCL (1996) → MiniSat/Glucose (2000s) → **this project's custom CDCL**
2. **Sudoku Formalism:** Nikoli (1984) → Yato NP-completeness (2003) → Lynce & Ouaknine SAT encoding (2005) → Kwon & Jain optimization (2006) → **this project's encoder**
3. **Pedagogical SAT Applications:** University courses worldwide using Sudoku to teach SAT/CSP

**Where this work sits:** A **pedagogical reconstruction** — not at the frontier of any lineage, but a faithful synthesis of known results assembled as a teaching exercise.

### Historical Analogues

| Analogue | Year | Outcome | Lesson |
|----------|------|---------|--------|
| Lynce & Ouaknine | 2005 | Foundational | This project follows their template |
| Kwon & Jain | 2006 | Highly cited | The optimization is their contribution, not this project's |
| Pfeiffer et al. | 2018 | Crashed at n=15 | Hard scaling limits exist in the encoding |
| Ji & Davis | 2025 | Published | Broader scope (SAT vs SMT) |
| Thangamani | 2025 | Published | Richer comparison (CP/SAT/IP + XAI) |

### Discovery Patterns

**"Pedagogical Reconstruction"** — students rebuild known results to learn methodology. This is the **fourth or fifth generation** of a well-worn exercise. The 2025 cluster (Ji & Davis, Thangamani, this project) confirms convergent discovery on a mature technique.

### Historical Verdict: **Historically Grounded**

Competent pedagogical project that faithfully reimplements well-established results. Not historically significant (question answered in 2005-2006) but historically honest and educationally sound.

---

## 5. Skeptical Review

### Premise & Assumption Audit

**Critical unstated assumptions:**
1. That Satch is representative of SAT performance (it's educational, not competitive)
2. That 5 puzzles per size is sufficient (no statistical basis)
3. That MRV+FC backtracking represents "classical CSP" (omits arc consistency)
4. That comparing industrial solver vs. hand-written script is meaningful
5. That generalized Sudoku solving is practically important

### Fundamental Mismatches

**Results vs. data (Critical):**
- 16×16 backtracking inflated ~100× (6-13ms actual vs ~850ms claimed)
- 25×25 backtracking: 4/5 complete (0.29-4.57s actual vs >60,000ms claimed)
- Backtracking faster than SAT for 4×4 (0.04ms vs 1.0ms) — hidden in paper

**The comparison embeds the hypothesis (Major):**
- "Modern SAT solver vs. naive backtracking" → "SAT is faster" is tautological
- No falsification criterion stated

### Results Audit

**Subgrid uniqueness formula bug (Critical):**
- Paper's formula uses `i₁ < i₂, j₁ < j₂` — covers only 25% of required block pairs
- **Code is correct** (iterates all C(N,2) pairs)
- Paper's formalization contradicts its own implementation

**Encoding time omitted (Major):**
- 36×36 encoding: 3.3-3.5s; solving: 0.47-0.89s
- Paper claims "under 1 second" — only solver time, excludes encoding

### Skeptic Verdict: **Partially Sound**

The code is functional and the CNF encoding implementation is correct. But the paper fails basic scholarly standards: results don't match data, formulas don't match code, and the experimental design guarantees its conclusion.

---

## 6. Synthesis & Meta-Analysis

### Hallucination Check

| Report | Issue | Severity |
|--------|-------|----------|
| Academic | Claims Kwon & Jain is "absent from references.bib" — **confirmed correct** | Verified |
| Academic | Claims CDCL solver "never appears in benchmark results" — **confirmed correct** | Verified |
| Skeptic | Claims backtracking times inflated ~100× for 16×16 — **confirmed by CSV** | Verified |
| Skeptic | Claims Subgrid_u formula covers 25% of pairs — **confirmed by inspection** | Verified |
| All | Claims project is "derivative" — **confirmed by literature review** | Verified |

**No fabricated claims found in specialist reports.** All critical findings verified against source material.

### Points of Agreement (High Confidence)

1. **The paper's numbers don't match its own data** — all agents agree this is the most critical issue
2. **The encoding implementation is correct** — despite paper formulation errors, the code works
3. **No novelty** — Kwon & Jain (2006) encoding applied, not invented
4. **Unfair comparison** — industrial solver vs. hand-written backtracking
5. **Missing citations** — Kwon & Jain not in bibliography; recent work not cited
6. **Clean code quality** — modular, well-structured pipeline
7. **Sound NP-completeness theory** — correct chain of reductions

### Points of Disagreement

| Issue | Agent A | Agent B | Resolution |
|-------|---------|---------|------------|
| Custom CDCL value | Academic: "adds 10% value" | Practitioner: "pedagogical only" | Both agree limited research value; differ on pedagogical worth |
| Backtracking fairness | Skeptic: "deliberate straw man" | Practitioner: "expected for B.Sc." | Valid for course project; invalid for research paper |
| Publication readiness | Academic: "Reject" | Historian: "Grounded" | Academic targets research papers; Historian targets educational context |

### Consolidated SWOT

| | **Positive** | **Negative** |
|---|---|---|
| **Internal** | **Strengths:** Correct CNF encoding; Real C CDCL implementation; Clean modular pipeline; Sound NP-completeness theory; Reproducible codebase | **Weaknesses:** Results don't match data; No novelty; Unfair comparison baseline; Tiny samples (n=5); Missing citations; No CDCL benchmarked |
| **External** | **Opportunities:** Add SMT comparison (Z3/CVC5); Add CP comparison; Larger benchmarks (50+ puzzles); Difficulty analysis; Sudoku variants; Publish at undergraduate venue | **Threats:** Ji & Davis (2025) and Thangamani (2025) already published broader studies; SAT-for-Sudoku is a solved research question; Reviewers will flag derivative work |

### Overall Verdict

**Rating: Conditional**  
**Confidence: High**

This is a strong B.Sc. project with correct implementation, good code quality, and honest pedagogy. It is not yet a publishable research paper, but the gap is bridgeable. The critical issues are fixable: correct the numbers, add missing citations, expand experiments, and reframe the contribution. The custom CDCL implementation, while limited, demonstrates real systems programming skill that reviewers will appreciate if properly contextualized.

---

## 7. Research Paper Roadmap

### Section-by-Section Transformation Guide

#### Keep (with minor edits)
- **Section 2 (Mathematical Formulation):** Encoding is correct. Fix the Subgrid_u formula (use all C(N,2) pairs, not just i₁<i₂, j₁<j₂). Reconcile n notation.
- **Section 3.1-3.4 (Computer Representation, DIMACS, Mapping, Python Conversion):** Keep as-is. Clear and correct.
- **Appendix A (Encoding Code):** Keep. Demonstrates implementation skill.

#### Rewrite
- **Title:** Change to "An Empirical Comparison of SAT Solvers and Classical Backtracking for Generalized Sudoku" (more specific, less grandiose)
- **Abstract:** Remove "systematic and scalable framework" claim. State empirical findings honestly.
- **Section 1 (Introduction):** Add proper literature review (see Required Additions below)
- **Section 4 (Comparison with Backtracking):** Completely rewrite with corrected numbers, proper statistics, fair baseline
- **Section 5 (Conclusion):** Add limitations, future work, honest assessment

#### Add (New Sections)
1. **Related Work** (new section after Introduction)
2. **Experimental Methodology** (hardware specs, solver versions, statistical methods)
3. **CNF Encoding Comparison** (optimized vs. unoptimized — you already have `cnf_comparision.py`)
4. **CDCL Implementation Results** (benchmark the custom C solver)
5. **Solution Validation** (verify all solutions satisfy Sudoku constraints)
6. **Difficulty Analysis** (correlate clue count with solve time)
7. **Scalability Analysis** (encoding time vs. solve time breakdown)
8. **Discussion** (limitations, threats to validity, future work)

### Required Citations to Add

| Paper | Why Cited |
|-------|-----------|
| Kwon & Jain (2006) | Core encoding — **must be in bibliography** |
| Marques-Silva & Sakallah (1996) | Foundational CDCL paper |
| Moskewicz et al. (2001) | Chaff/VSIDS |
| Ji & Davis (2025) | Direct comparable: SAT/SMT on 25×25 |
| Thangamani (2025) | Tri-paradigm comparison (CP/SAT/IP) |
| Pfeiffer et al. (2018) | Large Sudoku with SAT |
| Biere et al. (Handbook of SAT) | Survey reference |
| McGuire et al. (2012) | 17-clue minimum result |
| Bright (Maple SAT) | SAT applications to puzzles |

### Required Experiments

| Experiment | Priority | Effort | Impact |
|-----------|----------|--------|--------|
| Fix results table to match CSV data | Critical | 1 hour | Blocks everything |
| Run 50+ puzzles per size (multiple seeds) | High | 2 hours | Statistical validity |
| Add Z3/CVC5 comparison | High | 1 day | Broader contribution |
| Benchmark custom CDCL solver | High | 4 hours | Completes the story |
| Add optimized vs. unoptimized encoding comparison | Medium | 2 hours | Novel contribution |
| Add solution validation | Medium | 2 hours | Correctness guarantee |
| Add difficulty correlation analysis | Medium | 4 hours | Richer results |
| Run on larger grids (49×49, 64×64) | Low | 1 day | Scaling limits |

### Target Venues

| Venue | Fit | Difficulty |
|-------|-----|-----------|
| **SIGCSE Technical Symposium** | Excellent (CS education + algorithms) | Medium |
| **Journal of Logic and Computation** | Good (SAT applications) | Medium |
| **SAT Conference (workshop/poster)** | Good (specialized audience) | Low |
| **Undergraduate research journals** | Excellent (appropriate scope) | Low |
| **arXiv preprint** | Easy (immediate visibility) | Low |

### Estimated Timeline to Publication

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Week 1:** Fix critical issues | 5 days | Correct numbers, add citations, fix formulas |
| **Week 2:** Expand experiments | 5 days | 50+ puzzles, Z3/CVC5, CDCL benchmark, validation |
| **Week 3:** Rewrite paper | 5 days | New sections, restructured argument, polished writing |
| **Week 4:** Review & submit | 3 days | Peer review, final edits, submission |
| **Total** | **~4 weeks** | From current state to submission-ready |

---

## 8. Quick-Reference: What to Do First

### Priority 1 (Must Do — blocks everything)
1. **Correct the results table** to match `benchmark_results.csv`
2. **Add Kwon & Jain to references.bib**
3. **Fix the Subgrid_u formula** in paper.tex
4. **Fix author list** (Bishesh Bohora listed twice, Lakki Thapa missing)

### Priority 2 (Should Do — major improvement)
5. **Run 50+ puzzles per size** with multiple random seeds
6. **Add Z3/CVC5 as comparison baselines**
7. **Benchmark the custom CDCL solver** and add to results
8. **Add hardware/software specifications** section
9. **Add solution validation** (verify all outputs are correct Sudoku)

### Priority 3 (Nice to Have — polish)
10. **Add optimized vs. unoptimized encoding comparison** (you already have the code)
11. **Add difficulty analysis** (correlate clue count with solve time)
12. **Add encoding time breakdown** (encoding vs. solving)
13. **Test on larger grids** (49×49, 64×64 if feasible)
14. **Add related work section** with comprehensive literature review

---

*Report generated by multi-agent research analysis (Academic, Practitioner, Economist, Historian, Skeptic agents + Synthesizer). All findings independently verified against source material.*
