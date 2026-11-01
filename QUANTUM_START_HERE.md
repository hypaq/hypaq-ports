# HYPAQ Ports — Ket/KBW quantum add-on

This is an **incremental package** for the existing public `hypaq/hypaq-ports`
repository at classical base commit `d094fc6`. Extract the ZIP and upload its
contents into the repository root, preserving the directory structure.

This add-on does not replace the root README, LICENSE, original notebooks,
synthetic data, classical code or existing tests. It requires those files to be
present. It is not a standalone copy of the repository. No remote GitHub changes
have been made automatically.

## Added paths

| Path | Content |
| --- | --- |
| `notebooks/quantum/` | Three executed notebooks with QAOA, FALQON, comparison and plots. |
| `src/hypaq_ports/quantum/` | Ket backend and QAOA/FALQON runners using the shared classical BAP. |
| `results/quantum/` | Experiment configuration, regeneration script, actual JSON and CSV results. |
| `tests/test_quantum.py` | Ten integration checks, including an independent NumPy oracle. |
| `docs/quantum/README.md` | Mathematical conventions, resources and limitations. |
| `requirements-quantum.txt` | Exact versions tested for this extension. |

## Run after merging

```bash
python -m pip install -r requirements-quantum.txt
python -m unittest discover -s tests -v
python results/quantum/run_berth_comparison.py
```

Tested with Python 3.12.14 on Linux x86_64. Use Python 3.11+ for the pinned
dependency set. See `notebooks/quantum/README.md` for local and Colab setup.

The notebooks execute real quantum circuits in the classical **KBW simulator**
through **Ket**. They do not use quantum hardware. Their default final samples
are generated with a seed from the simulator's state snapshot; optimizer and
feedback queries use analytic expectations. These distinctions appear in reports.

## Update the public page

After upload, update the root README's availability status and link these paths:

- `notebooks/quantum/01_berth_allocation_qaoa_ket.ipynb`
- `notebooks/quantum/02_berth_allocation_falqon_ket.ipynb`
- `notebooks/quantum/03_berth_allocation_comparison.ipynb`
- `docs/quantum/README.md`
- `results/quantum/berth_comparison_summary.csv`

It is now accurate to describe Ket/KBW QAOA and FALQON as implemented simulator
experiments on the tiny berth instance after these files have been merged.
CP-SAT, AI assistance, other port quantum formulations and hardware execution
remain future work. No global quantum advantage or performance ranking is claimed.

Suggested commit: `Add Ket/KBW QAOA and FALQON berth experiments`.

Original extension content follows the repository's Apache-2.0 license. Preserve
the existing LICENSE. Third-party technologies retain their own licenses.
