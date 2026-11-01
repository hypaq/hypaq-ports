# SPDX-License-Identifier: Apache-2.0
"""Quantum integration checks with an independent NumPy state-vector oracle.

Ket is required: missing dependencies fail explicitly instead of silently
substituting classical execution. Run the classical tests separately if needed.
"""

import itertools
import sys
import unittest
from pathlib import Path

import ket
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hypaq_ports.reference import load_json, qubo_energy
from hypaq_ports.quantum.ket_backend import (
    bits_from_index, cost_observable, create_register, feedback_observable,
    full_energy, prepare_problem, readout,
)
from hypaq_ports.quantum.qaoa import qaoa_state, run_qaoa
from hypaq_ports.quantum.falqon import falqon_state, run_falqon


def numpy_diagonal(problem):
    return np.array([(qubo_energy(problem["model"], bits_from_index(k, problem["n"]))
                      - problem["ising"]["constant"]) / problem["scale"]
                     for k in range(2 ** problem["n"])])


def numpy_mixer(state, angle, n):
    # Full-statevector algebra, independent of Ket's gate implementation.
    indices = np.arange(len(state))
    for i in range(n):
        state = np.cos(angle) * state - 1j * np.sin(angle) * state[indices ^ (1 << (n - 1 - i))]
    return state


def numpy_mixer_hamiltonian(state, n):
    indices = np.arange(len(state))
    return sum(state[indices ^ (1 << (n - 1 - i))] for i in range(n))


def numpy_beta(state, diagonal, n):
    a = np.vdot(state, numpy_mixer_hamiltonian(diagonal * state, n))
    b = np.vdot(state, diagonal * numpy_mixer_hamiltonian(state, n))
    return float(np.real(-1j * (a - b)))


def ket_vector(register, n):
    amps = ket.dump(register).get()
    state = np.array([amps.get(i, 0j) for i in range(2 ** n)], dtype=complex)
    return state / np.linalg.norm(state)


class QuantumChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance = load_json(ROOT / "data/synthetic/berth_tiny_v1.json")
        cls.problem = prepare_problem(cls.instance)

    def test_ket_register_order_is_most_significant_first(self):
        for wire in range(3):
            process = ket.Process(num_qubits=3, execution="live", simulator="sparse")
            register = process.alloc(3)
            ket.X(register[wire])
            amps = ket.dump(register).get()
            self.assertEqual(list(amps), [1 << (2 - wire)])

    def test_ket_hamiltonian_matches_qubo_on_every_basis_state(self):
        for bits in itertools.product((0, 1), repeat=self.problem["n"]):
            process = ket.Process(num_qubits=self.problem["n"], execution="live", simulator="sparse")
            register = process.alloc(self.problem["n"])
            for i, bit in enumerate(bits):
                if bit:
                    ket.X(register[i])
            actual = full_energy(self.problem, ket.exp_value(cost_observable(self.problem, register)).get())
            self.assertAlmostEqual(actual, qubo_energy(self.problem["model"], bits), delta=2e-5)

    def test_qaoa_gate_signs_and_angles_match_numpy(self):
        parameters = [0.13, -0.27, -0.21, 0.19]
        process, register, _ = qaoa_state(self.problem, parameters, execution="live")
        actual = ket_vector(register, self.problem["n"])
        expected = np.ones(2 ** self.problem["n"], dtype=complex) / np.sqrt(2 ** self.problem["n"])
        diagonal = numpy_diagonal(self.problem)
        for gamma, beta in zip(parameters[:2], parameters[2:]):
            expected *= np.exp(-1j * gamma * diagonal)
            expected = numpy_mixer(expected, beta, self.problem["n"])
        np.testing.assert_allclose(actual, expected, atol=2e-5, rtol=0)

    def test_feedback_sign_matches_independent_commutator(self):
        process, register, _ = qaoa_state(self.problem, [0.13, -0.21], execution="live")
        state = ket_vector(register, self.problem["n"])
        expected = numpy_beta(state, numpy_diagonal(self.problem), self.problem["n"])
        actual = ket.exp_value(feedback_observable(self.problem, register)).get()
        self.assertAlmostEqual(actual, expected, delta=2e-4)

    def test_falqon_sequence_matches_numpy_feedback(self):
        layers, dt = 4, 0.025
        process, register, _, trace = falqon_state(self.problem, layers, dt)
        state = np.ones(2 ** self.problem["n"], dtype=complex) / np.sqrt(2 ** self.problem["n"])
        diagonal, beta = numpy_diagonal(self.problem), 0.0
        for layer in range(1, layers + 1):
            state *= np.exp(-1j * dt * diagonal)
            state = numpy_mixer(state, beta * dt, self.problem["n"])
            beta = numpy_beta(state, diagonal, self.problem["n"])
            self.assertAlmostEqual(trace[layer]["beta_next"], beta, delta=3e-4)
        np.testing.assert_allclose(ket_vector(register, self.problem["n"]), state, atol=3e-5, rtol=0)

    def test_seeded_snapshot_readout_is_repeatable(self):
        process, register, _ = qaoa_state(self.problem, [0.2, -0.3], execution="live")
        a = readout(self.problem, register, shots=256, seed=42)
        b = readout(self.problem, register, shots=256, seed=42)
        self.assertEqual(a[1], b[1])
        self.assertEqual(sum(a[1].values()), 256)
        self.assertAlmostEqual(sum(a[0].values()), 1.0)

    def test_native_kbw_sampling_is_available(self):
        process, register, _ = qaoa_state(self.problem, [0.2, -0.3], execution="live")
        _, counts, info = readout(self.problem, register, shots=128, sampling="kbw_native")
        self.assertEqual(sum(counts.values()), 128)
        self.assertIsNone(info["sampling_seed"])

    def test_qaoa_report_matches_state_distribution(self):
        result = run_qaoa(self.instance, p=1, max_evaluations=12, restarts=1, shots=256)
        self.assertTrue(result["quantum_circuit_executed"])
        self.assertFalse(result["hardware_execution"])
        self.assertEqual(sum(result["counts"].values()), 256)
        self.assertGreaterEqual(result["metrics"]["exact_feasible_probability"], 0)
        self.assertLessEqual(result["metrics"]["exact_feasible_probability"], 1)
        self.assertAlmostEqual(result["metrics"]["expected_full_qubo_energy"],
                               result["final_full_energy_from_observable"], delta=2e-3)

    def test_falqon_report_matches_state_distribution(self):
        result = run_falqon(self.instance, layers=8, shots=256)
        self.assertEqual(len(result["feedback_trace"]), 9)
        self.assertEqual(result["cost_expectation_queries"], 9)
        self.assertEqual(result["feedback_expectation_queries"], 8)
        self.assertAlmostEqual(result["metrics"]["expected_full_qubo_energy"],
                               result["final_full_energy_from_observable"], delta=2e-3)

    def test_invalid_budgets_and_steps_fail_explicitly(self):
        for options in [{"p": 0}, {"max_evaluations": 1}, {"seed": -1}, {"sampling": "hardware"}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                run_qaoa(self.instance, **options)
        with self.assertRaises(ValueError):
            run_falqon(self.instance, delta_t=-1)


if __name__ == "__main__":
    unittest.main()
