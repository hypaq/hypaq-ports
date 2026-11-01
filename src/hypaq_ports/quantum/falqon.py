# SPDX-License-Identifier: Apache-2.0
"""First-order FALQON with a live Ket/KBW state and explicit feedback law."""

from time import perf_counter

import ket

from .ket_backend import (
    apply_cost, apply_mixer, cost_observable, create_register, feedback_observable,
    finite_number, finish_report, full_energy, positive_integer,
    prepare_problem, readout, validate_sampling,
)


def falqon_state(problem, layers=64, delta_t=0.05, simulator="sparse"):
    """beta_0=0; layer k applies cost(dt), mixer(beta_k*dt).

    beta_(k+1) = -<i[sum X,H_tilde]> in the updated state. Observable queries
    here are exact simulator queries, not destructive on-hardware measurements.
    """
    positive_integer(layers, "layers", maximum=1000)
    delta_t = finite_number(delta_t, "delta_t")
    if delta_t <= 0:
        raise ValueError("delta_t must be positive")
    process, register, log = create_register(problem, execution="live", simulator=simulator)
    cost, feedback = cost_observable(problem, register), feedback_observable(problem, register)
    energy = float(ket.exp_value(cost).get())
    trace = [{"layer": 0, "full_qubo_energy": full_energy(problem, energy),
              "beta_applied": None, "beta_next": 0.0}]
    beta = 0.0
    for layer in range(1, layers + 1):
        apply_cost(problem, register, delta_t, log)
        apply_mixer(register, beta * delta_t, log)
        new_energy = float(ket.exp_value(cost).get())
        beta_next = float(ket.exp_value(feedback).get())
        trace.append({"layer": layer, "full_qubo_energy": full_energy(problem, new_energy),
                      "beta_applied": beta, "beta_next": beta_next})
        beta, energy = beta_next, new_energy
    return process, register, log, trace


def run_falqon(instance, layers=64, delta_t=0.05, seed=42, shots=4096,
               sampling="state_snapshot", simulator="sparse", penalty=None):
    validate_sampling(shots, seed, sampling)
    started = perf_counter()
    problem = prepare_problem(instance, penalty)
    process, register, log, trace = falqon_state(problem, layers, delta_t, simulator)
    probabilities, counts, info = readout(problem, register, shots, seed, sampling)
    elapsed = perf_counter() - started
    increases = sum(b["full_qubo_energy"] > a["full_qubo_energy"] + 1e-9 for a, b in zip(trace, trace[1:]))
    return finish_report(problem, "FALQON", {
        "layers": layers, "delta_t": delta_t, "beta_initial": 0.0,
        "simulator": simulator, "execution": "live", "mixer": "sum X",
        "feedback": "beta_next = -expectation(i[H_m,H_tilde])",
        "feedback_estimator": "exact KBW state-vector expectation",
        "splitting": "cost then mixer; first order; fixed delta_t"},
        probabilities, counts, info, log, elapsed, {
            "feedback_trace": trace, "energy_increases_observed": increases,
            "cost_expectation_queries": layers + 1, "feedback_expectation_queries": layers,
            "circuit_preparations": 1,
            "final_full_energy_from_observable": trace[-1]["full_qubo_energy"],
            "solution_status": "HEURISTIC; no global optimality or finite-step monotonicity guarantee"})
