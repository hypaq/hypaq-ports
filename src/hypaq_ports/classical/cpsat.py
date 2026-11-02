# SPDX-License-Identifier: Apache-2.0
"""OR-Tools CP-SAT adapter for the existing discrete, single-slot BAP.

The input schema and operational validator are shared with reference.py.
No exact enumeration, QUBO, quantum backend, or fallback solver is invoked.
OR-Tools is imported only when solve_berth_cpsat() is called.
"""

import math
from numbers import Real
from time import perf_counter

from hypaq_ports.reference import berth_metrics, check_berth_instance


_STATUS_DESCRIPTIONS = {
    "OPTIMAL": "A feasible schedule was found and optimality was proved.",
    "FEASIBLE": "A feasible schedule was found; optimality was not proved.",
    "INFEASIBLE": "The solver proved that no schedule satisfies this model.",
    "UNKNOWN": "No feasible schedule is available; infeasibility was not proved.",
    "MODEL_INVALID": "The CP-SAT model was rejected; this is not proof of infeasibility.",
}


def _check_options(time_limit_seconds, num_workers, random_seed, log_search_progress):
    if (isinstance(time_limit_seconds, bool)
            or not isinstance(time_limit_seconds, Real)
            or not math.isfinite(time_limit_seconds) or time_limit_seconds <= 0):
        raise ValueError("time_limit_seconds must be finite and strictly positive")
    if type(num_workers) is not int or num_workers < 1:
        raise ValueError("num_workers must be a positive integer")
    if type(random_seed) is not int or not 0 <= random_seed <= 2**31 - 1:
        raise ValueError("random_seed must be an integer in [0, 2**31 - 1]")
    if type(log_search_progress) is not bool:
        raise ValueError("log_search_progress must be a boolean")


def solve_berth_cpsat(instance, *, time_limit_seconds=10.0, num_workers=1,
                      random_seed=42, log_search_progress=False):
    """Minimize total waiting slots for the same base BAP as solve_berth_exact.

    Each vessel is assigned exactly once to an available compatible berth and a
    listed slot at/after arrival. Services occupy one slot. Berth/slot collisions
    are forbidden. No crane coupling, stability objective, or frozen assignments
    is included. Input data is not modified; ties may differ from enumeration.

    ``status`` is OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN, or MODEL_INVALID.
    Only OPTIMAL/FEASIBLE expose an incumbent: schedule, metrics, and score.
    Otherwise schedule is [], metrics/score/bound/gap are None. Invalid input or
    options raise ValueError (or the existing schema checker's input errors).

    ``elapsed_seconds`` includes validation, model construction, solving, decoding,
    and independent operational checks; dependency imports are excluded.
    ``solver_wall_time_seconds`` is CP-SAT's solve-only wall time. The time limit
    applies to solving, not model construction or report processing.

    OR-Tools 9.14.6206 is the tested version. A single worker and fixed seed are
    defaults for repeatable experiments, not a cross-version tie-break guarantee.
    """
    _check_options(time_limit_seconds, num_workers, random_seed, log_search_progress)
    try:
        import ortools
        from ortools.sat.python import cp_model
    except ImportError as exc:
        raise ImportError(
            "BAP CP-SAT requires OR-Tools. From the repository root run: "
            "python -m pip install -r requirements-classical.txt"
        ) from exc

    started = perf_counter()
    check_berth_instance(instance)
    # The shared checker accepts True == 1; require an actual integer duration.
    if any(type(v["service_slots"]) is not int for v in instance["vessels"]):
        raise ValueError("service_slots must be the integer 1")

    model = cp_model.CpModel()
    blocked = {(row["berth"], row["slot"])
               for row in instance.get("unavailable", [])}
    slots = sorted(instance["slots"])
    assignments, occupancy, objective_terms = [], {}, []
    objective_activity = 0
    for vessel_index, vessel in enumerate(instance["vessels"]):
        vessel_choices = []
        for berth_index, berth in enumerate(instance["berths"]):
            if berth not in vessel["compatible_berths"]:
                continue
            for slot in slots:
                if slot < vessel["arrival_slot"] or (berth, slot) in blocked:
                    continue
                waiting = slot - vessel["arrival_slot"]
                objective_activity += waiting
                # Bounds are returned by OR-Tools as doubles. Keep integer costs
                # and their full linear activity exactly representable as well.
                if objective_activity > 2**53 - 1:
                    raise ValueError("Waiting-cost activity exceeds the supported exact numeric range")
                variable = model.new_bool_var(f"x_{vessel_index}_{berth_index}_{slot}")
                vessel_choices.append(variable)
                occupancy.setdefault((berth, slot), []).append(variable)
                assignments.append((vessel["id"], berth, slot, variable))
                objective_terms.append(waiting * variable)
        # Empty ExactlyOne is a valid contradictory constraint, not invalid input.
        model.add_exactly_one(vessel_choices)
    for variables in occupancy.values():
        model.add_at_most_one(variables)
    model.minimize(sum(objective_terms))

    report = {
        "status": None,
        "method": "ortools_cp_sat",
        "schedule": [],
        "metrics": None,
        "score": None,
        "change_weight": 0,
        "has_solution": False,
        "proven_optimal": False,
        "best_objective_bound": None,
        "absolute_gap": None,
        "elapsed_seconds": None,
        "solver_wall_time_seconds": 0.0,
        "status_description": None,
        "model_validation_error": None,
        "solver_statistics": None,
        "configuration": {
            "time_limit_seconds": float(time_limit_seconds),
            "num_workers": num_workers,
            "random_seed": random_seed,
            "log_search_progress": log_search_progress,
        },
        "model": {
            "vessels": len(instance["vessels"]),
            "berths": len(instance["berths"]),
            "slots": len(slots),
            "assignment_variables": len(assignments),
            "objective": "minimize_total_waiting_slots",
            "service_slots": 1,
        },
        "environment": {"ortools": ortools.__version__},
        "timing_scope": "input validation, model construction, solve, decoding and operational validation; excludes dependency imports",
    }
    validation_error = model.validate()
    if validation_error:
        status = "MODEL_INVALID"
        report["model_validation_error"] = validation_error
    else:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(time_limit_seconds)
        solver.parameters.num_search_workers = num_workers
        solver.parameters.random_seed = random_seed
        solver.parameters.log_search_progress = log_search_progress
        native_status = solver.solve(model)
        status = solver.status_name(native_status)
        if status not in _STATUS_DESCRIPTIONS:
            raise RuntimeError(f"Unrecognized CP-SAT status: {status}")
        report["solver_wall_time_seconds"] = solver.wall_time
        report["solver_statistics"] = {
            "branches": solver.num_branches,
            "conflicts": solver.num_conflicts,
        }
        if status in ("OPTIMAL", "FEASIBLE"):
            schedule = [{"vessel": vessel, "berth": berth, "slot": slot}
                        for vessel, berth, slot, variable in assignments
                        if solver.value(variable)]
            metrics = berth_metrics(instance, schedule)
            if not metrics["feasible"]:
                raise RuntimeError(f"CP-SAT schedule failed the independent validator: {metrics['violations']}")
            score = metrics["total_waiting_slots"]
            if abs(solver.objective_value - score) > 1e-6:
                raise RuntimeError("CP-SAT objective differs from independently calculated waiting time")
            bound = solver.best_objective_bound
            report.update(
                schedule=schedule, metrics=metrics, score=score,
                has_solution=True, proven_optimal=(status == "OPTIMAL"),
                best_objective_bound=bound, absolute_gap=max(0.0, score - bound),
            )
        # Never read variables/objectives as incumbent data for UNKNOWN,
        # INFEASIBLE, or MODEL_INVALID; solver defaults are not a solution.
    report.update(status=status, status_description=_STATUS_DESCRIPTIONS[status],
                  elapsed_seconds=perf_counter() - started)
    return report
