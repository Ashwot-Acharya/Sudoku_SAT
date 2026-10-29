# Statistical Analysis — Sudoku SAT vs. Backtracking

**Data source:** `Results/benchmark_results_combined.csv` (derived from the two per-generator CSVs).  
**Design:** 2 generators × 5 sizes × 30 puzzles per cell × 1 repeat = **300 benchmark runs**; solver timeout = 120 s.  
**Analysis date:** 2026-10-28

## Executive summary

- **Correctness:** all 300 runs produced solutions that passed the validator. Legacy puzzles were uniqueness-verified 150/150; back-circulant puzzles were construction-valid 150/150 but their uniqueness was not re-checked in the benchmark run.
- **Timeouts:** SAT compact 0/300, SAT naive 0/300, SAT log 28/300, backtracking 81/300. Backtracking timeouts are concentrated in legacy 16×16 (21/30), 25×25 (30/30), and 36×36 (30/30).
- **Back-circulant:** backtracking is fastest at every size (median 78.5 µs at 4×4 to 94.1 ms at 36×36) and is roughly 18–31× faster end-to-end than compact SAT because SAT also pays CNF encoding cost.
- **Legacy:** compact SAT solves every puzzle and is the only method without large-grid timeouts. Its median solve time is 4.75 ms at 16×16, 10.4 ms at 25×25, and 24.6 ms at 36×36, versus 21/30, 0/30, and 0/30 solved for backtracking.
- **SAT encoding ranking:** compact SAT beats naive and log at 9×9 and above; log is the slowest SAT encoding and times out on 27/30 legacy 36×36 puzzles. The advantage is not present at 4×4, where all SAT encodings are within milliseconds and differences are practically irrelevant.
- **Generator comparison is confounded:** legacy puzzles become progressively denser (mean fill 25.8% → 49.8% from 4×4 to 36×36), while back-circulant puzzles remain near 25%. Large-grid legacy-vs-back-circulant timing differences therefore mix generator structure with clue density; they are not a clean causal estimate of generator quality.
- **End-to-end matters:** at 36×36 back-circulant, compact CNF encoding alone takes 1.58 s while solving takes 0.126 s. Encoding consumes about 93% of compact SAT end-to-end time there, so solve-only rankings overstate SAT's practical advantage.

## 1. Methodology

- **Unit of analysis:** one generated puzzle solved once by each of four methods: SAT with compact encoding, SAT with naive encoding, SAT with logarithmic encoding, and MRV/degree/forward-checking backtracking.
- **Dependence:** the four methods are paired within puzzle. Within-generator comparisons use the two-sided **Wilcoxon signed-rank test** on paired finite observations.
- **Generator comparisons:** legacy and back-circulant puzzles are independent samples, so two-sided **Mann–Whitney U** tests are used. Because timeouts are right-censored at 120 s, the primary generator comparison uses `min(time, 120)`; this avoids conditioning on successful runs only.
- **Effect size:** the rank-biserial correlation is reported for Mann–Whitney comparisons. Positive values mean legacy times are stochastically larger (legacy slower); negative values mean back-circulant times are larger.
- **Multiplicity:** Holm–Bonferroni adjusted p-values are reported within explicit test families. Unadjusted p-values are shown in parentheses where useful.
- **Descriptive timing:** medians and interquartile ranges use **finite solved runs only**. Rows with timeouts are flagged with their finite sample size; all-timeout cells say so explicitly. This makes the point estimate conditional on success and should be read alongside the timeout table.
- **No normality assumption** is used for inference. Log–log scaling exponents are descriptive fits over the sampled sizes, not asymptotic complexity proofs.

## 2. Data integrity and generation profile

| Check | Result |
|---|---|
| Benchmark rows | 300 |
| Solutions validated | 300/300 (100%) |
| Legacy uniqueness verified | 150/150 |
| Back-circulant construction valid | 150/150 |
| Back-circulant uniqueness re-checked in this run | No (blank in benchmark CSV) |
| SAT compact solved | 300/300 |
| SAT naive solved | 300/300 |
| SAT log solved | 272/300 |
| Backtracking solved | 219/300 |

| Generator | Size | Clues, mean (range) | Fill, mean | Generation median (max) | Retries |
|---|---:|---:|---:|---:|---:|
| Legacy | 4×4 | 4.13 (4–5) | 25.83% | 16.15 ms (26.70 ms) | 0 |
| Legacy | 9×9 | 25.23 (25–26) | 31.15% | 302.30 ms (493.80 ms) | 0 |
| Legacy | 16×16 | 93.27 (87–98) | 36.43% | 1.354 s (1.567 s) | 0 |
| Legacy | 25×25 | 262.70 (254–275) | 42.03% | 18.6 s (22.5 s) | 0 |
| Legacy | 36×36 | 644.83 (627–648) | 49.76% | 60.2 s (122.2 s) | 4 |
| Back-circulant | 4×4 | 4.00 (4–4) | 25.00% | 22 µs (38 µs) | 0 |
| Back-circulant | 9×9 | 20.00 (20–20) | 24.69% | 36 µs (43 µs) | 0 |
| Back-circulant | 16×16 | 64.00 (64–64) | 25.00% | 62 µs (228 µs) | 0 |
| Back-circulant | 25×25 | 156.00 (156–156) | 24.96% | 104 µs (326 µs) | 0 |
| Back-circulant | 36×36 | 324.00 (324–324) | 25.00% | 188 µs (476 µs) | 0 |

The clue/fill gap is the main confounder for cross-generator claims. Legacy 25×25 puzzles average 262.7 clues (42.0% fill) and legacy 36×36 puzzles average 644.8 clues (49.8% fill), versus 156 (25.0%) and 324 (25.0%) for back-circulant. The legacy 36×36 hard cap was respected: the maximum observed was 648/1296 = 50.0%.

## 3. Solver success and timeout profile

| Generator | Size | SAT-C | SAT-N | SAT-L | BT |
|---|---:|---:|---:|---:|---:|
| Legacy | 4×4 | 30/30 | 30/30 | 30/30 | 30/30 |
| Legacy | 9×9 | 30/30 | 30/30 | 30/30 | 30/30 |
| Legacy | 16×16 | 30/30 | 30/30 | 30/30 | 9/30 |
| Legacy | 25×25 | 30/30 | 30/30 | 29/30 | 0/30 |
| Legacy | 36×36 | 30/30 | 30/30 | 3/30 | 0/30 |
| Back-circulant | 4×4 | 30/30 | 30/30 | 30/30 | 30/30 |
| Back-circulant | 9×9 | 30/30 | 30/30 | 30/30 | 30/30 |
| Back-circulant | 16×16 | 30/30 | 30/30 | 30/30 | 30/30 |
| Back-circulant | 25×25 | 30/30 | 30/30 | 30/30 | 30/30 |
| Back-circulant | 36×36 | 30/30 | 30/30 | 30/30 | 30/30 |

**Timeout interpretation.** Legacy 16×16 backtracking has 21 timeouts; the nine successful runs give a finite median of 24.1 s, but a censored median of 120 s. Legacy 25×25 and 36×36 backtracking timed out on every puzzle. Legacy 36×36 log timed out on 27/30 puzzles; its finite median (93.1 s, n=3) is therefore a best-case estimate for the rare successful runs, not a representative 36×36 time.

## 4. Solve-only performance

Cells are **median (IQR)** over finite solved runs; `[n=…]` marks cells with timeouts. See the success table for the denominator.

| Generator | Size | SAT Compact | SAT Naive | SAT Log | Backtracking |
|---|---:|---:|---:|---:|---:|
| Legacy | 4×4 | 2.29 ms (2.22 ms–2.54 ms) | 2.36 ms (2.24 ms–2.58 ms) | 2.20 ms (2.08 ms–2.45 ms) | 60 µs (50 µs–79 µs) |
| Legacy | 9×9 | 2.91 ms (2.71 ms–3.09 ms) | 5.04 ms (4.74 ms–5.38 ms) | 8.49 ms (8.23 ms–9.41 ms) | 1.00 ms (702 µs–2.23 ms) |
| Legacy | 16×16 | 4.75 ms (4.25 ms–5.09 ms) | 27.73 ms (27.12 ms–28.48 ms) | 336.50 ms (271.40 ms–393.65 ms) | 24.1 s (15.1 s–99.3 s) [n=9] |
| Legacy | 25×25 | 10.43 ms (9.83 ms–11.83 ms) | 154.00 ms (149.10 ms–158.45 ms) | 8.623 s (7.053 s–14.5 s) [n=29] | all timeout |
| Legacy | 36×36 | 24.58 ms (19.18 ms–47.90 ms) | 711.44 ms (676.43 ms–825.38 ms) | 93.1 s (91.1 s–102.9 s) [n=3] | all timeout |
| Back-circulant | 4×4 | 2.10 ms (2.00 ms–2.26 ms) | 1.91 ms (1.67 ms–2.23 ms) | 1.95 ms (1.72 ms–2.12 ms) | 78 µs (44 µs–81 µs) |
| Back-circulant | 9×9 | 3.16 ms (2.99 ms–3.28 ms) | 4.59 ms (4.39 ms–4.84 ms) | 7.85 ms (7.15 ms–8.33 ms) | 466 µs (460 µs–471 µs) |
| Back-circulant | 16×16 | 7.41 ms (7.26 ms–7.62 ms) | 26.44 ms (26.10 ms–26.82 ms) | 142.46 ms (84.56 ms–193.77 ms) | 3.68 ms (3.64 ms–3.85 ms) |
| Back-circulant | 25×25 | 31.55 ms (31.22 ms–31.97 ms) | 147.68 ms (146.95 ms–148.60 ms) | 2.503 s (2.151 s–2.888 s) | 21.24 ms (21.05 ms–21.50 ms) |
| Back-circulant | 36×36 | 125.76 ms (124.28 ms–126.50 ms) | 639.56 ms (635.06 ms–646.59 ms) | 55.2 s (30.8 s–68.5 s) | 94.11 ms (93.41 ms–94.75 ms) |

The main pattern is a method-by-generator interaction. On back-circulant puzzles, backtracking is the fastest method at every size and remains stable through 36×36. On legacy puzzles, backtracking is excellent at 4×4 and 9×9 but collapses at 16×16 and above, while compact SAT remains sub-30 ms at 36×36. Backtracking's legacy 16×16 finite median is heavily selection-biased because only 9/30 runs finished.

## 5. CNF encoding cost and end-to-end performance

### 5.1 Mean CNF size

| Generator | Size | Naive vars | Naive clauses | Compact vars | Compact clauses | Log vars | Log clauses |
|---|---:|---:|---:|---:|---:|---:|---:|
| Legacy | 4×4 | 64 | 452 | 26 | 124 | 32 | 232 |
| Legacy | 9×9 | 729 | 12,013 | 212 | 1,646 | 324 | 7,958 |
| Legacy | 16×16 | 4,096 | 123,997 | 841 | 8,933 | 1,024 | 80,245 |
| Legacy | 25×25 | 15,625 | 752,763 | 2,236 | 28,854 | 3,125 | 505,688 |
| Legacy | 36×36 | 46,656 | 3,271,749 | 4,054 | 53,810 | 7,776 | 2,256,317 |
| Back-circulant | 4×4 | 64 | 452 | 27 | 133 | 32 | 232 |
| Back-circulant | 9×9 | 729 | 12,008 | 303 | 3,112 | 324 | 7,937 |
| Back-circulant | 16×16 | 4,096 | 123,968 | 1,706 | 32,356 | 1,024 | 80,128 |
| Back-circulant | 25×25 | 15,625 | 752,656 | 6,567 | 200,444 | 3,125 | 505,155 |
| Back-circulant | 36×36 | 46,656 | 3,271,428 | 19,686 | 880,716 | 7,776 | 2,254,392 |

Compact/naive clause ratios are about 0.29, 0.26, 0.26, 0.27, and 0.27 for back-circulant 4×4 through 36×36 (roughly a 3.4–3.9× clause reduction). Legacy ratios fall much more sharply with size (0.27, 0.14, 0.072, 0.038, 0.016) because legacy puzzles contain far more givens at large sizes, and clues add proportionally more clauses to the compact encoding than to the mostly size-driven naive encoding. This is a clue-density effect, not a property that generalizes across puzzle generators.

### 5.2 Encoding overhead and median end-to-end time

| Generator | Size | Enc C | Enc N | Enc L | SAT-C E2E | SAT-N E2E | SAT-L E2E | BT solve |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Legacy | 4×4 | 378 µs | 171 µs | 283 µs | 2.69 ms | 2.58 ms | 2.52 ms | 60 µs |
| Legacy | 9×9 | 6.39 ms | 4.53 ms | 9.14 ms | 9.42 ms | 9.56 ms | 18.10 ms | 1.00 ms |
| Legacy | 16×16 | 52.79 ms | 199.67 ms | 94.48 ms | 57.80 ms | 227.30 ms | 448.84 ms | 24.1 s |
| Legacy | 25×25 | 290.71 ms | 585.74 ms | 958.31 ms | 302.59 ms | 749.31 ms | 9.625 s | all timeout |
| Legacy | 36×36 | 1.141 s | 2.388 s | 3.923 s | 1.191 s | 3.181 s | 97.3 s | all timeout |
| Back-circulant | 4×4 | 335 µs | 168 µs | 254 µs | 2.45 ms | 2.09 ms | 2.20 ms | 78 µs |
| Back-circulant | 9×9 | 6.47 ms | 4.37 ms | 8.07 ms | 9.61 ms | 9.05 ms | 15.89 ms | 466 µs |
| Back-circulant | 16×16 | 61.62 ms | 37.41 ms | 146.33 ms | 69.10 ms | 63.89 ms | 290.58 ms | 3.68 ms |
| Back-circulant | 25×25 | 372.19 ms | 544.58 ms | 809.90 ms | 403.60 ms | 691.95 ms | 3.284 s | 21.24 ms |
| Back-circulant | 36×36 | 1.577 s | 2.155 s | 3.786 s | 1.704 s | 2.795 s | 59.0 s | 94.11 ms |

Encoding dominates end-to-end cost at large sizes. For back-circulant 36×36, compact encoding is 1.58 s versus 0.126 s of solving; the end-to-end compact time is 1.70 s. For legacy 36×36 compact, encoding is 1.14 s versus 0.0246 s of solving; end-to-end is 1.19 s. At 4×4, encoding is only about 7–15% of compact/naive end-to-end time, so encoding overhead becomes important only as size grows.

End-to-end, back-circulant backtracking wins by a wide margin at every size. The median BT/compact-SAT E2E ratio is approximately 0.032 at 4×4, 0.048 at 9×9, 0.053 at 16×16, 0.053 at 25×25, and 0.055 at 36×36; equivalently, compact SAT is roughly 18–31× slower once encoding is included. For legacy 16×16 and above, backtracking's end-to-end time is either conditional on the minority of successful runs or is a timeout, so the compact-SAT advantage is even larger in practical terms.

## 6. Within-generator statistical comparisons

### 6.1 SAT encoding choice (paired Wilcoxon)

Each cell shows **raw p (Holm-adjusted p)**. Tests use only puzzles where both methods finished. Holm adjustment is within each generator across the available SAT-method contrasts. `—` means fewer than five finite pairs.

| Generator | Size | C vs N | C vs L | N vs L | Fastest median |
|---|---:|---:|---:|---:|---|
| Legacy | 4×4 | 0.428 (0.856) | 0.0937 (0.281) | 0.0293 (0.147) | Log |
| Legacy | 9×9 | <0.001 (<0.001) | <0.001 (<0.001) | <0.001 (<0.001) | Compact |
| Legacy | 16×16 | <0.001 (<0.001) | <0.001 (<0.001) | <0.001 (<0.001) | Compact |
| Legacy | 25×25 | <0.001 (<0.001) | <0.001 (<0.001) | <0.001 (<0.001) | Compact |
| Legacy | 36×36 | <0.001 (<0.001) | — | — | Compact (Log 3/30 solved) |
| Back-circulant | 4×4 | 0.0417 (0.167) | <0.001 (0.00369) | 0.808 (0.856) | Naive |
| Back-circulant | 9×9 | <0.001 (<0.001) | <0.001 (<0.001) | <0.001 (<0.001) | Compact |
| Back-circulant | 16×16 | <0.001 (<0.001) | <0.001 (<0.001) | <0.001 (<0.001) | Compact |
| Back-circulant | 25×25 | <0.001 (<0.001) | <0.001 (<0.001) | <0.001 (<0.001) | Compact |
| Back-circulant | 36×36 | <0.001 (<0.001) | <0.001 (<0.001) | <0.001 (<0.001) | Compact |

Compact encoding is consistently faster than naive and log once the grid reaches 9×9. At 4×4 all three SAT encodings solve in roughly 2 ms; the compact-vs-naive difference is not significant for legacy (p=0.428) and the absolute differences are negligible. At 36×36 legacy, the log encoding cannot support a meaningful paired comparison because only 3/30 runs finish.

### 6.2 Backtracking versus compact SAT (paired Wilcoxon)

`BT/C` is the median of within-puzzle ratios; values below 1 favor backtracking. Holm adjustment is within each generator across the available size tests.

| Generator | Size | Pairs | SAT-C median | BT median | BT/C | Wilcoxon p (Holm) | Note |
|---|---:|---:|---:|---:|---:|---:|---|
| Legacy | 4×4 | 30 | 2.29 ms | 60 µs | 0.0247× | <0.001 (<0.001) | BT faster |
| Legacy | 9×9 | 30 | 2.91 ms | 1.00 ms | 0.371× | 0.00158 (0.00317) | BT faster |
| Legacy | 16×16 | 9 | 4.75 ms | 24.1 s | 5.48e+03× | 0.00391 (0.00391) | Only 9/30 BT solved; conditional |
| Legacy | 25×25 | 0 | 10.43 ms | all timeout | — | — | No finite pairs (BT all timeout) |
| Legacy | 36×36 | 0 | 24.58 ms | all timeout | — | — | No finite pairs (BT all timeout) |
| Back-circulant | 4×4 | 30 | 2.10 ms | 78 µs | 0.0325× | <0.001 (<0.001) | BT faster |
| Back-circulant | 9×9 | 30 | 3.16 ms | 466 µs | 0.146× | <0.001 (<0.001) | BT faster |
| Back-circulant | 16×16 | 30 | 7.41 ms | 3.68 ms | 0.499× | <0.001 (<0.001) | BT faster |
| Back-circulant | 25×25 | 30 | 31.55 ms | 21.24 ms | 0.677× | <0.001 (<0.001) | BT faster |
| Back-circulant | 36×36 | 30 | 125.76 ms | 94.11 ms | 0.749× | <0.001 (<0.001) | BT faster |

For back-circulant, backtracking is significantly faster than compact SAT at all five sizes after Holm adjustment. The advantage shrinks with size but remains material: median BT/C is 0.032 at 4×4, 0.146 at 9×9, 0.499 at 16×16, 0.677 at 25×25, and 0.749 at 36×36. For legacy, backtracking is faster at 4×4 and 9×9, but at 16×16 only 9/30 runs finish and the paired estimate is conditional; at 25×25 and 36×36 there are no finite pairs. Compact SAT is therefore the robust choice for legacy large grids.

## 7. Cross-generator comparisons

Both generators have 30 puzzles per size. Times below are medians of `min(time, 120)`; positive rank-biserial `r` means legacy is slower, negative means legacy is faster. Holm adjustment is across all 20 cross-generator tests.

| Size | Method | Legacy median | Back-circulant median | MW p | Holm p | Rank-biserial | Direction |
|---:|---|---:|---:|---:|---:|---:|---|
| 4×4 | SAT-C | 2.29 ms | 2.10 ms | <0.001 | 0.00159 | +0.54 | Legacy slower |
| 4×4 | SAT-N | 2.36 ms | 1.91 ms | <0.001 | <0.001 | +0.64 | Legacy slower |
| 4×4 | SAT-L | 2.20 ms | 1.95 ms | <0.001 | <0.001 | +0.60 | Legacy slower |
| 4×4 | BT | 60 µs | 78 µs | 0.491 | 0.491 | +0.10 | Not significant |
| 9×9 | SAT-C | 2.91 ms | 3.16 ms | 0.0035 | 0.007 | -0.44 | Legacy faster |
| 9×9 | SAT-N | 5.04 ms | 4.59 ms | <0.001 | 0.00159 | +0.54 | Legacy slower |
| 9×9 | SAT-L | 8.49 ms | 7.85 ms | 0.0012 | 0.00361 | +0.49 | Legacy slower |
| 9×9 | BT | 1.00 ms | 466 µs | <0.001 | <0.001 | +0.74 | Legacy slower |
| 16×16 | SAT-C | 4.75 ms | 7.41 ms | <0.001 | <0.001 | -0.93 | Legacy faster |
| 16×16 | SAT-N | 27.73 ms | 26.44 ms | <0.001 | <0.001 | +0.71 | Legacy slower |
| 16×16 | SAT-L | 336.50 ms | 142.46 ms | <0.001 | <0.001 | +0.75 | Legacy slower |
| 16×16 | BT | 120.0 s | 3.68 ms | <0.001 | <0.001 | +1.00 | Legacy slower |
| 25×25 | SAT-C | 10.43 ms | 31.55 ms | <0.001 | <0.001 | -1.00 | Legacy faster |
| 25×25 | SAT-N | 154.00 ms | 147.68 ms | <0.001 | <0.001 | +0.62 | Legacy slower |
| 25×25 | SAT-L | 8.762 s | 2.503 s | <0.001 | <0.001 | +1.00 | Legacy slower |
| 25×25 | BT | 120.0 s | 21.24 ms | <0.001 | <0.001 | +1.00 | Legacy slower |
| 36×36 | SAT-C | 24.58 ms | 125.76 ms | <0.001 | <0.001 | -0.80 | Legacy faster |
| 36×36 | SAT-N | 711.44 ms | 639.56 ms | <0.001 | <0.001 | +0.95 | Legacy slower |
| 36×36 | SAT-L | 120.0 s | 55.2 s | <0.001 | <0.001 | +1.00 | Legacy slower |
| 36×36 | BT | 120.0 s | 94.11 ms | <0.001 | <0.001 | +1.00 | Legacy slower |

These tests describe the generated puzzle sets, not a clean generator effect. Back-circulant backtracking is dramatically faster at 16×16 and above; the legacy backtracking medians there are censored at 120 s, so the effect size reaches its maximum. Compact SAT is faster on legacy at 16×16 and above, but those legacy puzzles have 36–50% fill versus 25% for back-circulant. More clues generally make SAT easier, so the compact-SAT difference cannot be attributed to generator structure alone. At 9×9, where fill is closer (31.2% vs 24.7%), back-circulant is faster for naive, log, and backtracking, while legacy is slightly faster for compact SAT.

## 8. Scaling behavior

Log–log fits use the median finite solve time at each size. Exponents are descriptive slopes over 4×4–36×36 and should not be read as asymptotic complexity.

| Generator | SAT Compact | SAT Naive | SAT Log | Backtracking |
|---|---:|---:|---:|---:|
| Legacy | N^1.05 (R²=0.87) | N^2.63 (R²=0.93) | N^4.51 (R²=0.91) (N≤25) | not estimated (timeouts) |
| Back-circulant | N^1.82 (R²=0.87) | N^2.68 (R²=0.94) | N^4.64 (R²=0.92) | N^3.26 (R²=0.98) |

Within back-circulant, compact SAT grows much more slowly than the other methods (fitted exponent 1.82 vs 2.68 for naive, 4.64 for log, and 3.26 for backtracking). Legacy compact SAT has a deceptively low fitted exponent (1.05) because the puzzle set becomes much denser as size increases; that is a difficulty trend, not evidence that compact SAT is asymptotically cheaper than the back-circulant fit suggests. Legacy backtracking and log fits are not reliable at large sizes because of timeouts.

End-to-end scaling is dominated by encoding: fitted exponents are approximately N^2.81 (legacy compact E2E), N^3.38 (legacy naive E2E), N^4.91 (legacy log E2E), N^3.03 (back-circulant compact E2E), N^3.36 (back-circulant naive E2E), and N^4.59 (back-circulant log E2E).

## 9. Interpretation and threats to validity

1. **Puzzle difficulty is not randomized across generators.** Legacy fill rises with size, while back-circulant fill is fixed near 25%. Cross-generator differences therefore combine generator structure, clue count, and clue placement. The correct claim is about these generated datasets, not a universal generator ranking.
2. **Timeouts are informative, not missing at random.** Conditioning on finite solves makes legacy backtracking look better than it is. The success table and censored comparisons are the primary evidence for large legacy grids.
3. **One repeat per puzzle.** SAT timing variance is small in these runs, but there is no estimate of within-puzzle run-to-run variance. The 30 puzzles per cell provide between-puzzle replication.
4. **Multiple comparisons.** Holm adjustment controls the stated families, but the report is still exploratory. Very small p-values reflect consistent rankings; they do not by themselves establish practical importance.
5. **Back-circulant uniqueness.** Construction validity is not the same as an independent uniqueness proof. The benchmark CSV leaves `verified_unique` blank for back-circulant; a separate uniqueness pass would be needed before claiming the same uniqueness guarantee as the legacy set.
6. **Implementation and hardware.** Results are specific to CaDiCaL, this CNF encoding implementation, this MRV/degree/forward-checking backtracker, and the host machine. Absolute times should not be compared across papers without the same setup.
7. **Scaling fits.** Five grid sizes and censored observations are enough for description, not for confident extrapolation to much larger Sudoku boards.

## 10. Practical conclusions

- For **structured back-circulant puzzles**, use backtracking if raw solve time or total time matters: it is fastest at every tested size and avoids CNF encoding entirely.
- For **legacy puzzles at 4×4 and 9×9**, backtracking is fastest. At 16×16 and above, use compact SAT; backtracking times out on most or all large legacy instances.
- Among SAT encodings, **compact** is the default choice from 9×9 upward. Naive is competitive only at tiny sizes, and log is not competitive at 16×16 and above.
- Report **end-to-end** time when comparing SAT to backtracking. Solve-only SAT comparisons omit an encoding cost that reaches about 93–96% of compact end-to-end time at 36×36.
- Treat generator comparisons as **descriptive of these datasets**. To isolate generator structure, generate puzzles with matched clue counts/fill, or use a clue-count-stratified design.

## 11. Reproduction

Raw data: `Results/benchmark_results_combined.csv`; per-generator inputs: `Results/benchmark_results_legacy.csv` and `Results/benchmark_results_back_circulant.csv`. The benchmark command used the pipeline defaults:

```bash
python experiment/Main/run_pipeline.py --sizes 4 9 16 25 36 --puzzles-per-size 30 --repeats 1 --generator both --timeout 120
```

The descriptive tables and tests above were computed directly from the combined CSV with SciPy (`scipy.stats.wilcoxon`, `scipy.stats.mannwhitneyu`, `scipy.stats.linregress`).
