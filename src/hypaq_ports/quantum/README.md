# Quantum adapter

| Module | Responsibility |
| --- | --- |
| `ket_backend.py` | Ising normalization, explicit gates, observables, MSB decoding, simulator readout, metrics. |
| `qaoa.py` | QAOA circuit and exact-expectation COBYLA search. |
| `falqon.py` | First-order live FALQON feedback loop. |

`run_qaoa(instance)` and `run_falqon(instance)` accept the existing berth-instance
dictionary and return JSON-serializable reports. They import the classical
formulation and validator from `hypaq_ports.reference`; no copy replaces them.

CPU KBW `sparse` is the default; `dense` is also accepted. Inputs are limited to
12 encoded qubits before enumeration or circuit construction. This is a safety
bound for teaching experiments, not a scalability claim. Default BAP uses eight.

The cost circuit uses RZ(2*gamma*h) for each Z term and
CNOT–RZ(2*gamma*J)–CNOT for each ZZ term. The mixer uses RX(2*beta).
QAOA parameters are ordered `[gamma_1,...,gamma_p,beta_1,...,beta_p]`.
The first restart uses a fixed small-angle schedule, while later restarts use
seeded random initialization. Optimizer success/budget-stop messages are retained.

FALQON applies cost(dt) then mixer(beta_k*dt), starting from beta_0=0. Its next
control is the expectation of `-i[sum X,H_tilde]`, evaluated on the updated state.
This API does not implement shot-noisy feedback, constrained mixers, adaptive
penalties, warm starts from the classical optimum, or hardware execution.

The existing Apache-2.0 license applies to these original adapter files. Ket and
other dependencies retain their own licenses. QAOA and FALQON are published
algorithms; the adapter and port formulation are not claims to their invention.
