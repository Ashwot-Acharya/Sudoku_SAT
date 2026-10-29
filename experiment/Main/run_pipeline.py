"""
run_pipeline.py  —  Master entry point (unified 3-encoding pipeline)

Usage:
    python run_pipeline.py                                  # full run, auto-detect solver
    python run_pipeline.py --solver /usr/sbin/cadical
    python run_pipeline.py --sizes 4 9 16 --repeats 3
    python run_pipeline.py --generator legacy               # single generator
    python run_pipeline.py --generator both                 # legacy + back-circulant
    python run_pipeline.py --no-save-solutions              # skip solution artifacts
    python run_pipeline.py --no-save-assignments            # grids only, no raw SAT models
    python run_pipeline.py --no-plot                        # skip matplotlib
    python run_pipeline.py --no-stats                       # skip stats computation

Runs all three CNF encodings (native/naive, optimized/compact, logarithmic)
through CaDiCaL plus backtracking (MRV + forward checking), then writes
Results/benchmark_results.csv and generates plots.
"""

import os, sys, argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

BANNER = """
╔══════════════════════════════════════════════════════════╗
║     Sudoku SAT vs Backtracking Benchmark Pipeline        ║
║                                                          ║
║  CNF Encodings:                                          ║
║    native    : N^3 direct encoding (naive)               ║
║    optimized : Kwon & Jain compact encoding              ║
║    logarithmic: Gavanelli log-support binary encoding    ║
║                                                          ║
║  SAT solver : CaDiCaL (auto-detect)                      ║
║  Backtracking: MRV + degree heuristic + forward checking ║
║  Solver timeout: 120 seconds                             ║
╚══════════════════════════════════════════════════════════╝
"""


def main():
    print(BANNER)
    parser = argparse.ArgumentParser(
        description="Unified 3-encoding Sudoku SAT vs Backtracking pipeline"
    )
    parser.add_argument("--solver", default=None,
                        help="Path to SAT solver binary (default: auto-find)")
    parser.add_argument("--generator", choices=["both", "legacy", "back_circulant"],
                        default="both",
                        help="Puzzle generator: both (default), legacy, or back_circulant")
    parser.add_argument("--sizes", nargs="+", type=int, default=[4, 9, 16, 25, 36],
                        help="Grid sizes (default: 4 9 16 25 36)")
    parser.add_argument("--puzzles-per-size", type=int, default=30,
                        help="Puzzles per size per generator (default: 30)")
    parser.add_argument("--repeats", type=int, default=1,
                        help="Repetition runs (default: 1)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Master random seed (default: 42)")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Solver/backtracking timeout in seconds (default: 120)")
    parser.add_argument("--no-plot", action="store_true",
                        help="Skip plot generation")
    parser.add_argument("--no-stats", action="store_true",
                        help="Skip statistical analysis computation")
    parser.add_argument("--no-save-solutions", action="store_true",
                        help="Skip writing per-run solution and comparison files")
    parser.add_argument("--no-save-assignments", action="store_true",
                        help="Skip saving raw SAT assignments")
    parser.add_argument("--solution-dir", default=None,
                        help="Directory for solution artifacts (default: Results/Solutions)")
    args = parser.parse_args()

    from unified_benchmark import run_benchmark_pipeline
    csv_path = run_benchmark_pipeline(
        sizes=args.sizes,
        puzzles_per_size=args.puzzles_per_size,
        repeats=args.repeats,
        seed=args.seed,
        solver_path=args.solver,
        timeout=args.timeout,
        no_plot=args.no_plot,
        no_stats=args.no_stats,
        generator=args.generator,
        solution_dir=args.solution_dir,
        save_solutions=not args.no_save_solutions,
        save_assignments=not args.no_save_assignments,
    )

    print("\n" + "=" * 58)
    print("  Pipeline complete!")
    print(f"  CSV     -> {csv_path}")
    print("  Plots   -> ../../Results/")
    print("  Sol     -> ../../Results/Solutions/<generator>/")
    if not args.no_save_solutions:
        details_dir = args.solution_dir or os.path.join(
            os.path.dirname(csv_path), "Solutions"
        )
        print(f"  Details -> {details_dir}")
    print("=" * 58)


if __name__ == "__main__":
    main()
