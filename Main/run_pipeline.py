"""
run_pipeline.py  —  Master entry point

Usage:
    python run_pipeline.py                           # full run, auto-detect solver
    python run_pipeline.py --solver ./executable/satch
    python run_pipeline.py --no-sat                  # backtracking only
    python run_pipeline.py --no-bt                   # SAT only
    python run_pipeline.py --no-plot                 # skip matplotlib
"""

import os, sys, argparse, importlib.util

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

BANNER = """
╔══════════════════════════════════════════════════════════╗
║     Sudoku SAT vs Backtracking Benchmark Pipeline        ║
║     Optimised CNF Encoding  (Kwon & Jain, 2006)         ║
║                                                          ║
║  Puzzle sets:                                            ║
║    9x9  : 5 x 17-clue  +  5 x 5-clue                   ║
║    4x4  : 5 puzzles                                      ║
║    16x16: 5 puzzles                                      ║
║    25x25: 5 puzzles                                      ║
║    36x36: 5 puzzles                                      ║
║                                                          ║
║  Backtracking timeout: 45 minutes                        ║
╚══════════════════════════════════════════════════════════╝
"""

def main():
    print(BANNER)
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver",  default=None)
    parser.add_argument("--no-sat",  action="store_true")
    parser.add_argument("--no-bt",   action="store_true")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()

    def load(name):
        path = os.path.join(SCRIPT_DIR, name + ".py")
        spec = importlib.util.spec_from_file_location(name, path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    bm = load("benchmark")
    results = bm.run_benchmark(
        solver_path = args.solver,
        run_sat     = not args.no_sat,
        run_bt      = not args.no_bt,
    )

    if not args.no_plot:
        bm.plot(results)

    print("\n" + "="*58)
    print("  Pipeline complete!")
    print(f"  Puzzles   -> ../Puzzles/")
    print(f"  CNF files -> ../CNF/")
    print(f"  Solutions -> ../Output/Sol/")
    print(f"  Plots     -> ../Output/")
    print("="*58)

if __name__ == "__main__":
    main()