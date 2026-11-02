# SPDX-License-Identifier: Apache-2.0
"""Run the same one-slot BAP through exact enumeration, CP-SAT, and optional Ket.

This additional scenario reads existing sources/inputs without modifying them.
This is a live comparison, never a merge of old quantum reports and new timings.
Without --include-quantum, no Ket module is imported. Outputs have new names and
do not replace the original alpha's reference files.
"""

import argparse
import csv
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hypaq_ports.classical.cpsat import solve_berth_cpsat
from hypaq_ports.reference import check_berth_instance, load_json, save_json, solve_berth_exact


def _enumeration_size(instance, limit):
    blocked = {(row["berth"], row["slot"]) for row in instance.get("unavailable", [])}
    count = 1
    for vessel in instance["vessels"]:
        choices = sum(berth in vessel["compatible_berths"]
                      and slot >= vessel["arrival_slot"] and (berth, slot) not in blocked
                      for berth in instance["berths"] for slot in instance["slots"])
        count = min(limit + 1, count * choices)
    return count


def _summary_row(method, result, optimum, quantum=False):
    skipped = result.get("status") == "SKIPPED"
    metrics = result.get("metrics") or {}
    best = (metrics.get("best_sampled_feasible_waiting_slots") if quantum
            else metrics.get("total_waiting_slots"))
    feasible = best is not None if quantum else bool(metrics.get("feasible", False))
    return {
        "method": method,
        "status": "SKIPPED" if skipped else ("HEURISTIC" if quantum else result["status"]),
        "has_feasible_solution": None if skipped else feasible,
        "proven_optimal": False if quantum or skipped else result["status"] == "OPTIMAL",
        "best_feasible_waiting_slots": best,
        "reference_optimal_waiting_slots": optimum,
        "absolute_gap_to_reference": best - optimum if best is not None and optimum is not None else None,
        "matches_reference_optimum": best == optimum if best is not None and optimum is not None else None,
        "elapsed_seconds": result.get("elapsed_seconds"),
        "solver_wall_time_seconds": result.get("solver_wall_time_seconds"),
        "best_objective_bound": result.get("best_objective_bound"),
        "exact_feasible_probability": metrics.get("exact_feasible_probability"),
        "exact_optimal_probability": metrics.get("exact_optimal_probability"),
        "sampled_feasible_rate": metrics.get("sampled_feasible_rate"),
        "logical_gate_count": result.get("logical_gate_count"),
        "logical_depth": result.get("logical_depth"),
        "cost_expectation_queries": result.get("cost_expectation_queries"),
        "feedback_expectation_queries": result.get("feedback_expectation_queries"),
        "note": result.get("reason", ""),
    }


def generate_comparison(instance, *, include_quantum=False, quantum_configuration=None,
                        time_limit_seconds=10.0, num_workers=1, random_seed=42,
                        enumeration_limit=100000, skip_enumeration=False):
    """Execute independent methods against one shared instance and validator.

    The enumeration guard caps candidate combinations, not CP-SAT problem size.
    Existing Ket runners independently enumerate tiny references inside their
    preparation; --skip-enumeration does not change those original runners.
    """
    check_berth_instance(instance)
    if type(enumeration_limit) is not int or enumeration_limit < 1:
        raise ValueError("enumeration_limit must be a positive integer")
    if skip_enumeration or _enumeration_size(instance, enumeration_limit) > enumeration_limit:
        enumeration = {"status": "SKIPPED", "reason": "Enumeration disabled or candidate count exceeds enumeration_limit"}
    else:
        started = perf_counter()
        enumeration = solve_berth_exact(instance)
        enumeration["elapsed_seconds"] = perf_counter() - started
    cpsat = solve_berth_cpsat(instance, time_limit_seconds=time_limit_seconds,
                             num_workers=num_workers, random_seed=random_seed)
    if enumeration["status"] == "OPTIMAL":
        if cpsat["status"] == "INFEASIBLE":
            raise RuntimeError("CP-SAT contradicts the feasible exact reference")
        if cpsat["status"] == "OPTIMAL" and cpsat["score"] != enumeration["score"]:
            raise RuntimeError("CP-SAT and enumeration disagree on the optimum")
    elif enumeration["status"] == "INFEASIBLE" and cpsat["has_solution"]:
        raise RuntimeError("CP-SAT incumbent contradicts exact infeasibility")
    optimum = (enumeration["score"] if enumeration["status"] == "OPTIMAL"
               else cpsat["score"] if cpsat["status"] == "OPTIMAL" else None)
    methods = {"enumeration": enumeration, "cpsat": cpsat}
    rows = [_summary_row("Exact enumeration", enumeration, optimum),
            _summary_row("OR-Tools CP-SAT", cpsat, optimum)]
    if include_quantum:
        encoded_qubits = len(instance["vessels"]) * len(instance["berths"]) * len(instance["slots"])
        if enumeration["status"] == "INFEASIBLE" or cpsat["status"] == "INFEASIBLE":
            reason = "Original Ket demonstrations require a feasible tiny BAP"
        elif encoded_qubits > 12:
            reason = "Original Ket adapter supports at most 12 encoded qubits"
        elif not cpsat["has_solution"] and enumeration["status"] != "OPTIMAL":
            reason = "No classical method established feasibility; quantum demonstrations were not started"
        else:
            reason = None
        if reason:
            for key, label in [("qaoa", "QAOA (Ket/KBW)"), ("falqon", "FALQON (Ket/KBW)")]:
                result = {"status": "SKIPPED", "reason": reason}
                methods[key] = result
                rows.append(_summary_row(label, result, optimum, quantum=True))
        else:
            from hypaq_ports.quantum import run_qaoa, run_falqon
            if quantum_configuration is None:
                quantum_configuration = load_json(ROOT / "results/quantum/berth_experiment.json")
            for key, label, runner in [("qaoa", "QAOA (Ket/KBW)", run_qaoa),
                                       ("falqon", "FALQON (Ket/KBW)", run_falqon)]:
                result = runner(instance, **quantum_configuration["common"], **quantum_configuration[key])
                methods[key] = result
                rows.append(_summary_row(label, result, optimum, quantum=True))
    return {
        "report_schema": "bap_solver_comparison_0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "instance": instance,
        "instance_id": instance.get("instance_id", "unnamed"),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "configuration": {
            "include_quantum": include_quantum, "time_limit_seconds": time_limit_seconds,
            "num_workers": num_workers, "random_seed": random_seed,
            "enumeration_limit": enumeration_limit, "skip_enumeration": skip_enumeration,
            "quantum": quantum_configuration if include_quantum else None,
        },
        "reference_optimal_waiting_slots": optimum,
        "results": methods,
        "summary": rows,
        "limitations": [
            "Simplified discrete BAP with one-slot services and synthetic data",
            "Different formulations and compute budgets; not a speedup or algorithm-ranking benchmark",
            "Elapsed times exclude dependency imports and have method-specific scope; see each detailed report",
            "Original Ket runners include exact tiny-reference preparation and exclude final report validation from their timer",
            "Quantum expectations are exact simulator values; default final sampling uses a state snapshot",
            "Logical final-circuit resources are not total training or hardware costs",
            "CP-SAT ties may differ from enumeration without changing objective or feasibility",
        ],
    }


def output_paths(prefix):
    """Keep every generated report inside this additional scenario folder."""
    prefix = Path(prefix).resolve()
    paths = Path(str(prefix) + ".json"), Path(str(prefix) + ".csv")
    if not all(path.is_relative_to(HERE.resolve()) for path in paths):
        raise ValueError("Output prefix must stay inside scenarios/bap_cpsat; original reports are protected")
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path, default=ROOT / "data/synthetic/berth_tiny_v1.json")
    parser.add_argument("--include-quantum", action="store_true")
    parser.add_argument("--time-limit", type=float, default=10.0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--enumeration-limit", type=int, default=100000)
    parser.add_argument("--skip-enumeration", action="store_true")
    parser.add_argument("--output-prefix", type=Path, default=HERE / "results/bap_comparison")
    args = parser.parse_args()
    json_path, csv_path = output_paths(args.output_prefix)
    report = generate_comparison(
        load_json(args.instance), include_quantum=args.include_quantum,
        time_limit_seconds=args.time_limit, num_workers=args.workers, random_seed=args.seed,
        enumeration_limit=args.enumeration_limit, skip_enumeration=args.skip_enumeration)
    save_json(report, json_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(report["summary"][0]))
        writer.writeheader()
        writer.writerows(report["summary"])
    for row in report["summary"]:
        print(f"{row['method']}: status={row['status']}, waiting={row['best_feasible_waiting_slots']}, seconds={row['elapsed_seconds']}")
    print(json_path)
    print(csv_path)


if __name__ == "__main__":
    main()
