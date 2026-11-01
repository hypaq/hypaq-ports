# SPDX-License-Identifier: Apache-2.0
"""Behavioral checks against operational constraints and exhaustive truth tables."""

import copy
import itertools
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hypaq_ports.reference import (
    apply_arrival_delay, berth_metrics, build_berth_qubo, decode_berth_bits,
    evaluate_crane_schedule, load_json, qubo_energy, qubo_to_ising,
    solve_berth_exact, solve_crane_exact, validate_berth_schedule,
)


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.berth = load_json(ROOT / "data/synthetic/berth_tiny_v1.json")
        self.cranes = load_json(ROOT / "data/synthetic/cranes_tiny_v1.json")

    def test_berth_zero_wait_feasible_optimum(self):
        result = solve_berth_exact(self.berth)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["metrics"]["total_waiting_slots"], 0)
        self.assertTrue(validate_berth_schedule(self.berth, result["schedule"])["feasible"])

    def test_validator_rejects_collision_early_and_missing(self):
        invalid = [
            [{"vessel": "V1", "berth": "B1", "slot": 1}, {"vessel": "V2", "berth": "B1", "slot": 1}],
            [{"vessel": "V1", "berth": "B1", "slot": 0}, {"vessel": "V2", "berth": "B2", "slot": 0}],
            [{"vessel": "V1", "berth": "B1", "slot": 0}],
        ]
        for schedule in invalid:
            with self.subTest(schedule=schedule):
                self.assertFalse(validate_berth_schedule(self.berth, schedule)["feasible"])

    def test_infeasible_instance_has_no_objective(self):
        instance = copy.deepcopy(self.berth)
        instance["unavailable"] = [{"berth": b, "slot": t} for b in instance["berths"] for t in instance["slots"]]
        result = solve_berth_exact(instance)
        self.assertEqual(result["status"], "INFEASIBLE")
        self.assertIsNone(result["score"])

    def test_qubo_feasible_energy_and_all_ground_states(self):
        model = build_berth_qubo(self.berth)
        candidates = []
        for bits in itertools.product((0, 1), repeat=len(model["variables"])):
            energy = qubo_energy(model, bits)
            metrics = berth_metrics(self.berth, decode_berth_bits(model, bits))
            if metrics["feasible"]:
                self.assertEqual(energy, metrics["total_waiting_slots"])
            candidates.append((energy, metrics["feasible"]))
        ground = min(energy for energy, feasible in candidates)
        self.assertEqual(ground, solve_berth_exact(self.berth)["score"])
        self.assertTrue(all(feasible for energy, feasible in candidates if energy == ground))

    def test_qubo_ground_states_respect_compatibility_and_closures(self):
        instance = copy.deepcopy(self.berth)
        instance["vessels"][0]["compatible_berths"] = ["B2"]
        instance["unavailable"] = [{"berth": "B1", "slot": 1}]
        model = build_berth_qubo(instance)
        values = [(qubo_energy(model, bits), decode_berth_bits(model, bits))
                  for bits in itertools.product((0, 1), repeat=len(model["variables"]))]
        minimum = min(e for e, schedule in values)
        self.assertEqual(minimum, solve_berth_exact(instance)["score"])
        self.assertTrue(all(validate_berth_schedule(instance, s)["feasible"] for e, s in values if e == minimum))

    def test_ising_matches_every_binary_assignment_including_offset(self):
        model = build_berth_qubo(self.berth)
        ising = qubo_to_ising(model)
        for bits in itertools.product((0, 1), repeat=len(model["variables"])):
            z = [1 - 2 * x for x in bits]
            energy = ising["constant"] + sum(h * spin for h, spin in zip(ising["h"], z))
            energy += sum(j * z[a] * z[b] for (a, b), j in ising["j"].items())
            self.assertAlmostEqual(energy, qubo_energy(model, bits))

    def test_delay_keeps_original_data_and_stable_replan_changes_fewer(self):
        original = solve_berth_exact(self.berth)["schedule"]
        updated = apply_arrival_delay(self.berth, "V1", 1)
        self.assertEqual(self.berth["vessels"][0]["arrival_slot"], 0)
        self.assertFalse(berth_metrics(updated, original)["feasible"])
        free = solve_berth_exact(updated, original=original)
        stable = solve_berth_exact(updated, original=original, change_weight=2)
        self.assertEqual(free["metrics"]["total_waiting_slots"], 0)
        self.assertEqual(stable["metrics"]["total_waiting_slots"], 0)
        self.assertLess(stable["metrics"]["changed_vessels"], free["metrics"]["changed_vessels"])

    def test_crane_reference_covers_demand(self):
        result = solve_crane_exact(self.cranes)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["metrics"]["total_unmet_units"], 0)
        self.assertEqual(result["metrics"]["active_crane_slots"], 4)
        self.assertEqual(result["assignments_examined"], 81)

    def test_crane_double_assignment_rejected(self):
        schedule = [{"crane": "QC1", "slot": 0, "vessel": "V1"},
                    {"crane": "QC1", "slot": 0, "vessel": "V2"}]
        self.assertFalse(evaluate_crane_schedule(self.cranes, schedule)["feasible"])

    def test_insufficient_capacity_reports_unmet_demand(self):
        self.cranes["vessels"][0]["demand_units"] = 100
        self.assertGreater(solve_crane_exact(self.cranes)["metrics"]["total_unmet_units"], 0)


if __name__ == "__main__":
    unittest.main()
