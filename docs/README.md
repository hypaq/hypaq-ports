# HYPAQ Ports — Development and implementation guide

This is the general guide to the repository's models, implemented methods,
execution paths, validation, and planned extensions.

The repository contains three original classical notebooks, exact enumeration
references, a berth QUBO/Ising formulation, and three original quantum BAP
notebooks running QAOA and FALQON through Ket on the KBW CPU simulator.
An additional [BAP CP-SAT scenario](../scenarios/bap_cpsat/README.md) provides
an OR-Tools demo, a seventh notebook, separate tests and reports, and live
comparisons with enumeration and the existing quantum methods.

The original classical exercises use **exhaustive enumeration**. The additional
CP-SAT adapter implements the same base one-slot BAP using direct constraints,
without calling enumeration or the quantum backend. Crane allocation and
stability-aware disruption/replanning remain enumeration-based examples.
AI assistance, operational schedule timelines, quantum hardware execution,
and terminal integration remain planned. See the
[quantum methodology](quantum/README.md) and [validation record](quantum/VALIDATION.md).

The CP-SAT additions are available on `main`; the original `v0.1.0-alpha.1`
source snapshot does not include them. Release tags identify specific source
snapshots. Select the intended tag when reproducing a release; updating `main`
does not change an existing tag.

## Implementation status

| Component | Current status |
| --- | --- |
| Classical BAP, crane allocation, and arrival-delay replanning | Implemented with exact exhaustive enumeration and independent metrics/validators. |
| BAP QUBO and Ising mapping | Implemented; full constant offset retained in energy comparisons. |
| BAP QAOA and FALQON | Implemented with Ket/KBW; the original notebooks use the eight-qubit input. The additional scenario also compares a six-qubit input. |
| Quantum plots, experiment configuration, and JSON/CSV reports | Original quantum notebooks provide plots; original and scenario results directories provide separate reports. |
| OR-Tools CP-SAT | Implemented for the base one-slot BAP; optional dependencies, demo, notebook, tests, and comparisons are in the [additional scenario](../scenarios/bap_cpsat/README.md). |
| Live BAP comparisons | Enumeration, CP-SAT, QAOA, and FALQON run on shared inputs, with independent operational validation and separate JSON/CSV reports. |
| Quantum crane allocation and quantum replanning | Planned; the corresponding current exercises are classical. |
| AI assistant, operational schedule timelines, and live terminal integration | Planned. |
| Quantum hardware execution and other backends | Planned; current quantum experiments run on the KBW CPU simulator. |

Start with the [main README](../README.md), the [classical guide](../START_HERE.md),
the [CP-SAT scenario guide](../scenarios/bap_cpsat/README.md), or the
[quantum guide](../QUANTUM_START_HERE.md). The detailed
[CP-SAT adapter guide](classical/README.md) documents its API and output contract.

## Model conventions

Berth services last exactly one slot. Every vessel must be assigned once, no
earlier than arrival, to a compatible and available berth. Overlaps are forbidden.
The objective is total waiting time in slots. The two-slot instance contains eight
binary variables in its full vessel/berth/slot encoding.

The additional [positive-waiting instance](../scenarios/bap_cpsat/data/berth_waiting_v1.json)
has two vessels arriving at slot 0, one berth, and three slots. Its full encoding
uses six binary variables/qubits, and its optimum is one waiting slot.
CP-SAT creates variables only for admissible assignments; its variable count
need not equal the full quantum encoding. Both represent the same supported
operational constraints and waiting-time objective.

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

### Original classical exercises — standard library

From the repository root, Python 3.10+ is sufficient for the classical reference code:

```bash
python -m unittest discover -s tests -p "test_reference.py" -v
python results/generate_reference.py
```

The reference generator and notebooks configure their import path automatically.
Open classical notebooks in a Jupyter environment; their code cells require only
the standard library. See the [classical notebook guide](../notebooks/README.md).

### Additional BAP CP-SAT scenario — optional OR-Tools

Use Python 3.11+ with the scenario's pinned dependencies, preferably in a
separate virtual environment. From the repository root:

```bash
python -m pip install -r scenarios/bap_cpsat/requirements.txt
python scenarios/bap_cpsat/run_demo.py
python scenarios/bap_cpsat/compare.py --output-prefix scenarios/bap_cpsat/results/my_classical_run
python -m unittest discover -s scenarios/bap_cpsat/tests -v
```

These commands run CP-SAT alone, compare it with enumeration, and execute
the 22 additional scenario tests. Ket is not required for this path.
Reports use the supplied prefix within the scenario directory; the CLI rejects
output prefixes outside that directory. The original report files are preserved.
See the [scenario guide](../scenarios/bap_cpsat/README.md) for environment
activation, platform notes, the additional notebook, and API usage.

### Original quantum experiments — Ket/KBW

For quantum BAP experiments, use Python 3.11+ for the pinned dependencies
(recorded environment: Python 3.12.14, Linux x86_64):

```bash
python -m pip install -r requirements-quantum.txt
python -m unittest discover -s tests -v
python results/quantum/run_berth_comparison.py
```

Discovery in `tests/` includes ten classical tests and ten quantum integration
tests and therefore requires Ket and NumPy. It does not discover the separate
CP-SAT scenario tests. For a standard-library-only environment, use the filtered
`test_reference.py` command above.
Jupyter is installed separately if needed. Local and Colab setup instructions
are in the [quantum notebook guide](../notebooks/quantum/README.md); external
Jupyter/Colab execution was not validated in the recorded build environment.

### Live four-method BAP comparison

Install both optional dependency sets in the chosen environment, then run the
additional comparator:

```bash
python -m pip install -r scenarios/bap_cpsat/requirements.txt -r requirements-quantum.txt
python scenarios/bap_cpsat/compare.py --include-quantum --output-prefix scenarios/bap_cpsat/results/my_four_method_run
```

For the positive-waiting input:

```bash
python scenarios/bap_cpsat/compare.py --include-quantum --instance scenarios/bap_cpsat/data/berth_waiting_v1.json --output-prefix scenarios/bap_cpsat/results/my_waiting_run
```

The comparator executes all four methods on the same input rather than
combining archived quantum results with new classical timings. It compares
operational waiting slots and independent feasibility checks. CP-SAT statuses
distinguish `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNKNOWN`, and `MODEL_INVALID`.
Quantum results remain `HEURISTIC`, even when a sampled solution matches the
known optimum. Detailed output/status contracts are in the
[scenario guide](../scenarios/bap_cpsat/README.md).

### Run both test suites

After installing both dependency sets above, run:

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s scenarios/bap_cpsat/tests -v
```

The expected total is **42 tests: 20 original plus 22 additional**. A complete
run must have no skips. The CP-SAT tests include parity with enumeration over
128 seeded small instances. Controlled status overrides exercise reporting
branches; they are not evidence of naturally occurring solver timeouts.
See the original [quantum validation record](quantum/VALIDATION.md) and the
[additional scenario validation record](../scenarios/bap_cpsat/VALIDATION.md).
These local checks do not replace an independent external reproduction.

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

The original quantum notebooks and reports describe the eight-qubit input.
The additional scenario records live four-method comparisons on that input and
the six-qubit positive-waiting input. Both enumeration and CP-SAT proved an
optimum of zero waiting slots on the original input and one waiting slot on
the additional input. QAOA and FALQON produced best feasible samples matching
those values in the recorded runs.

The algorithms have different resource budgets and timing boundaries. These
small synthetic experiments do not establish quantum speedup, a general
algorithm ranking, global heuristic optimality, or industrial readiness.
FALQON's finite-step energy trace is monitored rather than assumed to be
strictly monotonic. Neither the adapter nor the comparisons use quantum hardware.

See the [quantum results guide](../results/quantum/README.md),
[experiment configuration](../results/quantum/berth_experiment.json),
[CSV summary](../results/quantum/berth_comparison_summary.csv),
and [validation record](quantum/VALIDATION.md).

The additional [comparison reports](../scenarios/bap_cpsat/results/) and
[CP-SAT notebook](../scenarios/bap_cpsat/01_bap_cpsat.ipynb) are separate from
the original quantum assets. The new notebook's Python cells were validated
in-process, not through a full Jupyter/Colab kernel session.

## Roadmap and acceptance criteria

| Stage | Deliverable | Acceptance criterion |
| --- | --- | --- |
| Available: classical exercises | Three notebooks, exact references, BAP QUBO/Ising, inputs and outputs. | Ten classical behavioral checks; explicit feasibility and energy equivalence tests. |
| Available: Ket/KBW | Eight-qubit BAP QAOA and FALQON, comparison, plots, and reports. | Ten quantum integration checks recorded; versions, angles, sampling, resources, and limitations documented. |
| Available: CP-SAT scenario | Optional base-BAP adapter, demo, notebook, additional input, live comparisons, and separate reports. | 22 scenario tests; 128 seeded parity cases; operational validation and explicit solver statuses. |
| Next: broader comparisons | More instance families and repeated experiments with explicit resource budgets. | Record feasibility, objective gaps, sampling probabilities, seeds, timing scopes, and resources; seek independent reproduction. |
| Later: operational visualizations | Berth and crane timelines and scenario comparison. | Display actual computed schedules and explicit units. |
| Later: AI assistance | Structured scenario updates and grounded explanations. | Validate inputs before execution and cite calculated outputs in explanations. |

Keep original synthetic data separate from partner data. Document provenance,
units, assumptions, and third-party licensing before adding materials. Existing
research repositories keep their own licenses; this package does not copy their
code. Open an issue before proposing major scope changes.

References: [Ket](https://quantumket.org/),
[OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)
(implemented in the optional base-BAP scenario), and the
[CP-SAT scenario guide](../scenarios/bap_cpsat/README.md).
