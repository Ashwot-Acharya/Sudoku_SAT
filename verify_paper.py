#!/usr/bin/env python3
"""
Verification script to check if paper claims match the actual data.
This is your audit. Every check is independent.
"""

import pandas as pd
import numpy as np
from scipy import stats as sp_stats
from collections import defaultdict

# Load data
df = pd.read_csv('Results/benchmark_results.csv')

print("=" * 80)
print("VERIFICATION SCRIPT: Checking paper claims against raw data")
print("=" * 80)

# ============================================================================
# CHECK 1: Descriptive Statistics (Table 1 in paper)
# ============================================================================
print("\n\n[CHECK 1] Table 1: Solve-Only Times")
print("-" * 80)

table1_claims = {
    4: {"SAT_Compact": 0.001, "SAT_Naive": 0.001, "BT": 0.05e-3},
    9: {"SAT_Compact": 0.002, "SAT_Naive": 0.003, "BT": 0.003},
    16: {"SAT_Compact": 0.002, "SAT_Naive": 0.013, "BT": 0.95e-3},
    25: {"SAT_Compact": 0.002, "SAT_Naive": 0.078, "BT": 0.010},
    36: {"SAT_Compact": 0.002, "SAT_Naive": 0.347, "BT": 0.012},
}

for size in sorted(df['size'].unique()):
    subset = df[df['size'] == size]

    sc_mean = subset['sat_compact_time'].mean()
    sn_mean = subset['sat_naive_time'].mean()
    bt_mean = subset['bt_time'].mean()

    print(f"\nSize {size}x{size}:")
    print(f"  SAT Compact:  {sc_mean:.6f}s (paper claims ~{table1_claims[size]['SAT_Compact']:.6f}s)")
    print(f"  SAT Naive:    {sn_mean:.6f}s (paper claims ~{table1_claims[size]['SAT_Naive']:.6f}s)")
    print(f"  Backtracking: {bt_mean:.6f}s (paper claims ~{table1_claims[size]['BT']:.6f}s)")

    # Check if they're reasonably close (within 50% is OK for empirical work)
    if abs(sc_mean - table1_claims[size]['SAT_Compact']) < table1_claims[size]['SAT_Compact'] * 0.5:
        print(f"  ✓ SAT Compact matches")
    else:
        print(f"  ✗ SAT Compact MISMATCH (off by {abs(sc_mean - table1_claims[size]['SAT_Compact']) / table1_claims[size]['SAT_Compact'] * 100:.1f}%)")


# ============================================================================
# CHECK 2: Speedups (derived from times)
# ============================================================================
print("\n\n[CHECK 2] Speedup Ratios (Figure and text)")
print("-" * 80)

speedup_claims = {
    4: {"BT/SAT-C": 0.04, "N/C": 0.94},
    9: {"BT/SAT-C": 1.71, "N/C": 1.33},
    16: {"BT/SAT-C": 0.59, "N/C": 8.38},
    25: {"BT/SAT-C": 4.04, "N/C": 31.95},
    36: {"BT/SAT-C": 4.81, "N/C": 144.33},
}

for size in sorted(df['size'].unique()):
    subset = df[df['size'] == size]

    sc_mean = subset['sat_compact_time'].mean()
    sn_mean = subset['sat_naive_time'].mean()
    bt_mean = subset['bt_time'].mean()

    speedup_bt_sc = bt_mean / sc_mean if sc_mean > 0 else np.inf
    speedup_n_c = sn_mean / sc_mean if sc_mean > 0 else np.inf

    print(f"\nSize {size}x{size}:")
    print(f"  BT/SAT-C speedup: {speedup_bt_sc:.2f}x (paper claims {speedup_claims[size]['BT/SAT-C']:.2f}x)")
    print(f"  N/C speedup:      {speedup_n_c:.2f}x (paper claims {speedup_claims[size]['N/C']:.2f}x)")


# ============================================================================
# CHECK 3: Wilcoxon Signed-Rank Test (Table 2 in paper)
# ============================================================================
print("\n\n[CHECK 3] Wilcoxon Signed-Rank Test: BT vs SAT Compact")
print("-" * 80)

wilcoxon_claims = {
    4: {"p_value": "<0.001", "significant": True},
    9: {"p_value": "0.421", "significant": False},
    16: {"p_value": "<0.001", "significant": True},
    25: {"p_value": "<0.001", "significant": True},
    36: {"p_value": "<0.001", "significant": True},
}

for size in sorted(df['size'].unique()):
    subset = df[df['size'] == size]

    # Pair by puzzle and repetition
    bt_times = subset['bt_time'].values
    sc_times = subset['sat_compact_time'].values

    if len(bt_times) >= 5:
        # Remove any timeouts (600s values)
        mask = (bt_times < 600) & (sc_times < 600)
        bt_finite = bt_times[mask]
        sc_finite = sc_times[mask]

        if len(bt_finite) >= 5:
            stat, pval = sp_stats.wilcoxon(bt_finite, sc_finite, alternative="two-sided")
            significant = pval < 0.05

            print(f"\nSize {size}x{size}:")
            print(f"  Wilcoxon statistic: {stat:.2f}")
            print(f"  p-value: {pval:.6f} (paper claims {wilcoxon_claims[size]['p_value']})")
            print(f"  Significant (p<0.05): {significant} (paper claims {wilcoxon_claims[size]['significant']})")

            if significant == wilcoxon_claims[size]['significant']:
                print(f"  ✓ Result matches paper claim")
            else:
                print(f"  ✗ Result DOES NOT match paper claim")


# ============================================================================
# CHECK 4: Friedman Test (Table 3 in paper)
# ============================================================================
print("\n\n[CHECK 4] Friedman Test: All 3 solvers")
print("-" * 80)

friedman_claims = {
    4: {"chi2": 7.60, "p_value": "0.022", "kendall_w": 0.760, "significant": True},
    9: {"chi2": 2.80, "p_value": "0.247", "kendall_w": 0.280, "significant": False},
    16: {"chi2": 10.00, "p_value": "0.007", "kendall_w": 1.000, "significant": True},
    25: {"chi2": 10.00, "p_value": "0.007", "kendall_w": 1.000, "significant": True},
    36: {"chi2": 10.00, "p_value": "0.007", "kendall_w": 1.000, "significant": True},
}

for size in sorted(df['size'].unique()):
    subset = df[df['size'] == size]

    # Group by puzzle
    puzzles = subset['puzzle_name'].unique()

    # For each puzzle, get mean of each solver
    bt_means = []
    sc_means = []
    sn_means = []

    for puzzle in puzzles:
        puzzle_subset = subset[subset['puzzle_name'] == puzzle]
        bt_means.append(puzzle_subset['bt_time'].mean())
        sc_means.append(puzzle_subset['sat_compact_time'].mean())
        sn_means.append(puzzle_subset['sat_naive_time'].mean())

    if len(bt_means) >= 3:
        # Friedman test
        data = np.array([bt_means, sc_means, sn_means]).T
        chi2, pval = sp_stats.friedmanchisquare(*data.T)

        # Kendall's W
        n_blocks = len(bt_means)
        k = 3  # number of solvers
        W = chi2 / (n_blocks * (k - 1))

        significant = pval < 0.05

        print(f"\nSize {size}x{size}:")
        print(f"  Chi-squared: {chi2:.2f} (paper claims {friedman_claims[size]['chi2']:.2f})")
        print(f"  p-value: {pval:.6f} (paper claims {friedman_claims[size]['p_value']})")
        print(f"  Kendall's W: {W:.3f} (paper claims {friedman_claims[size]['kendall_w']:.3f})")
        print(f"  Significant (p<0.05): {significant} (paper claims {friedman_claims[size]['significant']})")

        if significant == friedman_claims[size]['significant']:
            print(f"  ✓ Result matches paper claim")
        else:
            print(f"  ✗ Result DOES NOT match paper claim")


# ============================================================================
# CHECK 5: Encoding Size Reduction (Table 3)
# ============================================================================
print("\n\n[CHECK 5] CNF Encoding Size Comparison (Table 3)")
print("-" * 80)

encoding_claims = {
    4: {"var_red": 66.2, "clause_red": 78.8},
    9: {"var_red": 56.3, "clause_red": 74.1},
    16: {"var_red": 95.2, "clause_red": 99.1},
    25: {"var_red": 95.0, "clause_red": 99.2},
    36: {"var_red": 98.7, "clause_red": 99.9},
}

for size in sorted(df['size'].unique()):
    subset = df[df['size'] == size]

    # Use first row as representative (encoding should be same for all puzzles of same size)
    first_row = subset.iloc[0]

    naive_vars = first_row['naive_vars']
    naive_clauses = first_row['naive_clauses']
    compact_vars = first_row['compact_vars']
    compact_clauses = first_row['compact_clauses']

    var_red_pct = (1 - compact_vars / naive_vars) * 100
    clause_red_pct = (1 - compact_clauses / naive_clauses) * 100

    print(f"\nSize {size}x{size}:")
    print(f"  Naive: {naive_vars} vars, {naive_clauses} clauses")
    print(f"  Compact: {compact_vars} vars, {compact_clauses} clauses")
    print(f"  Variable reduction: {var_red_pct:.1f}% (paper claims {encoding_claims[size]['var_red']:.1f}%)")
    print(f"  Clause reduction: {clause_red_pct:.1f}% (paper claims {encoding_claims[size]['clause_red']:.1f}%)")


# ============================================================================
# CHECK 6: All Solutions Valid (paper claims 100%)
# ============================================================================
print("\n\n[CHECK 6] Solution Validation (paper claims 100% pass rate)")
print("-" * 80)

valid_count = df['validator_passed'].sum()
total_count = len(df)
pass_rate = (valid_count / total_count) * 100

print(f"Valid solutions: {valid_count} / {total_count} ({pass_rate:.1f}%)")
if pass_rate == 100.0:
    print(f"✓ Paper claim is correct")
else:
    print(f"✗ Paper claim is INCORRECT (should be 100%)")


print("\n\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
