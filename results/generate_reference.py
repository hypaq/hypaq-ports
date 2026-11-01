# SPDX-License-Identifier: Apache-2.0
"""Regenerate classical reference outputs; no quantum backend is invoked."""

import itertools
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hypaq_ports import __version__
from hypaq_ports.reference import (
    apply_arrival_delay, berth_metrics, build_berth_qubo, decode_berth_bits,
    load_json, qubo_energy, qubo_to_ising, save_json,
    solve_berth_exact, solve_crane_exact,
)


def generate():
    berth = load_json(ROOT / "data/synthetic/berth_tiny_v1.json")
    cranes = load_json(ROOT / "data/synthetic/cranes_tiny_v1.json")
    scenario = load_json(ROOT / "data/synthetic/disruption_tiny_v1.json")
    original = solve_berth_exact(berth)
    event = scenario["event"]
    if event["type"] != "arrival_delay":
        raise ValueError("Only arrival_delay is implemented")
    updated = apply_arrival_delay(berth, event["vessel"], event["delay_slots"])
    model, minimum, ground, max_error = build_berth_qubo(berth), float("inf"), [], 0
    ising = qubo_to_ising(model)
    for bits in itertools.product((0, 1), repeat=len(model["variables"])):
        energy = qubo_energy(model, bits)
        spins = [1 - 2 * x for x in bits]
        ising_energy = ising["constant"] + sum(h * z for h, z in zip(ising["h"], spins))
        ising_energy += sum(j * spins[i] * spins[k] for (i, k), j in ising["j"].items())
        max_error = max(max_error, abs(energy - ising_energy))
        if energy < minimum:
            minimum, ground = energy, []
        if energy == minimum:
            ground.append({"bits": list(bits), "metrics": berth_metrics(berth, decode_berth_bits(model, bits))})
    return {
        "package_version": __version__, "python_version": platform.python_version(),
        "execution": "classical_standard_library_only", "quantum_execution": False,
        "instance_ids": [berth["instance_id"], cranes["instance_id"], scenario["scenario_id"]],
        "berth": original,
        "berth_qubo": {"binary_variables": len(model["variables"]), "bitstrings_evaluated": 2 ** len(model["variables"]),
                       "penalty": model["penalty"], "offset": model["offset"], "minimum_energy": minimum,
                       "ground_states": ground, "max_qubo_ising_energy_error": max_error},
        "cranes": solve_crane_exact(cranes),
        "disruption": {"configuration": scenario,
                       "original_plan_under_disruption": berth_metrics(updated, original["schedule"]),
                       "free_replanning": solve_berth_exact(updated, original=original["schedule"]),
                       "stable_replanning": solve_berth_exact(updated, original=original["schedule"],
                           change_weight=scenario["change_weight_waiting_slots_per_vessel"])},
    }


if __name__ == "__main__":
    target = ROOT / "results/reference_results.json"
    save_json(generate(), target)
    print(target)
