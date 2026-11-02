# Additional BAP scenario — OR-Tools CP-SAT

This folder adds a CP-SAT demonstration alongside HYPAQ Ports' existing classical
and quantum examples. All new files live under `scenarios/bap_cpsat/`.
The existing source, notebooks, requirements, documentation, historical reports
and release tags are unchanged.

The scenario **reuses the already published adapter** at
[`src/hypaq_ports/classical/cpsat.py`](../../src/hypaq_ports/classical/cpsat.py).
It imports `hypaq_ports.classical.cpsat` directly, so no change to a package
`__init__.py` is needed. Keep the folder inside a full clone of `hypaq-ports`;
it is not a standalone replacement for the repository.

## Files

| File or directory | Purpose |
| --- | --- |
| [run_demo.py](run_demo.py) | Run CP-SAT and print the schedule, waiting slots, status, bound and timings. |
| [compare.py](compare.py) | Live enumeration/CP-SAT comparison, with optional QAOA and FALQON. |
| [01_bap_cpsat.ipynb](01_bap_cpsat.ipynb) | Additional notebook comparing CP-SAT and enumeration on two inputs. |
| [requirements.txt](requirements.txt) | Optional CP-SAT environment; does not require Ket. |
| [data/berth_waiting_v1.json](data/berth_waiting_v1.json) | Additional tiny input with a positive optimum. |
| [results/](results/) | New comparison JSON/CSV files, separate from historical results. |
| [tests/test_scenario.py](tests/test_scenario.py) | Adapter parity, comparison contracts and output-boundary checks. |
| [VALIDATION.md](VALIDATION.md) | Local validation record and limitations. |

## 1. Install the optional CP-SAT environment

Use Python 3.11+; validation used Python 3.12.14 on Linux x86_64. From the
repository root, preferably in a **new virtual environment**:

```bash
python -m venv .venv-cpsat
source .venv-cpsat/bin/activate
python -m pip install -r scenarios/bap_cpsat/requirements.txt
```

Windows cmd activation: `.venv-cpsat\Scripts\activate`.
PowerShell: `.venv-cpsat\Scripts\Activate.ps1`.
Wheel availability and the quantum backend must be checked on the chosen platform.
Using a separate environment preserves the dependencies of your existing demos.

## 2. Run the CP-SAT demo

```bash
python scenarios/bap_cpsat/run_demo.py
```

This reads the existing `data/synthetic/berth_tiny_v1.json` and prints an OPTIMAL
schedule with zero waiting slots. No files are written. For positive waiting:

```bash
python scenarios/bap_cpsat/run_demo.py --instance scenarios/bap_cpsat/data/berth_waiting_v1.json
```

That input has two vessels arriving at slot 0, one berth and three slots.
One vessel must wait, giving an optimum of one waiting slot.

## 3. Compare enumeration and CP-SAT

```bash
python scenarios/bap_cpsat/compare.py --output-prefix scenarios/bap_cpsat/results/my_classical_run
```

The methods receive the same instance and reuse the operational validator.
Tie-breaking can produce different schedules with the same objective.
The default run does not import Ket. It writes only inside this scenario.

## 4. Optional comparison with the existing quantum methods

In the same optional environment, install the repository's **unchanged** quantum
requirements, then execute all four methods:

```bash
python -m pip install -r requirements-quantum.txt
python scenarios/bap_cpsat/compare.py --include-quantum --output-prefix scenarios/bap_cpsat/results/my_four_method_run
python scenarios/bap_cpsat/compare.py --include-quantum --instance scenarios/bap_cpsat/data/berth_waiting_v1.json --output-prefix scenarios/bap_cpsat/results/my_waiting_run
```

The command reads the existing QAOA/FALQON implementations and
`results/quantum/berth_experiment.json`. It computes fresh results; it does not
mix archived quantum results with new CP-SAT timings or execute the old report
generator. New JSON reports include input, statuses, schedules, configuration,
metrics, bounds, environment and timing notes; CSV files summarize the comparison.

With no `--output-prefix`, reports go to this folder's `results/bap_comparison.*`.
Use a custom prefix as above to retain the supplied example reports. The CLI
rejects output prefixes outside `scenarios/bap_cpsat/`, protecting old reports.

| Track | Method | Meaning |
| --- | --- | --- |
| Existing classical | Exhaustive enumeration | Exact reference for tiny instances. |
| Additional CP-SAT | OR-Tools CP-SAT | Direct constraints, search and propagation; reports optimality evidence. |
| Existing quantum | QAOA and FALQON, Ket/KBW | Heuristic optimization through CPU-simulated circuits. |

CP-SAT distinguishes OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN and MODEL_INVALID.
Only OPTIMAL proves optimality; FEASIBLE has an incumbent without that proof.
UNKNOWN must not be interpreted as infeasibility or zero waiting.
Quantum rows remain HEURISTIC even when a best sampled solution matches the
reference optimum. Cross-method objectives use waiting slots, not penalized energy.

## 5. Notebook and tests

Open [01_bap_cpsat.ipynb](01_bap_cpsat.ipynb) with a separately installed Jupyter
interface and select the kernel of the optional environment. Run its cells in
order. The notebook only prints results. It does not alter existing notebooks.

Run the **additional** scenario tests without changing the original test suite:

```bash
python -m unittest discover -s scenarios/bap_cpsat/tests -v
```

There are 22 scenario tests. Adapter/comparison tests require OR-Tools and are
explicitly skipped if it is missing; a complete local run must pass all 22 without
skips. The original commands and original test discovery remain unchanged.

## Scope and license

This is the same simplified discrete BAP with one-slot services, arrivals,
berth compatibility and blocked berth/slot pairs. There is no new crane model,
multi-slot service model or stability-aware CP-SAT replanning.

The quantum comparison uses the original KBW CPU simulator and at most 12 encoded
qubits. Optimization/feedback uses exact simulated expectations; default final
sampling uses seeded state snapshots. Original quantum preparation includes tiny
exact-reference enumeration. Budgets and timer scopes differ across methods.
These are integration exercises, not industrial benchmarks or quantum advantage.

Adding this folder does not modify the source attached to existing release tags.
No new release or GitHub Package is needed to use the additional scenario on main.

Original materials use the repository's [Apache-2.0 license](../../LICENSE).
Third-party dependencies retain their respective licenses. References:
[OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver),
[Ket](https://quantumket.org/).
