# Guided exercises — HYPAQ Ports

The public alpha includes **three classical teaching notebooks** in this
directory and **three quantum BAP experiment notebooks** in [`quantum/`](quantum/README.md).
They share source code from `src/` and documented synthetic JSON inputs from
`data/synthetic/`. The classical solver uses exact exhaustive enumeration;
OR-Tools CP-SAT remains a planned extension.

## Classical notebooks

| Notebook | Implemented now | Planned extensions |
| --- | --- | --- |
| [01 — Berth Allocation](01_berth_allocation.ipynb) | Exact BAP, exhaustive eight-bit QUBO search, and an Ising energy-equivalence check. | CP-SAT and an operational berth timeline. QAOA and FALQON are already available in separate quantum notebooks below. |
| [02 — Quay Crane Allocation](02_quay_crane_allocation.ipynb) | Exact classical allocation and independent demand/capacity metrics. | Validated crane QUBO/Ising formulation, followed by quantum experiments and an operational timeline. |
| [03 — Disruption and Replanning](03_disruption_and_replanning.ipynb) | Delayed arrival, original-plan validation, free replanning, and stability-aware replanning. | Additional disruptions, operational visualizations, quantum replanning, and AI-assisted scenario input. |

These three notebooks execute classical code. Exhaustive QUBO enumeration and
Ising energy checks do not simulate a quantum circuit. Crane allocation is a
simplified exercise independent of the berth schedule, not a complete QCSP.
Replanning is an offline arrival-delay scenario before service starts.

## Quantum notebooks — available now

| Notebook | Implemented experiment |
| --- | --- |
| [01 — BAP QAOA with Ket](quantum/01_berth_allocation_qaoa_ket.ipynb) | Eight-qubit BAP QAOA with a transverse-X mixer and SciPy COBYLA optimization. |
| [02 — BAP FALQON with Ket](quantum/02_berth_allocation_falqon_ket.ipynb) | First-order feedback-based evolution using exact KBW simulator expectations. |
| [03 — BAP comparison](quantum/03_berth_allocation_comparison.ipynb) | Comparison of the exact classical reference, QAOA, and FALQON, including metrics and experiment plots. |

These notebooks execute quantum circuits through **Ket on the KBW CPU simulator**.
Quantum execution currently covers the tiny BAP instance only. Quantum crane
allocation and quantum replanning are not implemented in this alpha.

The experiments use synthetic data and simulation, not quantum hardware.
Optimization and feedback use exact simulated state-vector expectations; default
final counts use seeded classical sampling from a KBW state snapshot. Optional
native KBW sampling is also supported. Resource budgets differ between algorithms;
these results do not establish quantum advantage, a general algorithm ranking,
or industrial readiness. See the [quantum methodology](../docs/quantum/README.md).

## Local use

Clone the repository and open notebooks from within its directory tree. Each
notebook's setup cell locates the repository root in the current directory or
its parents and configures the shared-code import path. Run cells in order.

### Classical path

Use Python 3.10+. The classical notebook cells require only the Python standard
library. Jupyter is a separate notebook interface; install it if needed:

```bash
python -m pip install jupyterlab
```

From the repository root, classical checks and result regeneration are:

```bash
python -m unittest discover -s tests -p "test_reference.py" -v
python results/generate_reference.py
```

These commands do not require Ket or OR-Tools. See the
[classical entry guide](../START_HERE.md) and
[development guide](../docs/README.md) for additional context.

### Quantum path

Use Python 3.11+ for the pinned quantum dependencies. The recorded environment
is Python 3.12.14 on Linux x86_64; wheel compatibility depends on the platform.
A separate virtual environment is recommended. From the repository root:

```bash
python -m pip install -r requirements-quantum.txt
python -m unittest discover -s tests -v
python results/quantum/run_berth_comparison.py
```

The full test suite imports Ket and NumPy. In a classical-only environment, use
the filtered classical test command above. Jupyter is installed separately if
needed. See the [quantum notebook guide](quantum/README.md) for experiment details.

## Google Colab

Open a notebook through Colab's GitHub picker. Opening an individual notebook
does not download the shared code or data. First run the following in a separate
setup cell to clone the repository and set the working directory:

```python
from pathlib import Path
import subprocess
import os

repo = Path('/content/hypaq-ports')
if not repo.exists():
    subprocess.run(
        ['git', 'clone', 'https://github.com/hypaq/hypaq-ports.git', str(repo)],
        check=True,
    )
os.chdir(repo)
```

For a **classical notebook**, proceed with its own cells. For a **quantum
notebook**, install the pinned dependencies in another setup cell first:

```python
%pip install -r /content/hypaq-ports/requirements-quantum.txt
```

If Colab has already imported incompatible package versions, restart its runtime
after installation, set the working directory again, and run the notebook cells
in order. An existing clone is not updated by the setup cell; use a fresh clone
or explicitly select the relevant commit/tag when reproducing reference results.

Full external Jupyter/Colab execution was not validated in the recorded build
environment. See the [validation record](../docs/quantum/VALIDATION.md) for the
checks completed and execution limitations.

## Supporting material

- [Project overview and current status](../README.md).
- [Model conventions and development guide](../docs/README.md).
- [Synthetic input assumptions](../data/synthetic/README.md).
- [Classical reference results](../results/README.md).
- [Quantum experiment configuration and results](../results/quantum/README.md).

Original repository materials are licensed under Apache-2.0 unless stated
otherwise. Third-party dependencies retain their own licenses.
