import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiment" / "Main"))

import backtracking_solver
import plot_results
import puzzle_manager
import sat_solver_runner
import unified_benchmark


class SeededGenerationTests(unittest.TestCase):
    def test_seed_derivation_is_stable_and_coordinate_specific(self):
        first = puzzle_manager.derive_puzzle_seed(42, "legacy", 16, 3)
        self.assertEqual(first, puzzle_manager.derive_puzzle_seed(42, "legacy", 16, 3))
        self.assertNotEqual(first, puzzle_manager.derive_puzzle_seed(42, "back_circulant", 16, 3))
        self.assertNotEqual(first, puzzle_manager.derive_puzzle_seed(42, "legacy", 16, 4))
        self.assertNotEqual(first, puzzle_manager.derive_puzzle_seed(42, "legacy", 16, 3, 1))

    def test_puzzle_name_contains_seed_and_generator(self):
        name = puzzle_manager.puzzle_name_for("legacy", 25, 123456, 7)
        self.assertIn("legacy", name)
        self.assertIn("seed123456", name)
        self.assertIn("25x25", name)

    def test_default_solver_timeouts_are_120_seconds(self):
        self.assertEqual(unified_benchmark.TIMEOUT_SECONDS, 120)
        self.assertEqual(backtracking_solver.TIMEOUT_SECONDS, 120)
        self.assertEqual(plot_results.TIMEOUT_SECONDS, 120.0)
        for fn in (
            sat_solver_runner.run_solver,
            sat_solver_runner.run_solver_raw,
            sat_solver_runner.solve_cnf,
        ):
            self.assertEqual(inspect.signature(fn).parameters["timeout"].default, 120)


if __name__ == "__main__":
    unittest.main()
