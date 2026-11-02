# BAP — OR-Tools CP-SAT adapter and additional scenario

This optional adapter solves the **existing discrete, one-slot Berth Allocation
Problem** using OR-Tools CP-SAT. It accepts the same base instance dictionary as
`solve_berth_exact(instance)` and returns the same operational schedule format.

The adapter is in [`src/hypaq_ports/classical/cpsat.py`](../../src/hypaq_ports/classical/cpsat.py).
It reuses the shared schema checker and independent operational validator.
It does not call enumeration or the quantum backend and does not use QUBO penalties.
The original enumeration and Ket implementations remain available.

The executable demo, notebook, comparisons, optional requirements, additional
input, reports, and tests are in
[`scenarios/bap_cpsat/`](../../scenarios/bap_cpsat/README.md).
This scenario is available on `main` alongside the original examples. The
original `v0.1.0-alpha.1` source snapshot does not contain the CP-SAT adapter or
this additional scenario. Documentation changes do not modify existing tags.

## Install

Use Python 3.11+ for the pinned dependency set; tested on Python 3.12.14,
Linux x86_64. Run all shell commands in this guide from the **repository root**,
not from `docs/classical/`. A separate virtual environment preserves the
dependencies of your existing demos:

```bash
python -m venv .venv-cpsat
```

Activate it with `source .venv-cpsat/bin/activate` on Linux/macOS,
`.venv-cpsat\Scripts\activate` in Windows cmd, or
`.venv-cpsat\Scripts\Activate.ps1` in PowerShell. Then install:

```bash
python -m pip install -r scenarios/bap_cpsat/requirements.txt
```

This installs OR-Tools and NumPy. Ket is not required for CP-SAT or the
enumeration/CP-SAT comparison. Platform-specific wheel availability must be
checked for the chosen operating system, architecture, and Python version.

The adapter imports OR-Tools only when called. Original standard-library
references remain usable without it. Dependency errors are explicit; the adapter
never silently falls back to exhaustive enumeration.

## Python API

From a Python session or notebook whose working directory is the repository
root, add `src/` to the import path and import the existing adapter module directly:

```python
from pathlib import Path
import sys

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "src"))

from hypaq_ports.classical.cpsat import solve_berth_cpsat
from hypaq_ports.reference import load_json

instance = load_json(ROOT / "data/synthetic/berth_tiny_v1.json")
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

The import is `from hypaq_ports.classical.cpsat import solve_berth_cpsat`;
it does not require adding or modifying a package `__init__.py`.
The scenario's `run_demo.py`, `compare.py`, and notebook configure the source
path themselves. The notebook also detects the repository root.

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

### CP-SAT demo

```bash
python scenarios/bap_cpsat/run_demo.py
```

This reads the original `data/synthetic/berth_tiny_v1.json` and prints the solver
report without writing files. The expected optimum is zero waiting slots.
The report includes the schedule, operational metrics, status, bound and timings.

### Enumeration and CP-SAT, without Ket

```bash
python scenarios/bap_cpsat/compare.py --output-prefix scenarios/bap_cpsat/results/my_classical_run
```

This executes both methods and writes
`scenarios/bap_cpsat/results/my_classical_run.json` and `.csv`.
It does not reuse archived timing or quantum reports. The JSON contains the
input, configuration, statuses, schedules, metrics, bounds, environment, and
timing notes. Cross-method objectives use waiting slots, not penalized QUBO energy.

### Four-method comparison with Ket/KBW

Install the unchanged quantum requirements in the same optional environment,
then execute enumeration, CP-SAT, QAOA, and FALQON:

```bash
python -m pip install -r requirements-quantum.txt
python scenarios/bap_cpsat/compare.py --include-quantum --output-prefix scenarios/bap_cpsat/results/my_four_method_run
```

### Additional positive-waiting input

The additional [six-qubit instance](../../scenarios/bap_cpsat/data/berth_waiting_v1.json)
has two vessels arriving at slot 0, one berth, and three slots. Its optimum is
one waiting slot. Run CP-SAT alone:

```bash
python scenarios/bap_cpsat/run_demo.py --instance scenarios/bap_cpsat/data/berth_waiting_v1.json
```

Or compare all four methods after installing the quantum dependencies:

```bash
python scenarios/bap_cpsat/compare.py --include-quantum --instance scenarios/bap_cpsat/data/berth_waiting_v1.json --output-prefix scenarios/bap_cpsat/results/my_waiting_run
```

The `my_*` output prefixes retain the supplied example reports. Without an
explicit prefix, the comparison overwrites its own
`scenarios/bap_cpsat/results/bap_comparison.json` and `.csv`. The CLI rejects
prefixes outside the additional scenario directory. Neither the root classical
reports nor the original quantum reports are rewritten by this scenario.

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

## Notebook and recorded outputs

Open the additional [CP-SAT notebook](../../scenarios/bap_cpsat/01_bap_cpsat.ipynb)
with a separately installed Jupyter interface and select the kernel belonging
to the optional environment. Its Python cells compare enumeration and CP-SAT
on both inputs without writing reports. Full Jupyter/Colab kernel execution
was not validated for this scenario; the code cells were executed in-process.

The original six classical/quantum notebooks retain their computations and saved
outputs. Recorded comparisons are available separately:

- [Original-input comparison CSV](../../scenarios/bap_cpsat/results/bap_comparison.csv).
- [Positive-waiting comparison CSV](../../scenarios/bap_cpsat/results/bap_waiting_comparison.csv).
- [Detailed JSON reports](../../scenarios/bap_cpsat/results/).

## Tests

Run the 22 additional scenario tests after installing its requirements:

```bash
python -m unittest discover -s scenarios/bap_cpsat/tests -v
```

Adapter/comparison checks are explicitly skipped if optional OR-Tools is absent.
A complete scenario run must pass all 22 tests without skips. This command does
not require Ket.

The 20 original classical/quantum tests remain in `tests/`. To run both suites,
install the scenario and quantum dependency sets, then execute both commands:

```bash
python -m pip install -r scenarios/bap_cpsat/requirements.txt -r requirements-quantum.txt
python -m unittest discover -s tests -v
python -m unittest discover -s scenarios/bap_cpsat/tests -v
```

The expected total is **42 tests: 20 original plus 22 additional**.
Discovery in `tests/` alone does not run the separate scenario suite.
To run only the ten original standard-library checks without OR-Tools or Ket:

```bash
python -m unittest discover -s tests -p "test_reference.py" -v
```

Parity tests compare CP-SAT with enumeration over 128 seeded small instances.
Controlled native-status overrides exercise `FEASIBLE`, `UNKNOWN`, and
`MODEL_INVALID` branches without relying on nondeterministic timeouts; these
status tests are not performance measurements. See the
[scenario validation record](../../scenarios/bap_cpsat/VALIDATION.md) for executed
checks, recorded versions, and limitations. These are local validation results;
they do not constitute an independent external reproduction.

## References and license

- [Google OR-Tools CP-SAT guide and statuses](https://developers.google.com/optimization/cp/cp_solver).
- [Additional BAP CP-SAT scenario guide](../../scenarios/bap_cpsat/README.md).
- [Shared HYPAQ model conventions](../README.md).
- [Quantum methodology](../quantum/README.md).

Original adapter and integration materials use the repository's Apache-2.0
license. OR-Tools, Ket, and their dependencies retain their respective licenses.
