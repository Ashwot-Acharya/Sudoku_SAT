# Unique-Solution Sparse Generalized Sudoku

## Question

Can a unique-solution generalized Sudoku of size `N x N`, where `N = k^2` and the boxes are `k x k`, be generated with fewer than 50% of its cells filled? In particular, what is known for 16x16, 25x25, and 36x36, how sparse can published puzzles be, and what method should this project use given its pure-Python + CaDiCaL constraint?

Throughout, “clue” and “given” are synonymous. A *defining set* is a set of clues with a unique completion. A *minimal* puzzle is one from which no clue can be removed without losing uniqueness. A *minimum* puzzle is one of smallest possible cardinality. The two notions are different: a minimal puzzle can have many more clues than the minimum.

## Executive Verdict

**Yes, unique-solution generalized Sudoku below 50% fill is possible, and 25% fill is provably achievable for every size `N = k^2`.** Mahdian and Mahmoodian give a construction based on back-circulant Latin squares with at most `floor(N^2/4)` clues [1]. For 16x16, 25x25, and 36x36 that is 64, 156, and 324 clues respectively, i.e. exactly 25% fill. Qiuyanzhe independently described the same `floor(N^2/4)` pattern on the EnjoySudoku forum [6].

The important qualification is that **this is an existence/construction result, not what a generic random generator produces**. Published uniqueness-preserving generators converge much higher:

| Size | Best known puzzle | Best known fill | Typical published generator |
|---|---:|---:|---:|
| 16x16 | 55 clues (community; 56 also published) | 21.5% | 94 clues, 36.7% median [4]; 35-36% [5] |
| 25x25 | 146 clues (community “world least”) | 23.4% | 269 clues, 43.0% median [4]; 41-43% [5] |
| 36x36 | 324 clues by construction [1,6] | 25.0% | 677 clues, 52.2% median [4]; no completed Stojadinović run [5] |

So the correct answer depends on the requirement:

- **If the requirement is “a unique puzzle with <50% fill”**: yes. Use the Mahdian/Qiuyanzhe construction, or a known sparse puzzle, and randomize it with Sudoku symmetries.
- **If the requirement is “a random full grid, then remove clues until unique”**: at 16x16 and 25x25, yes, comfortably (35-43%). At 36x36, published evidence does **not** support routinely getting below 50%; the observed median is 52.2%, and the one published generator that reports 36x36 generation says it did not finish even after several hours [5].
- **If the requirement is “find the minimum number of clues”**: open for 16x16, 25x25, and 36x36. Only 4x4 and 9x9 are solved (4 and 17 clues) [3,8].

For this project, the defensible plan is: implement the 25% construction first as a guaranteed sparse generator, then implement a Stojadinović-style removal + CaDiCaL uniqueness loop for 16x16 and 25x25 to obtain varied 35-45% puzzles. For 36x36, either use the construction (25%) or explicitly report that a generic SAT-based minimizer typically lands near 50-52%; do not promise a random <50% 36x36 puzzle without a structured grid.

## Theory & Lower Bounds

### The basic lower bound is weak

A proper `N x N` Sudoku puzzle must contain at least `N - 1` distinct symbols among its clues. If two symbols were completely absent, swapping them throughout any solution would produce a second solution. Each present symbol needs at least one clue, so at least `N - 1` clues are necessary [11]. For 16x16, 25x25, and 36x36 this is only 15, 24, and 35 clues; it says nothing about a 50% threshold.

### Defining sets, critical sets, and unavoidable sets

A Sudoku solution is a Latin square with the additional box constraint. A defining set is a partial Sudoku square with a unique completion. The smallest defining set is the minimum-clue problem. This is the Sudoku case of the classical critical-set problem for Latin squares.

The standard combinatorial tool is the *unavoidable set*: a set of cells whose entries can be changed in a cycle while preserving all row, column, and box constraints. Every proper puzzle must contain at least one clue in every unavoidable set; otherwise the cycle yields a second solution. Thus any proper puzzle is a hitting set for the family of unavoidable sets. McGuire, Tugemann, and Civario used this fact, enumerating unavoidable sets of size at most 12 for 9x9, to prove that no 16-clue puzzle exists [3]. For larger grids, the number and size of unavoidable sets grow rapidly, which is why the same approach becomes expensive.

### The 25% upper bound

Mahdian and Mahmoodian prove that for Sudoku squares of order `N = k^2`, the smallest defining set has size at most `floor(N^2/4)` [1]. Their construction starts from a back-circulant Latin square and applies a permutation of rows; for Sudoku it gives a partial square with `floor(N^2/4)` clues and a unique completion. Qiuyanzhe’s forum construction is the same idea and explicitly gives `floor(n^2/4)` givens for arbitrary size, with 156 givens for 25x25 [6]. For the sizes relevant here:

| Grid | `floor(N^2/4)` | Fill |
|---|---:|---:|
| 16x16 | 64 | 25.0% |
| 25x25 | 156 | 25.0% |
| 36x36 | 324 | 25.0% |
| 49x49 | 600 | 25.0% |
| 64x64 | 1024 | 25.0% |

This is an **upper bound on the minimum**, not a lower bound. It proves that no general theorem can force more than 25% fill.

### What is known about the true minimum

For Latin squares, the minimum defining-set size is conjectured to be `floor(N^2/4)`, and the same conjecture is natural for Sudoku. Mahdian and Mahmoodian conjecture that the smallest Sudoku defining set is `Theta(N^2)` [1]. The best proven lower bound for defining sets is only slightly superlinear; for the stricter notion of a *forcing set* they prove a `Theta(N^2)` lower bound [1]. Thus the asymptotic order is believed to be quadratic in `N`, i.e. a constant fraction of the `N^2` cells, but the constant is not known.

Eppstein and Zhang study a different quantity: for a *fixed* completed grid, what is the fewest clues needed to force that particular grid? They prove that a majority of filled `n^2 x n^2` grids require `n^4 - O(n^4 / log n)` clues, i.e. almost every cell must be a clue, leaving only a logarithmic fraction empty [2]. They construct 9x9 and 16x16 grids requiring 18 and 80 clues respectively. They also note that some puzzles can be uniquely specified with `floor(n^4/4)` clues [2]. This contrast is crucial: **sparse puzzles are special, not typical**. A random completed grid is usually a bad starting point if the goal is a sparse puzzle.

Eppstein and Zhang state that 16x16 Sudoku is “conjectured to require 56 clues” [2]. That figure should be treated cautiously: a 55-clue 16x16 puzzle has been reported and extracted on the EnjoySudoku forum, and Sudoku Theory lists 55 as the best known [7,8]. The 56-clue puzzle is the well-documented published construction from 2011 [7]. The 55-clue puzzle’s minimality is not proven. The apparent 55-versus-56 conflict is best reported as “55 best known, 56 published and conjectured by some authors,” not as a settled minimum.

## Published Generators & Achievable Fills

### Stojadinović 2015: removal plus SAT uniqueness

Stojadinović’s “Solving and generating large Sudoku puzzles by reduction to SAT” is the most directly relevant generator paper [5]. The method starts from a complete solution and randomly removes clues while the fill is above 20%. At that point the puzzle normally has many solutions. A second phase uses SAT (the meSAT system) with cardinality constraints to restore uniqueness: it removes or fills cells and checks whether the puzzle again has exactly one solution. The generated puzzles are unique, and removing any remaining prefilled number destroys uniqueness (local minimality).

The reported generation results for 100 puzzles per size are:

| Size | Original generation | Modified generation | Modified + preprocessing |
|---|---:|---:|---:|
| 16x16 | 36% fill | 35% fill | 35% fill |
| 25x25 | 43% fill | 41% fill | 41% fill |
| 36x36 | not completed | not completed | not completed |

These are average fill percentages from Table 3 of [5]. The paper states that generation for 36x36 did not finish even after several hours, so no 36x36 generation results are reported. This is strong evidence that a straightforward remove-and-check loop hits a practical wall at 36x36.

The same paper’s solving experiments are also relevant to cost: on 400 36x36 instances, the SAT approach solved 384 within a 300-second-per-instance limit, using 7231 seconds total, i.e. about 18 seconds per solved instance on average [5]. Solving a 36x36 puzzle is therefore feasible; *proving uniqueness during repeated clue removal* is the expensive part.

### Lagerkvist 2026: large reproducible corpus

Lagerkvist’s “Scaling Sudoku as a Constraint Problem” generates 32,000 unique-solution base puzzles and 402,201 easier variants up to 36x36 [4]. The generator starts from a complete grid, removes clues in randomized batches while preserving uniqueness, and refines toward single-clue removal. Uniqueness is checked with a two-solution CP-SAT model: the first solution is blocked before searching for a second, so the known complete grid cannot be returned twice. The 16x16 and 25x25 bases are minimal; the 36x36 bases are unique but usually not certified minimal because the final pass has a timeout.

The published medians are:

| Size | Median clues | Median fill | Propagation-only solved |
|---|---:|---:|---:|
| 6x6 | 10 | 27.8% | 100% |
| 9x9 | 24 | 29.6% | 100% |
| 16x16 | 94 | 36.7% | 84.9% |
| 25x25 | 269 | 43.0% | 0% |
| 36x36 | 677 | 52.2% | 0% |

The 36x36 corpus is explicitly a distribution produced by this generator, not a minimum-clue corpus. Only 0.2% of the 36x36 bases have an exact local-minimality certificate [4]. The corpus is available at [12].

This is the cleanest quantitative statement available: **a modern, well-engineered uniqueness-preserving generator reaches 36.7% at 16x16 and 43.0% at 25x25, but 52.2% at 36x36.** It does not prove that 36x36 below 50% is impossible; the 25% construction does the opposite. It shows that the generic removal process stops near 50% at that size.

### Community records

The EnjoySudoku “Minimum givens on larger puzzles” thread is the main record for large sparse puzzles [7]. Key entries:

- 16x16: a 55-clue puzzle was posted in 2015 and later extracted and analyzed by m_b_metcalf. A 56-clue puzzle was posted by T_Shirakawa in 2011. The 55-clue puzzle is the best known; minimality is unproven.
- 25x25: ton posted a 146-clue puzzle in 2019, described as “25x25(5x5), 146-clue I think minimum number is 140.” The same puzzle appears in a Japanese SAT article as “146 hints (currently the world’s fewest)” [7]. It is the best known; minimality is unproven. Some older pages say 151 or 156; those are outdated or construction values, not the record.
- 36x36: no low-clue record comparable to 55/146 was found. Forum constructions for 36x36 are locally minimal at roughly 52% fill (48% of clues removed from a full grid) [7]. The `floor(N^2/4)=324` construction is the strongest published upper bound at 25%.

A forum table summarizing the known large-puzzle records gives the proportions: 16x16 55/256 = 0.2148, 25x25 146/625 = 0.2336 [7]. The same table shows 9x9 17/81 = 0.2099. The empirical best fills for 9x9, 16x16, and 25x25 are all in the 21-23% range, consistent with the `floor(N^2/4)` conjecture being close to tight for these specially constructed grids.

### What “best fill” means for 36x36

There are two different 36x36 answers:

1. **Existence / structured construction:** 324 clues, 25.0%, by the Mahdian/Qiuyanzhe construction [1,6]. This is a valid unique puzzle if the construction is implemented correctly.
2. **Generic random generator:** 677 clues, 52.2% median [4]; Stojadinović did not complete 36x36 generation [5]; forum hand-minimized 36x36 puzzles sit near 52% [7].

If the project’s claim is “we can generate unique 36x36 puzzles below 50%,” the construction is the only defensible route supported by current evidence. If the claim is “our random generator reaches below 50% at 36x36,” the published evidence does not support it, and the project should either demonstrate it empirically with a substantial sample or weaken the claim.

## Why <50% Is Hard

### 1. It is not a mathematical barrier

There is no known theorem saying that a proper generalized Sudoku needs more than 50% of its cells filled. The 25% construction refutes any such general claim. The 50% figure is a **practical and typical-case barrier**, not a proven lower bound.

### 2. Uniqueness is a second-solution problem

Checking that a puzzle is proper means checking that there is no second solution. This is the “another solution problem” (ASP), which is ASP-complete for Sudoku; deciding whether a partial Sudoku has a solution is NP-complete [9,11]. In practice, SAT solvers can solve large puzzles quickly when many clues remain, but proving that no second solution exists becomes much harder as clues are removed. The solver must refute every alternative near-solution, not just find one completion.

### 3. Sparse puzzles live on special grids

Eppstein and Zhang show that most complete grids require almost all cells as clues [2]. A random full grid is therefore likely to have a high minimum clue count. The 25% construction works because it uses a highly structured back-circulant Latin square, not a random grid. This is the single most important design lesson: **choose the solution grid for sparsity; do not expect a random grid to admit a sparse defining set.**

### 4. The near-solution explosion

As clues are removed, many unavoidable sets become unhit, and the number of ways to complete the partial grid grows. A SAT uniqueness check then has to explore a large search space of near-solutions. The transition is not a sharp phase transition in the existence of a unique completion; it is a gradual increase in the cost of proving uniqueness. Stojadinović observes that uniqueness is typically reached around 50% fill in the first phase, then spends substantial extra time reducing below that [5].

### 5. Empirical evidence

- Stojadinović: 16x16 35-36%, 25x25 41-43%, 36x36 not completed after hours [5].
- Lagerkvist: 16x16 median 36.7%, 25x25 median 43.0%, 36x36 median 52.2% [4].
- Community bests: 16x16 21.5%, 25x25 23.4% [7], but these are specially searched/constructed puzzles, not typical generator output.
- 36x36 forum puzzles: around 52% fill after local minimization [7].

### Pilot check in this project

A single 36x36 base puzzle from the Lagerkvist corpus with 695 clues (53.6% fill) was encoded as a one-hot CNF with sequential cardinality constraints (540,433 clauses) and checked with CaDiCaL. The uniqueness proof, using a 1296-literal blocker for the known solution, took 1356.7 seconds (about 22.6 minutes) on this machine. A subsequent greedy one-clue-removal pass did not finish within the remaining budget; a prototype constraint-propagation solver also failed to finish a full uniqueness check within 600 seconds. This is a single-instance pilot, not a benchmark, but it illustrates the practical cost: a greedy pass needs hundreds of such checks, so naive 36x36 minimization is not viable without a much stronger strategy.

## Candidate Methods for This Project

### A. Structured construction (recommended first)

Implement the Mahdian/Qiuyanzhe back-circulant construction for arbitrary `N = k^2` [1,6]. It gives `floor(N^2/4)` clues and is pure Python. Randomize the result with Sudoku symmetries (digit relabeling, row/column permutations within bands/stacks, band/stack permutations, transposition) to produce many distinct puzzles from the same pattern. This is the only method that gives a **guaranteed** <50% result at 36x36, 49x49, and 64x64 without relying on a SAT search.

Strengths: guaranteed clue count, fast, seed-reproducible, no solver dependency. Weaknesses: structured puzzles may be easy (often singles-only), and the pattern is not a random sample of all sparse puzzles. If the project needs “playable” puzzles, add clues or choose a different construction variant.

### B. Stojadinović-style remove and restore

For 16x16 and 25x25, implement the two-phase method [5]:

1. Generate a random complete solution grid.
2. Remove clues randomly until about 20% fill remains.
3. Repeatedly use a SAT uniqueness check to restore or remove clues until the puzzle is unique and locally minimal.

This is the best documented route to varied 35-43% puzzles. Use an efficient encoding, keep the known solution, and block it before asking for a second solution. A cardinality/sequential encoding is much smaller than naive pairwise clauses. Expect the uniqueness checks near the end to dominate the runtime.

### C. Greedy minimization from a known sparse puzzle

Start from a known unique puzzle (e.g. the 55-clue 16x16 or 146-clue 25x25, or a construction at 25%) and try removing one clue at a time:

- Remove a clue.
- Solve with the remaining clues and a blocker for the known solution.
- If UNSAT, keep the removal; if SAT, restore the clue.
- Repeat in random order, possibly multiple passes.

This produces a locally minimal puzzle, not a globally minimum one. It is effective at 16x16 and 25x25, but at 36x36 each uniqueness check can be very expensive, as the pilot shows. Use batching, symmetry, and a per-check timeout; do not expect a full pass on 36x36 with a pure-Python + CaDiCaL loop.

### D. Unavoidable-set / hitting-set search

Enumerate small unavoidable sets, find a small hitting set, then verify uniqueness with SAT [3]. This is the method that proved the 9x9 minimum and is the principled way to search for very low clue counts. It is also the most implementation-heavy: enumerating all relevant unavoidable sets for 16x16 is already a substantial project, and 36x36 is likely out of reach for a B.Sc. timeline. Use it only as an optional extension for 16x16.

### E. Local search / evolutionary methods

Local search can find sparse candidate clue sets, but it cannot certify uniqueness by itself. It must be paired with a SAT check, and the search space of clue patterns is enormous. Without CP-SAT or a strong UA-based pruning method, this is unlikely to beat the simpler methods above within the project’s constraints.

## Recommended Plan

### Phase 1: Guaranteed 25% generator (highest priority)

- Implement the Mahdian/Qiuyanzhe construction for `N = 16, 25, 36, 49, 64`.
- Add Sudoku symmetry randomization and a seed parameter.
- Verify uniqueness on 4x4, 9x9, and 16x16 with CaDiCaL; for 25x25 and 36x36, verify a sample and rely on the construction theorem for the rest.
- Acceptance: every generated 16x16/25x25/36x36 puzzle has exactly `floor(N^2/4)` clues and a unique solution on the verified sample; 36x36 is below 50% by construction.

### Phase 2: Varied 35-45% generator for 16x16 and 25x25

- Implement the Stojadinović-style removal and restoration loop [5].
- Use a compact CNF encoding (one-hot cell variables plus cardinality constraints) and CaDiCaL.
- Run 100 seeded trials per size; record clue count, fill, generation time, and number of SAT calls.
- Target: 16x16 at or below 45%, 25x25 at or below 45%; fall back to the Phase 1 construction if a trial exceeds its budget.
- Acceptance: all puzzles unique; reproducible from seed; no CP-SAT dependency; results comparable to the published 35-43% range.

### Phase 3: 36x36 strategy

- Default: use the 25% construction, randomized by symmetries. This gives a genuine <50% unique puzzle with predictable cost.
- Optional: start from a known 36x36 unique base (e.g. the Lagerkvist corpus) and run a time-boxed greedy minimization. Report the achieved fill honestly; do not claim that a generic run will go below 50% unless the experiment actually does so.
- If a more “random-looking” 36x36 puzzle is required, add clues to the construction toward 40-50% rather than trying to force a random removal process downward.
- Acceptance: either a construction-based <50% puzzle, or a clearly labelled 50-52% generic result with a statement of the limitation.

### Phase 4: Evaluation and write-up

- Compare clue counts and fill percentages across sizes and methods.
- Measure SAT solving time and uniqueness-check time separately.
- Report the gap between best-known records, construction bounds, and this project’s generator.
- State explicitly that 16x16, 25x25, and 36x36 minimum clue counts are open; only 4x4 and 9x9 are solved.

### Practical implementation notes

- Use the known solution as a blocker: after finding one solution, add a clause that forbids exactly that complete assignment, then ask for another. Do not simply ask the solver for a second model without blocking; it may return the same solution.
- Prefer a compact encoding over naive pairwise all-different clauses. For 36x36, naive pairwise encoding produces millions of clauses and slow builds.
- Cache uniqueness results by clue-set hash during greedy minimization.
- Set per-check timeouts and log them; a timeout is not a proof of uniqueness.
- For 36x36, budget in hours, not minutes, if attempting SAT-based minimization.

## References

[1] M. Mahdian and E. S. Mahmoodian. “Small defining sets in n x n Sudoku squares.” *Proceedings of the 7th International Conference on Computational Methods (ICCM 2016)*, pp. 1292-1298, 2016. URL: https://www.sci-en-tech.com/ICCM2016/PDFs/2006-6313-1-PB.pdf

[2] D. Eppstein and X. Zhang. “Sudoku Grids That Require Many Clues.” arXiv:2607.05728, 7 July 2026. URL: https://arxiv.org/abs/2607.05728

[3] G. McGuire, B. Tugemann, and G. Civario. “There Is No 16-Clue Sudoku: Solving the Sudoku Minimum Number of Clues Problem via Hitting Set Enumeration.” *Experimental Mathematics* 23(2):190-217, 2014. DOI: 10.1080/10586458.2013.870056. arXiv:1201.0749.

[4] M. Z. Lagerkvist. “Scaling Sudoku as a Constraint Problem.” *25th International Workshop on Constraint Modelling and Reformulation (ModRef 2026)*, CP 2026, Lisbon, 2026. URL: https://zayenz.se/research/paper/scaling-sudoku/ ; PDF: https://2026.modref.org/ModRef2026-07-Scaling-Sudoku-as-a-Constraint-Problem.pdf

[5] M. Stojadinović. “Solving and generating large Sudoku puzzles by reduction to SAT.” *InfoM* 54/2015, pp. 25-30, 2015. UDC 519.1:004.4. URL: https://www.infom.fon.bg.ac.rs/index.php/infom/article/download/1867/1839

[6] Qiuyanzhe et al. “Minimum givens on larger puzzles,” EnjoySudoku forum thread t4801, posts from 31 August 2018. The construction gives `floor(n^2/4)` givens, including 156 for 25x25. URL: http://forum.enjoysudoku.com/minimum-givens-on-larger-puzzles-t4801.html and page 2: http://forum.enjoysudoku.com/minimum-givens-on-larger-puzzles-t4801-15.html

[7] “Minimum givens on larger puzzles,” EnjoySudoku forum thread t4801, especially the 2011 56-clue 16x16 post by T_Shirakawa, the 2015 55-clue 16x16 post by ton and extraction by m_b_metcalf, and the 2019 146-clue 25x25 post by ton. URL: http://forum.enjoysudoku.com/minimum-givens-on-larger-puzzles-t4801.html and http://forum.enjoysudoku.com/minimum-givens-on-larger-puzzles-t4801-15.html

[8] “Snipes,” Sudoku Theory wiki. Lists 16x16 best known as 55 givens and notes that minimality is unknown; lists 4x4 minimum 4 and 9x9 minimum 17. URL: http://sudokutheory.com/wiki/index.php?title=Snipes

[9] T. Yato and T. Seta. “Complexity of finding a solution to a Sudoku puzzle.” *IPSJ SIG Notes* 2003(93):1-8, 2003. The NP-completeness and ASP-completeness result for generalized Sudoku.

[10] E. D. Demaine, F. Ma, A. Schvartzman, E. Waingarten, and S. Aaronson. “The Fewest Clues Problem.” *Theoretical Computer Science* 748:28-39, 2018. DOI: 10.1016/j.tcs.2018.01.020

[11] “Mathematics of Sudoku,” Wikipedia. Sections on minimum number of givens, unavoidable sets, and the exact-cover formulation. URL: https://en.wikipedia.org/wiki/Mathematics_of_Sudoku

[12] M. Z. Lagerkvist. “Scaled Sudoku Instances” corpus, GitHub repository. 32,000 base puzzles and 402,201 walk variants, including 16x16, 25x25, and 36x36. URL: https://github.com/zayenz/scaled-sudoku-instances

## Notes on Verification Status

- The 25% construction is supported by a peer-reviewed ICCM paper [1] and an independent forum construction [6].
- The 16x16 55-clue puzzle and 25x25 146-clue puzzle are community records [7], not peer-reviewed proofs of optimality. The 55-clue puzzle has been extracted and analyzed on the forum; the 146-clue puzzle is described as the current world least in a separate SAT article.
- Eppstein and Zhang’s “56 clues” statement [2] conflicts with the 55-clue community record. This report treats 55 as best known and 56 as the well-documented published construction/conjecture; the discrepancy should be noted in any thesis discussion.
- The 36x36 25% figure is a construction bound, not a record found by a generator. The 52.2% figure is the median of a specific generated corpus [4], not a lower bound.
- The pilot timing in this report is a single local experiment, not a peer-reviewed benchmark.
