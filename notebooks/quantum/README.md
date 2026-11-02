# Quantum experiments with Ket and KBW

These notebooks extend the existing classical berth-allocation exercise. They
execute **actual quantum circuits in the KBW simulator through Ket**. They do not
use quantum hardware, and there is no silent NumPy fallback for algorithm runs.
NumPy is used independently in the integration tests to check the Ket circuits.

| Notebook | Experiment |
| --- | --- |
| [01 — BAP QAOA with Ket](01_berth_allocation_qaoa_ket.ipynb) | Eight-qubit QAOA with a transverse-X mixer and SciPy COBYLA. |
| [02 — BAP FALQON with Ket](02_berth_allocation_falqon_ket.ipynb) | First-order FALQON with live KBW state and exact feedback expectations. |
| [03 — BAP comparison](03_berth_allocation_comparison.ipynb) | Compare both quantum algorithms with the original exact classical reference. |

These are the three original quantum notebooks. The additional comparison with
OR-Tools CP-SAT is available separately in
[`scenarios/bap_cpsat/`](../../scenarios/bap_cpsat/README.md), alongside these
experiments. The original notebook computations and saved outputs are preserved.

## Install and run

Clone or download `hypaq-ports`. The notebooks, shared source, and inputs are
already included in the repository. Use Python 3.11+ (tested with 3.12.14 on
Linux x86_64), preferably in a separate virtual environment, then run from the
**repository root**, not from `notebooks/quantum/`:

```bash
python -m pip install -r requirements-quantum.txt
python -m unittest discover -s tests -v
python results/quantum/run_berth_comparison.py
```

The test command above runs the 20 original tests: ten classical checks and ten
quantum integration checks. The additional CP-SAT tests are run separately as
described below.

Open the notebooks in your Jupyter environment and run all cells in order.
Jupyter is the notebook interface, not a runtime dependency of the experiment
script. To install a local interface if needed: `python -m pip install jupyterlab`.

## Google Colab

Opening one notebook in Colab does not download its shared source or inputs.
Run this in a separate first cell to clone the repository and set the working
directory:

```python
from pathlib import Path
import subprocess
import os
repo = Path('/content/hypaq-ports')
if not repo.exists():
    subprocess.run(['git', 'clone', 'https://github.com/hypaq/hypaq-ports.git', str(repo)], check=True)
os.chdir(repo)
```

Then install dependencies in another cell:

```python
%pip install -r /content/hypaq-ports/requirements-quantum.txt
```

If Colab has already imported incompatible package versions, restart its runtime
after installation, set the working directory again, and run the notebook. Use a
fresh clone when testing new commits. Wheels depend on OS, architecture and
Python compatibility; only the environment recorded in the report is validated.
Full external Jupyter/Colab kernel execution was not validated in the recorded
build environment; see the [quantum validation record](../../docs/quantum/VALIDATION.md).

## What the results mean

- The shared instance remains `data/synthetic/berth_tiny_v1.json`.
- Binary variable i is register index i and the leftmost/MSB bit in displayed strings.
- QAOA minimizes exact KBW expectations of the scaled nonconstant Hamiltonian.
- FALQON obtains its feedback from exact KBW expectations in live execution.
- All reported full QUBO energies restore the omitted constant and scaling.
- Default final counts use the public `QuantumState.sample` method on a dumped
  KBW state, with seed 42. This is classical seeded sampling from a simulated
  quantum state, not native KBW sampling or QPU measurement.
- Set `sampling='kbw_native'` in a runner to use `ket.sample`. This adapter does
  not expose a native sampling seed; exact probabilities remain simulator diagnostics.
- Feasibility is checked against the original operational constraints, not inferred
  from low Hamiltonian energy or the most frequent bitstring.
- A finite-step FALQON trace may increase in energy. Monotonicity and global
  optimality are not asserted. Change step size and record observed behavior.

The comparison is one illustrative instance with different resource budgets.
It does not rank the algorithms or demonstrate speedup. These three notebooks
use exhaustive enumeration as their classical reference. See the
[quantum methodology](../../docs/quantum/README.md).

## Additional comparison with OR-Tools CP-SAT

The implemented [BAP CP-SAT scenario](../../scenarios/bap_cpsat/README.md)
provides a separate demo, notebook, tests, and live comparison runner. It reuses
the existing QAOA/FALQON implementations and operational validators without
changing the original quantum notebooks or reports.

To run all four methods on the same input, install both dependency sets in the
chosen environment and execute these commands from the repository root:

```bash
python -m pip install -r scenarios/bap_cpsat/requirements.txt -r requirements-quantum.txt
python scenarios/bap_cpsat/compare.py --include-quantum --output-prefix scenarios/bap_cpsat/results/my_four_method_run
```

This executes exhaustive enumeration, OR-Tools CP-SAT, QAOA, and FALQON live,
rather than combining archived quantum results with new classical timings.
The custom prefix keeps the supplied example reports unchanged. New JSON/CSV
files remain inside `scenarios/bap_cpsat/`; the CLI rejects output prefixes
outside that directory.

The scenario supports the original eight-qubit input and an additional
[six-qubit positive-waiting input](../../scenarios/bap_cpsat/data/berth_waiting_v1.json).
CP-SAT distinguishes proved optimality from a feasible incumbent or an
inconclusive result. Quantum rows remain `HEURISTIC`, even when their best
feasible sampled solution matches a known optimum. Different resource budgets
and timing boundaries prevent interpreting these demos as a speedup benchmark.

Run the 22 additional scenario tests separately:

```bash
python -m unittest discover -s scenarios/bap_cpsat/tests -v
```

Together with the 20 original tests, these cover 42 tests across two discovery
commands. The CP-SAT scenario tests require its optional OR-Tools dependencies;
they do not require Ket. See the [scenario guide](../../scenarios/bap_cpsat/README.md)
and [validation record](../../scenarios/bap_cpsat/VALIDATION.md) for full usage,
recorded results, status handling, and execution limitations.

The original `v0.1.0-alpha.1` source snapshot does not include CP-SAT. The
additional scenario is available on `main`; existing release tags are unchanged.
