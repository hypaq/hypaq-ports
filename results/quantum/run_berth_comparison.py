# SPDX-License-Identifier: Apache-2.0
"""Execute Ket/KBW QAOA and FALQON alongside the existing exact reference."""

import csv
import io
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from hypaq_ports.reference import load_json, save_json, solve_berth_exact
from hypaq_ports.quantum import run_qaoa, run_falqon


def comparison_rows(classical, qaoa, falqon):
    rows = [{"method": "Exact enumeration", "best_feasible_waiting_slots": classical["metrics"]["total_waiting_slots"],
             "exact_feasible_probability": None, "sampled_feasible_rate": None,
             "exact_optimal_probability": None, "full_qubo_energy": None,
             "cost_expectation_queries": None, "feedback_expectation_queries": None,
             "logical_gate_count": None, "logical_depth": None, "seconds": classical.get("elapsed_seconds")}]
    for result in (qaoa, falqon):
        m = result["metrics"]
        rows.append({"method": result["algorithm"], "best_feasible_waiting_slots": m["best_sampled_feasible_waiting_slots"],
                     "exact_feasible_probability": m["exact_feasible_probability"],
                     "sampled_feasible_rate": m["sampled_feasible_rate"],
                     "exact_optimal_probability": m["exact_optimal_probability"],
                     "full_qubo_energy": m["expected_full_qubo_energy"],
                     "cost_expectation_queries": result["cost_expectation_queries"],
                     "feedback_expectation_queries": result["feedback_expectation_queries"],
                     "logical_gate_count": result["logical_gate_count"], "logical_depth": result["logical_depth"],
                     "seconds": result["elapsed_seconds"]})
    return rows


def generate_comparison():
    config = load_json(ROOT / "results/quantum/berth_experiment.json")
    instance = load_json(ROOT / config["instance_path"])
    started = perf_counter()
    classical = solve_berth_exact(instance)
    classical["elapsed_seconds"] = perf_counter() - started
    qaoa = run_qaoa(instance, **config["common"], **config["qaoa"])
    falqon = run_falqon(instance, **config["common"], **config["falqon"])
    return {"configuration": config, "classical": classical, "qaoa": qaoa, "falqon": falqon,
            "summary": comparison_rows(classical, qaoa, falqon),
            "limitations": ["No quantum hardware", "No CP-SAT adapter in this package",
                            "Exact state-vector expectations, not shot-estimated training",
                            "Final seeded sampling uses a dumped KBW state, not native KBW or QPU measurements",
                            "Tiny zero-wait optimum; no relative approximation ratio",
                            "Resource budgets differ; no speedup or algorithm-ranking claim",
                            "FALQON first-order discretization may exhibit energy increases"]}


def save_comparison(report):
    folder = ROOT / "results/quantum"
    save_json(report, folder / "berth_comparison_reference.json")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(report["summary"][0]))
    writer.writeheader(); writer.writerows(report["summary"])
    (folder / "berth_comparison_summary.csv").write_text(stream.getvalue(), encoding="utf-8")


if __name__ == "__main__":
    report = generate_comparison()
    save_comparison(report)
    for row in report["summary"]:
        print(row)
