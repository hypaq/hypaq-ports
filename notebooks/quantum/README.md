# Quantum experiments with Ket and KBW

These notebooks extend the existing classical berth-allocation exercise. They
execute **actual quantum circuits in the KBW simulator through Ket**. They do not
use quantum hardware, and there is no silent NumPy fallback for algorithm runs.
NumPy is used independently in the integration tests to check the Ket circuits.

| Notebook | Experiment |
| --- | --- |
| `01_berth_allocation_qaoa_ket.ipynb` | Eight-qubit QAOA with a transverse-X mixer and SciPy COBYLA. |
| `02_berth_allocation_falqon_ket.ipynb` | First-order FALQON with live KBW state and exact feedback expectations. |
| `03_berth_allocation_comparison.ipynb` | Compare both quantum algorithms with the original exact classical reference. |

## Install and run

Merge this add-on into the repository root, preserving existing files. Use Python
3.11+ (tested with 3.12.14 on Linux x86_64), then run in the repository root:

```bash
python -m pip install -r requirements-quantum.txt
python -m unittest discover -s tests -v
python results/quantum/run_berth_comparison.py
```

Open the notebooks in your Jupyter environment and run all cells in order.
Jupyter is the notebook interface, not a runtime dependency of the experiment
script. To install a local interface if needed: `python -m pip install jupyterlab`.

## Google Colab

After the add-on has been uploaded to GitHub, run this in a separate first cell:

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
It does not rank the algorithms or demonstrate speedup. CP-SAT is not implemented
in this add-on. See [methodology](../../docs/quantum/README.md).
