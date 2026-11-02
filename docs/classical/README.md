# BAP — OR-Tools CP-SAT adapter

This optional adapter solves the **existing discrete, one-slot Berth Allocation
Problem** using OR-Tools CP-SAT. It accepts the same base instance dictionary as
`solve_berth_exact(instance)` and returns the same operational schedule format.

The adapter is in [`src/hypaq_ports/classical/cpsat.py`](../../src/hypaq_ports/classical/cpsat.py).
It reuses the shared schema checker and independent operational validator.
It does not call enumeration or the quantum backend and does not use QUBO penalties.
The original enumeration and Ket implementations remain available.

## Install

Use Python 3.11+ for the pinned dependency set; tested on Python 3.12.14,
Linux x86_64. From the repository root, preferably in a virtual environment:

```bash
python -m pip install -r requirements-classical.txt
```

The adapter imports OR-Tools only when called. Original standard-library
references remain usable without it. Dependency errors are explicit; the adapter
never silently falls back to exhaustive enumeration.

## Python API

From a script or notebook with `src/` on the import path:

```python
from hypaq_ports.classical import solve_berth_cpsat
from hypaq_ports.reference import load_json

instance = load_json("data/synthetic/berth_tiny_v1.json")
result = solve_berth_cpsat(
    instance,
    time_limit_seconds=10.0,
    num_workers=1,
    random_seed=42,
)
print(result["status"])
if result["has_solution"]:
    print(result["schedule"])
    print(result["metrics"]["total_waiting_slots"])
print(result["elapsed_seconds"])
```

`results/run_berth_solver_comparison.py` configures the import path automatically.
Existing notebooks use a root-detection setup cell. For an interactive Python
session launched from the repository root, add `src/` to `sys.path` first.

## Supported model

- Each vessel has an integer, nonnegative arrival slot and service duration **1**.
- Each vessel is assigned to exactly one listed slot and compatible berth.
- Service cannot precede arrival or use a listed unavailable berth/slot.
- At most one vessel occupies each berth/slot.
- The objective is `sum(service_slot - arrival_slot)` across vessels.
- Slots may be unsorted or nonconsecutive; differences use their integer values.
- No input data is mutated. Metadata such as slot duration is preserved in input
  but does not change the objective's unit of waiting slots.

Only admissible assignment choices receive Boolean variables. An empty choice
set makes the model infeasible. This differs from the full binary encoding of
the quantum formulation but represents the same supported operational problem.

This adapter does not implement crane allocation, varying service durations,
replanning stability costs, frozen assignments, navigation channels, tides, or
live terminal integration. It is not a general CP-SAT model converter.

## Status and output contract

| Status | Incumbent schedule? | Interpretation |
| --- | --- | --- |
| `OPTIMAL` | Yes | Feasible schedule and optimality proved by CP-SAT. |
| `FEASIBLE` | Yes | Feasible incumbent, without proof of optimality. |
| `INFEASIBLE` | No | CP-SAT proved this model has no feasible schedule. |
| `UNKNOWN` | No | No incumbent available; do not infer infeasibility. |
| `MODEL_INVALID` | No | The model was rejected; investigate the model/solver configuration. |

`score` equals total waiting slots. `metrics` comes from `berth_metrics`, and
every returned incumbent is independently checked before it is exposed.
For statuses without an incumbent, `schedule=[]` and `metrics`, `score`,
`best_objective_bound`, and `absolute_gap` are `None`.

`proven_optimal` follows the native status. It is not changed to true merely
because an incumbent matches an externally known optimum or has zero waiting.
`best_objective_bound` is the solver's lower bound when an incumbent exists;
`absolute_gap` is its nonnegative difference from `score`. Invalid input/options
raise input errors rather than being mislabeled as an infeasible problem.

Reported timings are separate:

- `elapsed_seconds`: input checks, model construction, solve, decoding, and
  operational validation; excludes dependency imports.
- `solver_wall_time_seconds`: CP-SAT's own solve time.
- `time_limit_seconds`: applies to solving, not the full Python function.

The default is one worker with seed 42. Multiple workers may change search
behavior; neither seed nor worker count guarantees identical tie-breaking across
OR-Tools releases. Optimal schedules can differ from the enumeration schedule
while sharing the same objective and satisfying the same constraints.

The supported full linear waiting-cost activity is limited to `2**53 - 1` to
avoid silently rounding integer objectives/bounds in the reported double values.
The classical references retain their existing input schema checks; unsupported
durations and malformed domains must be corrected by the caller.

## Run and compare

Classical comparison, without Ket:

```bash
python results/run_berth_solver_comparison.py
```

This writes `results/bap_solver_comparison.json` and `.csv`. It executes the
methods; it does not reuse archived timing or quantum reports. The JSON contains
the input, configuration, statuses, schedules, metrics, bounds, environment,
and timing scopes. Classical and quantum methods are compared on waiting slots,
not by substituting penalized energy for the operational objective.

Four-method comparison with the original QAOA/FALQON budgets:

```bash
python -m pip install -r requirements-classical.txt -r requirements-quantum.txt
python results/run_berth_solver_comparison.py --include-quantum
```

A second, six-qubit synthetic instance has a positive optimum of one waiting slot:

```bash
python results/run_berth_solver_comparison.py --include-quantum --instance data/synthetic/berth_waiting_v1.json --output-prefix results/bap_waiting_comparison
```

The original `results/quantum/berth_experiment.json` supplies quantum budgets.
The new input is passed directly to all methods. `HEURISTIC` remains the status
of quantum results even when a sampled solution matches the reference optimum.
An infeasible model, an encoding above the existing 12-qubit limit, or missing
classical feasibility evidence produces explicit `SKIPPED` quantum rows.
Actual runtime or dependency errors fail visibly instead of becoming fake results.

For larger classical instances, `--skip-enumeration` avoids the comparison
script's exhaustive reference. The default enumeration guard permits at most
100000 candidate combinations; `--enumeration-limit` changes this threshold.
The CP-SAT adapter itself has no enumeration dependency. Original quantum
runners still compute their own tiny exact reference internally.

These are illustrative comparisons on tiny synthetic instances, not a matched
resource benchmark or evidence of speedup. Quantum timers and final-circuit
counts have different scopes from classical solver timing; the detailed reports
state those differences. Neither quantum hardware nor GPU execution is involved.

## Tests

```bash
python -m unittest discover -s tests -p "test_reference.py" -v
python -m unittest discover -s tests -p "test_cpsat.py" -v
python -m unittest discover -s tests -p "test_bap_comparison.py" -v
```

The new test modules are explicitly skipped if optional OR-Tools is absent.
After installing both requirement files, `python -m unittest discover -s tests -v`
runs all 41 tests, including the original quantum checks.

Parity tests compare CP-SAT with enumeration over 128 seeded small instances.
Controlled native-status overrides exercise `FEASIBLE`, `UNKNOWN`, and
`MODEL_INVALID` branches without relying on nondeterministic timeouts; these
status tests are not performance measurements. See the
[validation record](VALIDATION.md) for executed checks and recorded versions.

## References and license

- [Google OR-Tools CP-SAT guide and statuses](https://developers.google.com/optimization/cp/cp_solver).
- [Shared HYPAQ model conventions](../README.md).
- [Quantum methodology](../quantum/README.md).

Original adapter and integration materials use the repository's Apache-2.0
license. OR-Tools, Ket, and their dependencies retain their respective licenses.
