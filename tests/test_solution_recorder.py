import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiment" / "Main"))

import solution_recorder as recorder
import sat_solver_runner


GRID_A = [
    [1, 2],
    [2, 1],
]
GRID_B = [
    [1, 2],
    [2, 2],
]


class SolutionRecorderTests(unittest.TestCase):
    def test_grid_hash_and_model_hash(self):
        self.assertEqual(recorder.grid_hash(GRID_A), recorder.grid_hash([row[:] for row in GRID_A]))
        self.assertNotEqual(recorder.grid_hash(GRID_A), recorder.grid_hash(GRID_B))
        self.assertEqual(recorder.model_hash([3, 1, 2]), recorder.model_hash([2, 3, 1]))
        self.assertNotEqual(recorder.model_hash([3, 1, 2]), recorder.model_hash([3, 1]))

    def test_grid_matches_clues(self):
        puzzle = [[1, 0], [0, 1]]
        self.assertTrue(recorder.grid_matches_clues(GRID_A, puzzle))
        self.assertFalse(recorder.grid_matches_clues(GRID_B, puzzle))

    def test_compare_solutions_equal_and_mismatch(self):
        reference = GRID_A
        solutions = {
            "compact": GRID_A,
            "naive": GRID_A,
            "log": GRID_A,
            "bt": GRID_A,
        }
        comparison = recorder.compare_solutions(2, reference, solutions)
        self.assertEqual(comparison["all_equal"], "YES")
        self.assertEqual(comparison["all_match_reference"], "YES")
        self.assertEqual(comparison["all_methods_solved"], "YES")
        self.assertEqual(comparison["mismatch_count"], 0)

        solutions["log"] = GRID_B
        comparison = recorder.compare_solutions(2, reference, solutions)
        self.assertEqual(comparison["all_equal"], "NO")
        self.assertEqual(comparison["all_match_reference"], "NO")
        self.assertEqual(comparison["matches_bt"]["log"], "NO")
        self.assertGreater(comparison["mismatch_count"], 0)

    def test_compare_solutions_missing_reference(self):
        comparison = recorder.compare_solutions(2, None, {"compact": GRID_A, "bt": GRID_A})
        self.assertEqual(comparison["reference_present"], "NO")
        self.assertEqual(comparison["all_equal"], "YES")
        self.assertEqual(comparison["all_match_reference"], "N/A")
        self.assertEqual(comparison["all_methods_solved"], "NO")
        self.assertEqual(comparison["solved_count"], 2)

    def test_writers_and_reference_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            puzzle_path = os.path.join(tmp, "puzzle.txt")
            with open(puzzle_path, "w", encoding="utf-8") as handle:
                handle.write("SIZE 2\nPUZZLE\n1 0\n0 1\nSOLUTION\n1 2\n2 1\n")

            reference = recorder.read_reference_solution(puzzle_path, 2)
            self.assertEqual(reference, GRID_A)

            solution_path = os.path.join(tmp, "run_01_compact_solution.txt")
            recorder.write_solution_file(
                solution_path,
                size=2,
                puzzle_name="puzzle",
                run_id="run_0001",
                repeat=1,
                method="compact",
                encoding="compact",
                status="solved",
                solve_time_s=0.1,
                e2e_time_s=0.2,
                grid=GRID_A,
                valid=True,
                matches_clues=True,
                matches_reference="YES",
                matches_bt="YES",
                all_equal="YES",
            )
            self.assertIn("SOLUTION\n1 2\n2 1\n", Path(solution_path).read_text())

            assignment_path = os.path.join(tmp, "run_01_compact_assignment.txt")
            recorder.write_assignment_file(
                assignment_path,
                puzzle_name="puzzle",
                run_id="run_0001",
                repeat=1,
                method="compact",
                encoding="compact",
                cnf_path="/tmp/puzzle_compact.cnf",
                status="solved",
                solve_time_s=0.1,
                raw_lines=["v 1 -2 3 0"],
                model_hash_value=recorder.model_hash([1, 3]),
            )
            assignment_text = Path(assignment_path).read_text()
            self.assertIn("RAW_LITERAL_COUNT 3", assignment_text)
            self.assertIn("RAW_ASSIGNMENT\nv 1 -2 3 0\n", assignment_text)

            comparison = recorder.compare_solutions(2, GRID_A, {"compact": GRID_A, "bt": GRID_A})
            report_path = os.path.join(tmp, "run_01_report.txt")
            recorder.write_report(
                report_path,
                size=2,
                puzzle_name="puzzle",
                run_id="run_0001",
                repeat=1,
                reference=GRID_A,
                solutions={"compact": GRID_A, "bt": GRID_A},
                method_rows=[
                    {
                        "method": "compact",
                        "status": "solved",
                        "solve_time_s": "0.100000",
                        "grid_hash": recorder.grid_hash(GRID_A),
                        "valid": "YES",
                        "matches_clues": "YES",
                        "matches_reference": "YES",
                        "matches_bt": "YES",
                    },
                    {
                        "method": "bt",
                        "status": "solved",
                        "solve_time_s": "0.100000",
                        "grid_hash": recorder.grid_hash(GRID_A),
                        "valid": "YES",
                        "matches_clues": "YES",
                        "matches_reference": "YES",
                        "matches_bt": "N/A",
                    },
                ],
                comparison=comparison,
            )
            report_text = Path(report_path).read_text()
            self.assertIn("SOLUTION REPORT", report_text)
            self.assertIn("COMPACT SOLUTION", report_text)
            self.assertIn("DIFFERENCES\nnone", report_text)

    def test_run_solver_raw_captures_signed_literals(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_solver = os.path.join(tmp, "fake_solver")
            with open(fake_solver, "w", encoding="utf-8") as handle:
                handle.write(
                    "#!/usr/bin/env python3\n"
                    "import sys\n"
                    "print('s SATISFIABLE')\n"
                    "print('v 1 -2 3 0')\n"
                    "sys.exit(10)\n"
                )
            os.chmod(fake_solver, stat.S_IRWXU)

            old_temp_dir = sat_solver_runner.TEMP_DIR
            sat_solver_runner.TEMP_DIR = tmp
            try:
                cnf_path = os.path.join(tmp, "fake.cnf")
                with open(cnf_path, "w", encoding="utf-8") as handle:
                    handle.write("p cnf 3 1\n1 2 3 0\n")
                sat, assignment, elapsed, raw_lines = sat_solver_runner.run_solver_raw(
                    fake_solver, cnf_path, timeout=5
                )
                sat2, assignment2, elapsed2 = sat_solver_runner.run_solver(
                    fake_solver, cnf_path, timeout=5
                )
            finally:
                sat_solver_runner.TEMP_DIR = old_temp_dir

            self.assertTrue(sat)
            self.assertEqual(assignment, [1, 3])
            self.assertEqual(raw_lines, ["v 1 -2 3 0"])
            self.assertGreaterEqual(elapsed, 0.0)
            self.assertTrue(sat2)
            self.assertEqual(assignment2, [1, 3])
            self.assertGreaterEqual(elapsed2, 0.0)


if __name__ == "__main__":
    unittest.main()
