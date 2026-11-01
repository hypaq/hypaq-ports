# SPDX-License-Identifier: Apache-2.0
"""Explicit Ket circuits, simulator readout and operational solution validation.

The adapter uses x_i=(1-Z_i)/2, register index 0 is the leftmost bit, and
U_cost(gamma)=exp(-i*gamma*H_tilde), H_tilde=(H_cost-constant*I)/scale.
scale=max(1, max absolute nonconstant Ising coefficient). No fallback simulator
is used if Ket fails. dump/analytic expectations are simulator-only diagnostics.
"""

import math
import platform
from collections import Counter
from importlib.metadata import version

import ket

from hypaq_ports.reference import (
    berth_metrics, build_berth_qubo, decode_berth_bits, qubo_energy,
    qubo_to_ising, solve_berth_exact,
)


def finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite and numeric")
    return float(value)


def positive_integer(value, name, maximum=None):
    if type(value) is not int or value < 1 or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be a positive integer" + (f" <= {maximum}" if maximum else ""))
    return value


def validate_sampling(shots, seed, method):
    positive_integer(shots, "shots")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if method not in ("state_snapshot", "kbw_native"):
        raise ValueError("sampling must be state_snapshot or kbw_native")


def prepare_problem(instance, penalty=None):
    # Refuse a large Cartesian encoding BEFORE the existing enumerator runs.
    n = len(instance["vessels"]) * len(instance["berths"]) * len(instance["slots"])
    positive_integer(n, "qubits", maximum=12)
    if penalty is not None:
        finite_number(penalty, "penalty")
    reference = solve_berth_exact(instance)
    if reference["status"] != "OPTIMAL":
        raise ValueError("Quantum demonstration requires a feasible tiny reference instance")
    model = build_berth_qubo(instance, penalty=penalty)
    ising = qubo_to_ising(model)
    coefficients = list(ising["h"]) + list(ising["j"].values())
    scale = max(1.0, *(abs(c) for c in coefficients))
    return {"instance": instance, "model": model, "ising": ising, "scale": scale,
            "h": [c / scale for c in ising["h"]],
            "j": {pair: c / scale for pair, c in ising["j"].items()},
            "n": n, "reference": reference}


def bits_from_index(index, n):
    if type(index) is not int or index < 0 or index >= 2 ** n:
        raise ValueError("Basis state outside register")
    return [int(c) for c in format(index, f"0{n}b")]


class GateLog:
    """Syntactic logical gate count/depth; not hardware-transpiled resources."""

    def __init__(self, n):
        self.counts, self.levels = Counter(), [0] * n

    def record(self, gate, *wires):
        self.counts[gate] += 1
        level = 1 + max(self.levels[i] for i in wires)
        for i in wires:
            self.levels[i] = level

    def report(self):
        return {"logical_gate_counts": dict(self.counts), "logical_gate_count": sum(self.counts.values()),
                "logical_depth": max(self.levels),
                "resource_note": "Explicit logical gates; excludes observables, readout, compilation and feedback latency"}


def create_register(problem, execution="batch", simulator="sparse"):
    if simulator not in ("sparse", "dense"):
        raise ValueError("Use the tested CPU sparse or dense KBW simulator")
    process = ket.Process(num_qubits=problem["n"], simulator=simulator, execution=execution)
    register = process.alloc(problem["n"])
    log = GateLog(problem["n"])
    for i in range(problem["n"]):
        ket.H(register[i])
        log.record("H", i)
    return process, register, log


def apply_cost(problem, register, gamma, log):
    gamma = finite_number(gamma, "gamma")
    # Constant omitted from evolution (global phase), retained in reported energy.
    for i, h in enumerate(problem["h"]):
        if h * gamma != 0:
            ket.RZ(2 * gamma * h, register[i])
            log.record("RZ", i)
    for (i, j), coupling in sorted(problem["j"].items()):
        if coupling * gamma != 0:
            ket.CNOT(register[i], register[j]); log.record("CNOT", i, j)
            ket.RZ(2 * gamma * coupling, register[j]); log.record("RZ", j)
            ket.CNOT(register[i], register[j]); log.record("CNOT", i, j)


def apply_mixer(register, beta, log):
    beta = finite_number(beta, "beta")
    if beta != 0:
        for i in range(len(register)):
            ket.RX(2 * beta, register[i])
            log.record("RX", i)


def cost_observable(problem, register):
    with ket.obs():
        terms = [float(h) * ket.Z(register[i]) for i, h in enumerate(problem["h"]) if h]
        terms += [float(j) * ket.Z(register[i]) * ket.Z(register[k])
                  for (i, k), j in problem["j"].items() if j]
        if not terms:
            raise ValueError("Zero nonconstant Hamiltonian is not supported by this demo")
        return sum(terms)


def feedback_observable(problem, register):
    """Return -i[H_m,H_tilde] = -2 sum hY -2 sum J(YZ+ZY).

    For H_m=sum X, beta_next is this observable's expectation. Finite-step
    first-order splitting is monitored, not assumed monotonic or globally optimal.
    """
    with ket.obs():
        terms = [-2 * float(h) * ket.Y(register[i]) for i, h in enumerate(problem["h"]) if h]
        for (i, j), coupling in problem["j"].items():
            if coupling:
                terms.append(-2 * float(coupling) * ket.Y(register[i]) * ket.Z(register[j]))
                terms.append(-2 * float(coupling) * ket.Z(register[i]) * ket.Y(register[j]))
        return sum(terms)


def full_energy(problem, normalized_expectation):
    return problem["scale"] * normalized_expectation + problem["ising"]["constant"]


def readout(problem, register, shots=4096, seed=42, sampling="state_snapshot"):
    validate_sampling(shots, seed, sampling)
    snapshot = ket.dump(register)
    amplitudes = snapshot.get()  # Triggers batch execution; simulator state access.
    probabilities = {int(k): float(abs(v) ** 2) for k, v in sorted(amplitudes.items())}
    mass = sum(probabilities.values())
    if abs(mass - 1.0) > 1e-4:
        raise RuntimeError(f"State normalization mismatch: {mass}")
    # Normalize floating-point drift, not substantive missing probability mass.
    probabilities = {k: v / mass for k, v in probabilities.items()}
    if sampling == "state_snapshot":
        # Public Ket snapshot API; this is classical sampling, not QPU measurement.
        counts = snapshot.sample(shots=shots, seed=seed)
        description = "Ket QuantumState.sample on a KBW state snapshot; classical seeded sampling"
        sampling_seed = seed
    else:
        counts = ket.sample(register, shots=shots).get()
        description = "Native KBW sample; this adapter exposes no native sampling seed"
        sampling_seed = None
    return probabilities, {int(k): int(v) for k, v in counts.items()}, {
        "shots": shots, "sampling_method": sampling, "sampling_description": description,
        "sampling_seed": sampling_seed, "state_norm_before_roundoff_normalization": mass,
        "exact_distribution_source": "ket.dump on CPU KBW simulator, normalized for <=1e-4 roundoff drift"}


def evaluate_distribution(problem, probabilities, counts):
    if not probabilities or abs(sum(probabilities.values()) - 1.0) > 1e-7:
        raise ValueError("Expected a normalized probability distribution")
    if any(p < 0 or not math.isfinite(p) for p in probabilities.values()):
        raise ValueError("Probabilities must be finite and nonnegative")
    if not counts or any(type(c) is not int or c < 0 for c in counts.values()):
        raise ValueError("Expected nonnegative integer sample counts")
    shots = sum(counts.values())
    if shots < 1:
        raise ValueError("Expected at least one sample")
    optimum = problem["reference"]["metrics"]["total_waiting_slots"]
    records = {}
    for index in set(probabilities) | set(counts):
        bits = bits_from_index(index, problem["n"])
        schedule = decode_berth_bits(problem["model"], bits)
        metrics = berth_metrics(problem["instance"], schedule)
        records[index] = {"bits": "".join(map(str, bits)), "count": counts.get(index, 0),
                          "probability": probabilities.get(index, 0.0),
                          "qubo_energy": qubo_energy(problem["model"], bits),
                          "feasible": metrics["feasible"], "waiting_slots": metrics["total_waiting_slots"],
                          "violations": metrics["violations"], "schedule": schedule}
    feasible = [r for r in records.values() if r["feasible"]]
    optimal = [r for r in feasible if r["waiting_slots"] == optimum]
    feasible_mass = sum(r["probability"] for r in feasible)
    feasible_count = sum(r["count"] for r in feasible)
    sampled_feasible = [r for r in feasible if r["count"] > 0]
    best = min(sampled_feasible, key=lambda r: (r["waiting_slots"], -r["count"], r["bits"])) if sampled_feasible else None
    mean_wait = sum(r["probability"] * r["waiting_slots"] for r in feasible) / feasible_mass if feasible_mass else None
    return {
        "reference_optimal_waiting_slots": optimum,
        "expected_full_qubo_energy": sum(r["probability"] * r["qubo_energy"] for r in records.values()),
        "exact_feasible_probability": feasible_mass,
        "exact_optimal_probability": sum(r["probability"] for r in optimal),
        "conditional_expected_feasible_waiting_slots": mean_wait,
        "sampled_feasible_rate": feasible_count / shots,
        "sampled_optimal_rate": sum(r["count"] for r in optimal) / shots,
        "best_sampled_feasible_waiting_slots": best["waiting_slots"] if best else None,
        "best_sampled_absolute_gap_slots": best["waiting_slots"] - optimum if best else None,
        "best_sampled_feasible_schedule": best["schedule"] if best else None,
        "top_sampled_states": sorted(records.values(), key=lambda r: (-r["count"], r["bits"]))[:10],
    }


def environment():
    return {"python": platform.python_version(), "platform": platform.platform(),
            "ket_lang": version("ket-lang"), "ket_components": ket.ket_version(),
            "numpy": version("numpy"), "scipy": version("scipy")}


def finish_report(problem, algorithm, configuration, probabilities, counts, sampling_info, log, elapsed, extra):
    return {"report_schema": "0.1", "algorithm": algorithm,
            "instance_id": problem["instance"].get("instance_id", "unnamed"),
            "quantum_circuit_executed": True, "execution_target": "KBW CPU state-vector simulator",
            "hardware_execution": False, "configuration": configuration, "environment": environment(),
            "qubits": problem["n"], "penalty": problem["model"]["penalty"],
            "hamiltonian_scale": problem["scale"], "hamiltonian_constant": problem["ising"]["constant"],
            "bit_order": "register[0] is the most significant (leftmost) bit",
            "elapsed_seconds": elapsed, "timing_scope": "problem preparation, circuit execution, algorithm loop and final readout; excludes imports and report validation",
            **sampling_info, **log.report(),
            "metrics": evaluate_distribution(problem, probabilities, counts),
            "counts": {format(k, f'0{problem["n"]}b'): v for k, v in sorted(counts.items())},
            "probabilities": {format(k, f'0{problem["n"]}b'): v for k, v in sorted(probabilities.items())},
            **extra}
