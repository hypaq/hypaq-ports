# Guided exercises — HYPAQ Ports

The repository includes **three original classical teaching notebooks** in this
directory and **three original quantum BAP experiment notebooks** in
[`quantum/`](quantum/README.md). They share source code from `src/` and documented
synthetic JSON inputs from `data/synthetic/`. The original classical notebooks
use exact exhaustive enumeration.

An implemented [OR-Tools CP-SAT scenario](../scenarios/bap_cpsat/README.md) is
available separately, with an [additional BAP notebook](../scenarios/bap_cpsat/01_bap_cpsat.ipynb),
bringing the total to **seven notebooks**. The additional scenario preserves the
six original notebooks and their computational outputs. It is available on
`main` and is not part of the original `v0.1.0-alpha.1` source snapshot.

## Classical notebooks

| Notebook | Implemented now | Planned extensions |
| --- | --- | --- |
| [01 — Berth Allocation](01_berth_allocation.ipynb) | Exact BAP, exhaustive eight-bit QUBO search, and an Ising energy-equivalence check. | Operational berth timeline. |
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
These three notebooks use the original eight-qubit BAP input. Quantum crane
allocation and quantum replanning are not implemented in this alpha.

The experiments use synthetic data and simulation, not quantum hardware.
Optimization and feedback use exact simulated state-vector expectations; default
final counts use seeded classical sampling from a KBW state snapshot. Optional
native KBW sampling is also supported. Resource budgets differ between algorithms;
these results do not establish quantum advantage, a general algorithm ranking,
or industrial readiness. See the [quantum methodology](../docs/quantum/README.md).

## Additional BAP CP-SAT notebook — available now

| Notebook | Implemented experiment |
| --- | --- |
| [BAP CP-SAT and enumeration](../scenarios/bap_cpsat/01_bap_cpsat.ipynb) | Compare OR-Tools CP-SAT with exhaustive enumeration on the original zero-waiting input and an additional positive-waiting input, including schedules, solver status, objective bounds, and timings. |

The [scenario guide](../scenarios/bap_cpsat/README.md) provides installation,
execution, tests, and interpretation. The notebook requires the scenario's
OR-Tools dependencies but does not require Ket. A separate runner in that
scenario optionally compares all four methods: enumeration, CP-SAT, QAOA,
and FALQON. The four-method comparison uses the existing quantum implementations;
it does not change the original notebooks or historical reports.

## Local use

Clone the repository and open notebooks from within its directory tree. Each
notebook's setup cell locates the repository root in the current directory or
its parents and configures the shared-code import path. Run cells in order.

### Original classical path — standard library

Use Python 3.10+. The three original classical notebooks require only the Python
standard library. Jupyter is a separate notebook interface; install it if needed:

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

### Additional CP-SAT path — optional OR-Tools

Use Python 3.11+, preferably in a separate virtual environment. From the
repository root, install the scenario dependencies and run its demo and tests:

```bash
python -m pip install -r scenarios/bap_cpsat/requirements.txt
python scenarios/bap_cpsat/run_demo.py
python -m unittest discover -s scenarios/bap_cpsat/tests -v
```

Open the [additional notebook](../scenarios/bap_cpsat/01_bap_cpsat.ipynb) in Jupyter
using the kernel of that environment. Ket is not required for this notebook.
For comparison commands, including optional QAOA/FALQON execution and separate
JSON/CSV outputs, follow the [scenario guide](../scenarios/bap_cpsat/README.md).

### Quantum path

Use Python 3.11+ for the pinned quantum dependencies. The recorded environment
is Python 3.12.14 on Linux x86_64; wheel compatibility depends on the platform.
A separate virtual environment is recommended. From the repository root:

```bash
python -m pip install -r requirements-quantum.txt
python -m unittest discover -s tests -v
python results/quantum/run_berth_comparison.py
```

The test command in `tests/` runs the 20 original tests and imports Ket and
NumPy. The 22 CP-SAT scenario tests are run separately with the command in the
CP-SAT section above; the two suites cover 42 tests when their dependencies
are installed. In a standard-library-only environment, use the filtered
`test_reference.py` command. Jupyter is installed separately if needed. See the
[quantum notebook guide](quantum/README.md) for experiment details.

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

For one of the **three original classical notebooks**, proceed with its own
cells. For an **original quantum notebook**, install the pinned dependencies
in another setup cell first:

```python
%pip install -r /content/hypaq-ports/requirements-quantum.txt
```

For the **additional CP-SAT notebook**, install its own dependency set instead:

```python
%pip install -r /content/hypaq-ports/scenarios/bap_cpsat/requirements.txt
```

If Colab has already imported incompatible package versions, restart its runtime
after installation, set the working directory again, and run the notebook cells
in order. An existing clone is not updated by the setup cell; use a fresh clone
or explicitly select the relevant commit/tag when reproducing reference results.

Full external Jupyter/Colab execution was not validated in the recorded build
environment. See the original [quantum validation record](../docs/quantum/VALIDATION.md)
and [CP-SAT scenario validation record](../scenarios/bap_cpsat/VALIDATION.md)
for the checks completed and execution limitations.

## Supporting material

- [Project overview and current status](../README.md).
- [Model conventions and development guide](../docs/README.md).
- [Synthetic input assumptions](../data/synthetic/README.md).
- [Classical reference results](../results/README.md).
- [Quantum experiment configuration and results](../results/quantum/README.md).
- [Additional CP-SAT scenario and comparison guide](../scenarios/bap_cpsat/README.md).

Original repository materials are licensed under Apache-2.0 unless stated
otherwise. Third-party dependencies retain their own licenses.
