# SPDX-License-Identifier: Apache-2.0
"""QAOA with explicit Ket gates and exact KBW expectation objectives."""

from time import perf_counter

import ket
import numpy as np
from scipy.optimize import minimize

from .ket_backend import (
    apply_cost, apply_mixer, cost_observable, create_register, finish_report,
    full_energy, positive_integer, prepare_problem, readout, validate_sampling,
)


def qaoa_state(problem, parameters, simulator="sparse", execution="batch"):
    parameters = np.asarray(parameters, dtype=float)
    if parameters.ndim != 1 or len(parameters) < 2 or len(parameters) % 2 or not np.all(np.isfinite(parameters)):
        raise ValueError("Parameters must contain finite [gammas..., betas...] of equal lengths")
    p = len(parameters) // 2
    process, register, log = create_register(problem, execution=execution, simulator=simulator)
    for gamma, beta in zip(parameters[:p], parameters[p:]):
        apply_cost(problem, register, float(gamma), log)
        apply_mixer(register, float(beta), log)
    return process, register, log


def run_qaoa(instance, p=2, max_evaluations=80, restarts=2, seed=42,
             shots=4096, sampling="state_snapshot", simulator="sparse", penalty=None):
    """Optimize exact simulated energy; final counts do not drive optimization.

    COBYLA budgets are per restart. A budget stop is reported honestly and does
    not certify convergence. The best evaluated parameters are always retained.
    """
    positive_integer(p, "p", maximum=20)
    positive_integer(max_evaluations, "max_evaluations")
    positive_integer(restarts, "restarts", maximum=20)
    if max_evaluations < 2 * p + 2:
        raise ValueError("COBYLA needs at least 2*p+2 evaluations")
    validate_sampling(shots, seed, sampling)
    started = perf_counter()
    problem = prepare_problem(instance, penalty)
    rng = np.random.default_rng(seed)
    trace, restart_reports = [], []
    best = {"normalized_energy": float("inf"), "parameters": None}

    def objective(theta):
        process, register, _ = qaoa_state(problem, theta, simulator)
        value = float(ket.exp_value(cost_observable(problem, register)).get())
        trace.append({"evaluation": len(trace) + 1, "full_qubo_energy": full_energy(problem, value)})
        if value < best["normalized_energy"]:
            best.update(normalized_energy=value, parameters=np.asarray(theta).copy())
        return value

    for restart in range(restarts):
        initial = (np.concatenate([np.linspace(0.1, 0.3, p), np.full(p, -0.3)])
                   if restart == 0 else rng.uniform(-np.pi, np.pi, size=2 * p))
        result = minimize(objective, initial, method="COBYLA",
                          options={"maxiter": max_evaluations, "rhobeg": 0.5, "tol": 1e-5})
        restart_reports.append({"restart": restart, "success": bool(result.success),
                                "message": str(result.message), "evaluations": int(result.nfev),
                                "returned_normalized_energy": float(result.fun)})
    # dump() is a live-only diagnostic in the pinned Ket API. Rebuild the final
    # circuit in live mode; optimizer evaluations above remain batch executions.
    process, register, log = qaoa_state(problem, best["parameters"], simulator, execution="live")
    final_expectation = float(ket.exp_value(cost_observable(problem, register)).get())
    probabilities, counts, info = readout(problem, register, shots, seed, sampling)
    elapsed = perf_counter() - started
    return finish_report(problem, "QAOA", {
        "p": p, "max_evaluations_per_restart": max_evaluations, "restarts": restarts,
        "initialization_seed": seed, "simulator": simulator, "optimization_execution": "batch",
        "final_readout_execution": "live",
        "initialization_policy": "First restart: gamma linspace(0.1,0.3,p), beta=-0.3; remaining restarts: seeded uniform(-pi,pi)",
        "optimizer": "SciPy COBYLA", "objective_estimator": "exact KBW state-vector expectation",
        "mixer": "sum X", "parameter_order": "gammas first, then betas"},
        probabilities, counts, info, log, elapsed, {
            "parameters": best["parameters"].tolist(), "optimization_trace": trace,
            "restart_reports": restart_reports,
            "cost_expectation_queries": len(trace) + 1, "feedback_expectation_queries": 0,
            "circuit_preparations": len(trace) + 1,
            "final_full_energy_from_observable": full_energy(problem, final_expectation),
            "solution_status": "HEURISTIC; no global optimality certificate from QAOA"})
