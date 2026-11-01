# Guided exercises

| Notebook | Implemented now | Next extension |
| --- | --- | --- |
| `01_berth_allocation.ipynb` | Exact BAP, all-bitstring QUBO search, Ising energy check. | CP-SAT, Ket/KBW QAOA, timeline. |
| `02_quay_crane_allocation.ipynb` | Exact allocation and independent capacity metrics. | QUBO formulation and validation, then quantum execution. |
| `03_disruption_and_replanning.ipynb` | Delayed arrival, original-plan validation, free and stable replanning. | Additional disruptions, scenarios, visualizations. |

These are executable classical teaching notebooks, not quantum simulation results.
They import shared code from `src/` and load versioned synthetic JSON instances.

## Local use

Open a notebook from a Jupyter environment with Python 3.10+. The setup cell
locates the repository root by looking in the current directory and its parents.
Run all cells in order. No third-party Python package is required by the cells.

## Google Colab

After merging this package into the public repository, open a notebook through
Colab's GitHub picker. First run the following in a separate setup cell so the
shared code and data are available to the Colab runtime:

```python
from pathlib import Path
import subprocess
import os

repo = Path('/content/hypaq-ports')
if not repo.exists():
    subprocess.run(['git', 'clone', 'https://github.com/hypaq/hypaq-ports.git', str(repo)], check=True)
os.chdir(repo)
```

Then run the notebook's own cells. Opening a notebook in Colab does not itself
download the rest of the repository. Use a fresh clone or the relevant commit
when reproducing a reference run.
