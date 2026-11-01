# Development guide

This starter contains executable **classical references**, a berth QUBO/Ising
formulation, and three guided notebooks. It is an initial educational asset.
CP-SAT, Ket/KBW execution, QAOA, FALQON, AI assistance, charts, and terminal
integration are not implemented in this package.

## Model conventions

Berth services last exactly one slot. Every vessel must be assigned once, no
earlier than arrival, to a compatible and available berth. Overlaps are forbidden.
The objective is total waiting time in slots. The two-slot instance contains eight
binary variables in its full vessel/berth/slot encoding.

The QUBO is upper triangular (no automatic doubling of off-diagonal terms):

`E(x) = offset + sum(Q[i,j] * x[i] * x[j], i <= j)`.

It adds one-hot penalties `A*(sum(x_v)-1)^2`, `A*x` for forbidden choices,
and `A*x_i*x_j` for different vessels occupying the same berth/slot.
Waiting coefficients are nonnegative. The default A is larger than an upper
bound on any feasible waiting cost; if a feasible assignment exists, no
infeasible assignment can be a ground state. Infeasible instances still require
independent feasibility checks: low energy alone is not a feasibility certificate.

The Ising mapping uses `x=(1-z)/2`, where `z` is +1 or -1. The conversion preserves
the full additive constant. Both transformations are checked over all 256 binary
assignments of the supplied berth instance. This does not execute a circuit.

Crane allocation is independent of the berth schedule. Every vessel is available
in every period. Cranes may be idle and can serve at most one vessel per period.
Productivity is fixed. The exact objective is lexicographic: minimize unmet work,
then minimize active crane-slots. Oversupply is allowed and served demand is
clipped. Interference, travel and non-crossing are not modeled.

Replanning is offline, before any service has started. It supports a vessel
arrival delay; no assignments are frozen. Stability counts the number of vessels
whose `(berth, slot)` pair differs from the original plan. The stability objective
is `waiting_slots + change_weight * changed_vessels`. The two objective terms
must be reported separately. Berth outages are supported in BAP data through
`unavailable`, but no outage-specific notebook scenario is included yet.

## Execution

From the repository root, Python 3.10+ is sufficient for the reference code:

```bash
python -m unittest discover -s tests -v
PYTHONPATH=src python results/generate_reference.py
```

On Windows PowerShell, use `$env:PYTHONPATH = 'src'` before running the generator.
The notebooks add `src/` to their import path automatically. Open them with your
preferred Jupyter environment. They contain only standard-library code cells.
See `notebooks/README.md` for Google Colab setup.

## Roadmap and acceptance criteria

| Stage | Deliverable | Acceptance criterion |
| --- | --- | --- |
| Initial scaffold (this package) | Three classical exercises and BAP QUBO/Ising. | References regenerate and all checks pass. |
| Next: CP-SAT | A solver adapter using the same inputs and validator. | Match exact objectives on tiny feasible instances; distinguish feasible/optimal/infeasible statuses. |
| Next: Ket/KBW | A tested Hamiltonian and small QAOA experiment. | Document versions, angle/bit conventions, layers, shots, seeds, energies and sample feasibility. |
| Later: visualizations | Berth and crane timelines and scenario comparison. | Display actual computed schedules and explicit units. |
| Later: AI assistance | Structured scenario updates and grounded explanations. | Validate inputs before execution and cite calculated outputs in explanations. |

Keep original synthetic data separate from partner data. Document provenance,
units, assumptions, and third-party licensing before adding materials. Existing
research repositories keep their own licenses; this package does not copy their
code. Open an issue before proposing major scope changes.

References: [Ket](https://quantumket.org/),
[OR-Tools](https://developers.google.com/optimization/cp/cp_solver).
