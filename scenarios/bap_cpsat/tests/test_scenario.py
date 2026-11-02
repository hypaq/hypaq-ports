# SPDX-License-Identifier: Apache-2.0
"""CP-SAT BAP parity, operational constraints, and honest status reporting."""

import copy
import importlib.util
import json
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hypaq_ports.classical.cpsat import solve_berth_cpsat
from hypaq_ports.reference import load_json, solve_berth_exact, validate_berth_schedule

HAS_ORTOOLS = importlib.util.find_spec("ortools") is not None


@unittest.skipUnless(HAS_ORTOOLS, "Install scenarios/bap_cpsat/requirements.txt")
class BerthCpSatTests(unittest.TestCase):
    def setUp(self):
        self.instance = load_json(ROOT / "data/synthetic/berth_tiny_v1.json")

    def assert_parity(self, instance):
        exact = solve_berth_exact(instance)
        result = solve_berth_cpsat(instance)
        self.assertEqual(result["status"], exact["status"])
        self.assertEqual(result["score"], exact["score"])
        if result["has_solution"]:
            self.assertTrue(validate_berth_schedule(instance, result["schedule"])["feasible"])
        return result

    def test_published_instance_matches_exact_optimum(self):
        result = self.assert_parity(self.instance)
        self.assertEqual(result["score"], 0)
        self.assertTrue(result["proven_optimal"])
        self.assertEqual(result["absolute_gap"], 0)
        self.assertGreaterEqual(result["elapsed_seconds"], result["solver_wall_time_seconds"])

    def test_nonzero_waiting_cost(self):
        self.instance.update(berths=["B1"], slots=[0, 1, 2, 3])
        self.instance["vessels"] = [
            {"id": f"V{i}", "arrival_slot": 0, "service_slots": 1,
             "compatible_berths": ["B1"]} for i in range(3)]
        self.assertEqual(self.assert_parity(self.instance)["score"], 3)

    def test_compatibility_and_closures(self):
        self.instance["vessels"][0]["compatible_berths"] = ["B2"]
        self.instance["unavailable"] = [{"berth": "B2", "slot": 0}]
        self.assert_parity(self.instance)

    def test_arrivals_and_gapped_unsorted_slots(self):
        self.instance["slots"] = [5, 0, 2]
        self.instance["vessels"][1]["arrival_slot"] = 1
        self.assertEqual(self.assert_parity(self.instance)["score"], 1)

    def test_no_available_assignment_is_infeasible(self):
        self.instance["unavailable"] = [
            {"berth": b, "slot": t}
            for b in self.instance["berths"] for t in self.instance["slots"]]
        result = self.assert_parity(self.instance)
        for key in ["metrics", "score", "best_objective_bound", "absolute_gap"]:
            self.assertIsNone(result[key])
        self.assertEqual(result["schedule"], [])
        self.assertFalse(result["has_solution"])

    def test_capacity_collision_proves_infeasibility(self):
        self.instance.update(berths=["B1"], slots=[1])
        for vessel in self.instance["vessels"]:
            vessel["compatible_berths"] = ["B1"]
        self.assert_parity(self.instance)

    def test_input_is_unchanged_and_report_is_json_serializable(self):
        before = copy.deepcopy(self.instance)
        result = solve_berth_cpsat(self.instance)
        self.assertEqual(before, self.instance)
        self.assertEqual(json.loads(json.dumps(result))["score"], 0)

    def test_adapter_does_not_call_enumeration(self):
        with patch("hypaq_ports.reference.solve_berth_exact", side_effect=AssertionError("No enumeration")):
            self.assertEqual(solve_berth_cpsat(self.instance)["status"], "OPTIMAL")

    def test_invalid_options_are_rejected(self):
        for options in [
            {"time_limit_seconds": 0}, {"time_limit_seconds": -1},
            {"time_limit_seconds": float("nan")}, {"time_limit_seconds": float("inf")},
            {"time_limit_seconds": True}, {"num_workers": 0}, {"num_workers": True},
            {"random_seed": -1}, {"random_seed": 2**31}, {"random_seed": True},
            {"log_search_progress": 1},
        ]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                solve_berth_cpsat(self.instance, **options)

    def test_invalid_domain_and_multi_slot_services_are_rejected(self):
        for key, value in [("service_slots", 2), ("service_slots", True), ("arrival_slot", 0.5)]:
            instance = copy.deepcopy(self.instance)
            instance["vessels"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                solve_berth_cpsat(instance)

    def test_large_waiting_cost_rejected_without_rounding(self):
        self.instance["slots"] = [2**54]
        with self.assertRaises(ValueError):
            solve_berth_cpsat(self.instance)

    def _force_returned_status(self, status):
        # Use a real CP-SAT solve to obtain values, but override only its returned
        # status. This tests incumbent/status handling without timing-dependent
        # tests or assuming that a tiny instance will stop before proving optimality.
        from ortools.sat.python import cp_model
        original_solver = cp_model.CpSolver

        class StatusOverride:
            def __init__(self):
                self.inner = original_solver()
                self.parameters = self.inner.parameters

            def solve(self, model):
                self.inner.solve(model)
                return status

            def __getattr__(self, key):
                if key in ("value", "objective_value", "best_objective_bound") and status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                    raise AssertionError("No incumbent values may be read for this status")
                return getattr(self.inner, key)

        with patch.object(cp_model, "CpSolver", StatusOverride):
            return solve_berth_cpsat(self.instance)

    def test_feasible_is_not_promoted_to_optimal_even_when_cost_is_zero(self):
        from ortools.sat.python import cp_model
        result = self._force_returned_status(cp_model.FEASIBLE)
        self.assertEqual(result["status"], "FEASIBLE")
        self.assertTrue(result["has_solution"])
        self.assertFalse(result["proven_optimal"])
        self.assertEqual(result["score"], 0)

    def test_unknown_does_not_expose_values_or_claim_infeasibility(self):
        from ortools.sat.python import cp_model
        result = self._force_returned_status(cp_model.UNKNOWN)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["has_solution"])
        self.assertEqual(result["schedule"], [])
        self.assertIsNone(result["score"])
        self.assertIsNone(result["metrics"])

    def test_solver_model_invalid_is_distinct_from_infeasible(self):
        from ortools.sat.python import cp_model
        result = self._force_returned_status(cp_model.MODEL_INVALID)
        self.assertEqual(result["status"], "MODEL_INVALID")
        self.assertIsNone(result["score"])

    def test_model_validation_error_is_reported(self):
        from ortools.sat.python import cp_model
        with patch.object(cp_model.CpModel, "validate", return_value="Controlled model validation error"):
            result = solve_berth_cpsat(self.instance)
        self.assertEqual(result["status"], "MODEL_INVALID")
        self.assertIn("Controlled", result["model_validation_error"])
        self.assertFalse(result["has_solution"])

    def test_random_small_instances_match_exhaustive_reference(self):
        rng = random.Random(20261102)
        for case in range(128):
            berths = [f"B{i}" for i in range(rng.randint(1, 2))]
            slots = rng.sample([0, 1, 2, 4], rng.randint(1, 3))
            vessels = []
            for i in range(rng.randint(1, 4)):
                vessels.append({"id": f"V{i}", "arrival_slot": rng.randint(0, max(slots) + 1),
                                "service_slots": 1,
                                "compatible_berths": rng.sample(berths, rng.randint(1, len(berths)))})
            instance = {"berths": berths, "slots": slots, "vessels": vessels,
                        "unavailable": [{"berth": b, "slot": t}
                                        for b in berths for t in slots if rng.random() < 0.2]}
            with self.subTest(case=case):
                self.assert_parity(instance)



# SPDX-License-Identifier: Apache-2.0
"""Integration checks for shared-instance comparison and explicit skipped runs."""

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hypaq_ports.reference import load_json

SPEC = importlib.util.spec_from_file_location("bap_comparison", HERE / "compare.py")
COMPARISON = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARISON)


@unittest.skipUnless(importlib.util.find_spec("ortools") is not None,
                     "Install scenarios/bap_cpsat/requirements.txt")
class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.instance = load_json(HERE / "data/berth_waiting_v1.json")

    def test_both_classical_methods_match_nonzero_optimum(self):
        report = COMPARISON.generate_comparison(self.instance)
        self.assertEqual(report["reference_optimal_waiting_slots"], 1)
        self.assertEqual(len(report["summary"]), 2)
        self.assertTrue(all(row["proven_optimal"] for row in report["summary"]))
        self.assertTrue(all(row["absolute_gap_to_reference"] == 0 for row in report["summary"]))

    def test_enumeration_guard_skips_search_and_cpsat_still_solves(self):
        with patch.object(COMPARISON, "solve_berth_exact", side_effect=AssertionError("Must not enumerate")):
            report = COMPARISON.generate_comparison(self.instance, enumeration_limit=1)
        self.assertEqual(report["results"]["enumeration"]["status"], "SKIPPED")
        self.assertEqual(report["results"]["cpsat"]["score"], 1)

    def test_infeasible_quantum_runs_are_explicitly_skipped(self):
        self.instance["slots"] = [0]
        report = COMPARISON.generate_comparison(self.instance, include_quantum=True)
        self.assertEqual(report["results"]["cpsat"]["status"], "INFEASIBLE")
        self.assertEqual(report["results"]["qaoa"]["status"], "SKIPPED")
        self.assertIsNone(report["summary"][2]["best_feasible_waiting_slots"])

    def test_large_quantum_encoding_is_explicitly_skipped(self):
        self.instance["slots"] = list(range(7))
        report = COMPARISON.generate_comparison(self.instance, include_quantum=True)
        self.assertEqual(report["results"]["cpsat"]["status"], "OPTIMAL")
        self.assertEqual(report["results"]["qaoa"]["status"], "SKIPPED")

    def test_inconclusive_classical_run_does_not_start_quantum_demo(self):
        unknown = {"status": "UNKNOWN", "has_solution": False, "score": None}
        with patch.object(COMPARISON, "solve_berth_cpsat", return_value=unknown):
            report = COMPARISON.generate_comparison(
                self.instance, include_quantum=True, skip_enumeration=True)
        self.assertEqual(report["results"]["qaoa"]["status"], "SKIPPED")
        self.assertIsNone(report["reference_optimal_waiting_slots"])



class OutputBoundaryTests(unittest.TestCase):
    def test_report_paths_cannot_target_original_results(self):
        paths = COMPARISON.output_paths(HERE / "results/temporary_comparison")
        self.assertTrue(all(path.is_relative_to(HERE) for path in paths))
        with self.assertRaises(ValueError):
            COMPARISON.output_paths(ROOT / "results/quantum/berth_comparison_reference")


if __name__ == "__main__":
    unittest.main()
