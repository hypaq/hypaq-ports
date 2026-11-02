# HYPAQ Ports — Development and implementation guide

The public alpha contains three executable classical notebooks, exact
enumeration references, a berth QUBO/Ising formulation, and three quantum BAP
notebooks running QAOA and FALQON through Ket on the KBW CPU simulator.
Quantum notebooks include experiment plots. CP-SAT, AI assistance, operational
schedule timelines, hardware execution, and terminal integration remain planned.

The classical solver is **exhaustive enumeration**, not OR-Tools CP-SAT.
Quantum execution is currently limited to the supplied tiny BAP. Crane allocation
and disruption/replanning remain classical examples. See the
[quantum methodology](quantum/README.md) and [validation record](quantum/VALIDATION.md).

## Implementation status

| Component | Current status |
| --- | --- |
| Classical BAP, crane allocation, and arrival-delay replanning | Implemented with exact exhaustive enumeration and independent metrics/validators. |
| BAP QUBO and Ising mapping | Implemented; full constant offset retained in energy comparisons. |
| BAP QAOA and FALQON | Implemented with Ket/KBW on the supplied eight-qubit instance. |
| Quantum plots, experiment configuration, and JSON/CSV reports | Available in the quantum notebooks and results directory. |
| OR-Tools CP-SAT | Planned; not an implemented backend or runtime dependency of this alpha. |
| Quantum crane allocation and quantum replanning | Planned; the corresponding current exercises are classical. |
| AI assistant, operational schedule timelines, and live terminal integration | Planned. |
| Quantum hardware execution and other backends | Planned; current quantum experiments run on the KBW CPU simulator. |

Start with the [main README](../README.md), the [classical guide](../START_HERE.md),
or the [quantum guide](../QUANTUM_START_HERE.md).

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
assignments of the supplied berth instance. These classical mapping checks do
not execute circuits; separate quantum integration tests do execute Ket/KBW
circuits and check them against independent NumPy calculations.

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

All commands below must be run from the cloned repository root, not from `docs/`.

### Classical path

From the repository root, Python 3.10+ is sufficient for the classical reference code:

```bash
python -m unittest discover -s tests -p "test_reference.py" -v
python results/generate_reference.py
```

The reference generator and notebooks configure their import path automatically.
Open classical notebooks in a Jupyter environment; their code cells require only
the standard library. See the [classical notebook guide](../notebooks/README.md).

### Quantum path

For quantum BAP experiments, use Python 3.11+ for the pinned dependencies
(recorded environment: Python 3.12.14, Linux x86_64):

```bash
python -m pip install -r requirements-quantum.txt
python -m unittest discover -s tests -v
python results/quantum/run_berth_comparison.py
```

Full discovery includes ten classical tests and ten quantum integration tests
and therefore requires Ket and NumPy. For a classical-only environment, use
the filtered `test_reference.py` command above.
Jupyter is installed separately if needed. Local and Colab setup instructions
are in the [quantum notebook guide](../notebooks/quantum/README.md); external
Jupyter/Colab execution was not validated in the recorded build environment.

## Quantum execution and result interpretation

The default BAP encodes two vessels, two berths, and two slots with eight qubits.
The same operational constraints and classical reference are shared by QAOA and
FALQON. Both use a transverse-X mixer; a feasibility-preserving mixer is not
implemented. Decoded solutions are checked against the original constraints.

QAOA optimization and FALQON feedback use exact simulated state-vector
expectations. The default final counts use seeded classical sampling from a KBW
state snapshot. Optional native KBW sampling is supported, but neither path
executes on quantum hardware. Exact simulator probabilities are diagnostics,
not hardware measurements.

Published reports distinguish operational waiting time, penalized QUBO energy,
feasibility/optimality probabilities, empirical sample frequencies, logical gate
counts/depth, and environment-specific timing. The quantum methods found samples
matching the zero-wait classical optimum in the recorded run, while their full
state distributions also contain infeasible assignments.

The algorithms have different resource budgets and are evaluated on one tiny
synthetic instance. This does not establish quantum speedup, a general algorithm
ranking, global heuristic optimality, or industrial readiness. FALQON's finite-step
energy trace is monitored rather than assumed to be strictly monotonic.

See the [quantum results guide](../results/quantum/README.md),
[experiment configuration](../results/quantum/berth_experiment.json),
[CSV summary](../results/quantum/berth_comparison_summary.csv),
and [validation record](quantum/VALIDATION.md).

## Roadmap and acceptance criteria

| Stage | Deliverable | Acceptance criterion |
| --- | --- | --- |
| Available: classical exercises | Three notebooks, exact references, BAP QUBO/Ising, inputs and outputs. | Ten classical behavioral checks; explicit feasibility and energy equivalence tests. |
| Available: Ket/KBW | Eight-qubit BAP QAOA and FALQON, comparison, plots, and reports. | Ten quantum integration checks recorded; versions, angles, sampling, resources, and limitations documented. |
| Next: CP-SAT | A solver adapter using the same inputs and validator. | Match exact objectives on tiny feasible instances; distinguish feasible/optimal/infeasible statuses. |
| Later: operational visualizations | Berth and crane timelines and scenario comparison. | Display actual computed schedules and explicit units. |
| Later: AI assistance | Structured scenario updates and grounded explanations. | Validate inputs before execution and cite calculated outputs in explanations. |

Keep original synthetic data separate from partner data. Document provenance,
units, assumptions, and third-party licensing before adding materials. Existing
research repositories keep their own licenses; this package does not copy their
code. Open an issue before proposing major scope changes.

References: [Ket](https://quantumket.org/),
[OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)
(reference for a planned adapter, not an implemented backend).
