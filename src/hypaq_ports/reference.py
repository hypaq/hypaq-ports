# SPDX-License-Identifier: Apache-2.0
"""Tiny exact references; no external dependencies or quantum execution.

All berth services occupy one integer time slot. Enumeration is intentionally
limited to small teaching instances, not intended for operational scale.
"""

import copy
import itertools
import json
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(value, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check_berth_instance(instance):
    """Validate the explicitly supported single-slot input model."""
    berths, slots, vessels = instance["berths"], instance["slots"], instance["vessels"]
    if not berths or len(set(berths)) != len(berths):
        raise ValueError("Berths must be nonempty and unique")
    if not slots or len(set(slots)) != len(slots) or any(type(t) is not int or t < 0 for t in slots):
        raise ValueError("Slots must be unique nonnegative integers")
    if not vessels or len({v["id"] for v in vessels}) != len(vessels):
        raise ValueError("Vessel IDs must be nonempty and unique")
    for vessel in vessels:
        if type(vessel["arrival_slot"]) is not int or vessel["arrival_slot"] < 0:
            raise ValueError("Arrivals must be nonnegative integers")
        if vessel.get("service_slots") != 1:
            raise ValueError("This reference supports one-slot services only")
        allowed = vessel["compatible_berths"]
        if not allowed or not set(allowed) <= set(berths):
            raise ValueError("Each vessel needs known compatible berths")
    for closed in instance.get("unavailable", []):
        if closed["berth"] not in berths or closed["slot"] not in slots:
            raise ValueError("Unavailable berth/slot must belong to the instance")


def validate_berth_schedule(instance, schedule):
    """Check the original operational constraints, independently of QUBO energy."""
    check_berth_instance(instance)
    vessels = {v["id"]: v for v in instance["vessels"]}
    blocked = {(x["berth"], x["slot"]) for x in instance.get("unavailable", [])}
    errors, seen, occupied = [], set(), set()
    for row in schedule:
        vid, berth, slot = row.get("vessel"), row.get("berth"), row.get("slot")
        if vid not in vessels:
            errors.append("Unknown vessel")
            continue
        if vid in seen:
            errors.append(f"Duplicate assignment: {vid}")
        seen.add(vid)
        if berth not in instance["berths"] or berth not in vessels[vid]["compatible_berths"]:
            errors.append(f"Incompatible berth: {vid}")
        if type(slot) is not int or slot not in instance["slots"]:
            errors.append(f"Invalid slot: {vid}")
            continue
        if slot < vessels[vid]["arrival_slot"]:
            errors.append(f"Service before arrival: {vid}")
        if (berth, slot) in blocked:
            errors.append(f"Unavailable berth/slot: {vid}")
        if (berth, slot) in occupied:
            errors.append(f"Berth conflict: {berth}, {slot}")
        occupied.add((berth, slot))
    if seen != set(vessels):
        errors.append("Every vessel must have exactly one assignment")
    return {"feasible": not errors, "violations": errors}


def berth_metrics(instance, schedule, original=None):
    validation = validate_berth_schedule(instance, schedule)
    if not validation["feasible"]:
        return {**validation, "total_waiting_slots": None, "changed_vessels": None}
    arrivals = {v["id"]: v["arrival_slot"] for v in instance["vessels"]}
    waiting = sum(row["slot"] - arrivals[row["vessel"]] for row in schedule)
    before = {row["vessel"]: (row["berth"], row["slot"]) for row in original} if original is not None else None
    changed = sum(before.get(row["vessel"]) != (row["berth"], row["slot"]) for row in schedule) if before is not None else 0
    return {**validation, "total_waiting_slots": waiting, "changed_vessels": changed}


def solve_berth_exact(instance, original=None, change_weight=0):
    """Enumerate feasible assignments; ties use input ordering deterministically.

    score = total waiting slots + change_weight * number of changed vessels.
    No scheduling freeze is assumed. Passing a positive weight requires an
    original feasible schedule covering the same vessels (under its old data).
    """
    check_berth_instance(instance)
    if change_weight < 0 or (change_weight > 0 and original is None):
        raise ValueError("Use a nonnegative weight and supply an original schedule")
    if original is not None:
        if len(original) != len(instance["vessels"]) or {r["vessel"] for r in original} != {v["id"] for v in instance["vessels"]}:
            raise ValueError("Original schedule must cover each vessel exactly once")
    blocked = {(r["berth"], r["slot"]) for r in instance.get("unavailable", [])}
    options = [
        [(b, t) for b in instance["berths"] for t in sorted(instance["slots"])
         if b in v["compatible_berths"] and t >= v["arrival_slot"] and (b, t) not in blocked]
        for v in instance["vessels"]
    ]
    best, evaluated = None, 0
    for choices in itertools.product(*options):
        evaluated += 1
        if len(set(choices)) != len(choices):
            continue
        schedule = [{"vessel": v["id"], "berth": b, "slot": t}
                    for v, (b, t) in zip(instance["vessels"], choices)]
        metrics = berth_metrics(instance, schedule, original)
        score = metrics["total_waiting_slots"] + change_weight * metrics["changed_vessels"]
        if best is None or score < best["score"]:
            best = {"status": "OPTIMAL", "method": "exhaustive_enumeration",
                    "schedule": schedule, "metrics": metrics, "score": score,
                    "change_weight": change_weight}
    if best is None:
        best = {"status": "INFEASIBLE", "method": "exhaustive_enumeration", "schedule": [], "score": None}
    best["assignments_examined"] = evaluated
    return best


def build_berth_qubo(instance, penalty=None):
    """Return E(x)=offset+sum Q[i,j]*x[i]*x[j], upper triangular Q.

    Variables cover every vessel/berth/slot, including forbidden choices.
    Penalties enforce one choice per vessel, allowed choices, and no conflicts.
    The default penalty exceeds an upper bound on any feasible waiting cost.
    """
    check_berth_instance(instance)
    bound = sum(max(0, max(instance["slots"]) - v["arrival_slot"]) for v in instance["vessels"])
    penalty = bound + 1 if penalty is None else penalty
    if penalty <= bound:
        raise ValueError("Penalty must exceed the feasible waiting-cost upper bound")
    variables = [{"vessel": v["id"], "berth": b, "slot": t}
                 for v in instance["vessels"] for b in instance["berths"] for t in sorted(instance["slots"])]
    q = {}
    def add(i, j, value):
        key = tuple(sorted((i, j)))
        q[key] = q.get(key, 0) + value
    blocked = {(r["berth"], r["slot"]) for r in instance.get("unavailable", [])}
    vessels = {v["id"]: v for v in instance["vessels"]}
    for i, row in enumerate(variables):
        v = vessels[row["vessel"]]
        add(i, i, max(0, row["slot"] - v["arrival_slot"]) - penalty)
        if row["berth"] not in v["compatible_berths"] or row["slot"] < v["arrival_slot"] or (row["berth"], row["slot"]) in blocked:
            add(i, i, penalty)
        for j in range(i + 1, len(variables)):
            other = variables[j]
            if row["vessel"] == other["vessel"]:
                add(i, j, 2 * penalty)
            elif (row["berth"], row["slot"]) == (other["berth"], other["slot"]):
                add(i, j, penalty)
    return {"variables": variables, "q": q, "offset": penalty * len(vessels), "penalty": penalty}


def qubo_energy(model, bits):
    if len(bits) != len(model["variables"]) or any(x not in (0, 1) for x in bits):
        raise ValueError("Expected one binary value per variable")
    return model["offset"] + sum(coef * bits[i] * bits[j] for (i, j), coef in model["q"].items())


def decode_berth_bits(model, bits):
    qubo_energy(model, bits)  # Check length and binary values before decoding.
    return [dict(row) for row, bit in zip(model["variables"], bits) if bit]


def qubo_to_ising(model):
    """Map x=(1-z)/2, preserving the constant: E=constant+sum h*z+sum J*z*z."""
    h, interactions = [0.0] * len(model["variables"]), {}
    constant = float(model["offset"])
    for (i, j), coef in model["q"].items():
        if i == j:
            constant += coef / 2
            h[i] -= coef / 2
        else:
            constant += coef / 4
            h[i] -= coef / 4
            h[j] -= coef / 4
            interactions[(i, j)] = coef / 4
    return {"constant": constant, "h": h, "j": interactions}


def apply_arrival_delay(instance, vessel_id, delay_slots):
    check_berth_instance(instance)
    if type(delay_slots) is not int or delay_slots < 0:
        raise ValueError("Delay must be a nonnegative integer")
    updated = copy.deepcopy(instance)
    for vessel in updated["vessels"]:
        if vessel["id"] == vessel_id:
            vessel["arrival_slot"] += delay_slots
            return updated
    raise ValueError("Unknown vessel ID")


def evaluate_crane_schedule(instance, schedule):
    """Single crane-to-vessel assignment per period; fixed productivity.

    Every vessel can be served in every listed period. Oversupply is allowed
    but clipped when reporting served demand. This is allocation, not QCSP.
    """
    rates = {c["id"]: c["units_per_slot"] for c in instance["cranes"]}
    demand = {v["id"]: v["demand_units"] for v in instance["vessels"]}
    if not rates or len(rates) != len(instance["cranes"]) or not demand or len(demand) != len(instance["vessels"]):
        raise ValueError("Crane and vessel IDs must be nonempty and unique")
    if not instance["slots"] or len(set(instance["slots"])) != len(instance["slots"]):
        raise ValueError("Slots must be nonempty and unique")
    if any(x <= 0 for x in rates.values()) or any(x < 0 for x in demand.values()):
        raise ValueError("Productivity must be positive and demand nonnegative")
    errors, seen, capacity = [], set(), {v: 0 for v in demand}
    for row in schedule:
        c, v, t = row.get("crane"), row.get("vessel"), row.get("slot")
        if c not in rates or v not in demand or t not in instance["slots"]:
            errors.append("Unknown crane, vessel, or slot")
            continue
        if (c, t) in seen:
            errors.append("Crane assigned more than once in a period")
        seen.add((c, t))
        capacity[v] += rates[c]
    served = {v: min(demand[v], capacity[v]) for v in demand}
    return {"feasible": not errors, "violations": errors,
            "served_units": served, "unmet_units": {v: demand[v] - served[v] for v in demand},
            "total_unmet_units": sum(demand.values()) - sum(served.values()),
            "active_crane_slots": len(schedule),
            "utilization": len(seen) / (len(rates) * len(instance["slots"])) if not errors else None}


def solve_crane_exact(instance):
    evaluate_crane_schedule(instance, [])  # Validate supported data.
    pairs = [(c["id"], t) for c in instance["cranes"] for t in instance["slots"]]
    options = [None] + [v["id"] for v in instance["vessels"]]
    best, evaluated = None, 0
    for allocation in itertools.product(options, repeat=len(pairs)):
        evaluated += 1
        schedule = [{"crane": c, "slot": t, "vessel": v} for (c, t), v in zip(pairs, allocation) if v is not None]
        metrics = evaluate_crane_schedule(instance, schedule)
        key = (metrics["total_unmet_units"], metrics["active_crane_slots"])
        if best is None or key < best[0]:
            best = (key, schedule, metrics)
    return {"status": "OPTIMAL", "method": "exhaustive_enumeration",
            "objective_order": ["total_unmet_units", "active_crane_slots"],
            "schedule": best[1], "metrics": best[2], "assignments_examined": evaluated}
