# Validation record

Date: **2026-11-01**. Classical base: `d094fc6c65504636a47b8bb5d2fcaa4ac1207944`.

## Environment and execution

- CPython 3.12.14, Linux x86_64, glibc 2.39.
- Ket 0.10.4.2, Libket 0.7.1, KBW 0.5.1.
- NumPy 2.3.5, SciPy 1.17.0, Matplotlib 3.10.8.
- CPU KBW sparse simulation; no quantum hardware or GPU execution.
- Exact state-vector expectations for cost and feedback.
- Default final readout: 4096 seeded samples through Ket's snapshot sampler.

## Checks completed

| Check | Result |
| --- | --- |
| Original classical behavioral tests | 10 passed, original files unchanged. |
| New Ket integration tests | 10 passed. |
| All 256 basis-state cost values | Ket observables agree with the original QUBO within stated numerical tolerances. |
| QAOA state evolution | Matches independent NumPy evolution. |
| FALQON commutator sign and sequence | Matches independent NumPy feedback/state calculations. |
| Snapshot and native sampling | Seeded snapshot repeatability and native shot totals verified. |
| Notebook execution | 13 code cells across three notebooks executed successfully in in-process IPython. |
| Notebook structure | All three files validated with nbformat; one embedded PNG plot in each notebook. |
| Charts | QAOA trajectory, FALQON energy/feedback, and feasibility comparison visually inspected. |
| Standalone runner | Executed and generated the bundled JSON and CSV. |

The build environment does not permit the sockets required to start an external
Jupyter kernel. Notebook code, IPython magics, HTML tables and plots were therefore
executed in process using real Ket/KBW. Launching a full external Jupyter or Colab
session was not validated. The notebooks retain the standard Python 3 kernelspec.

## Recorded illustrative results

From the bundled `results/quantum/berth_comparison_reference.json`:

| Metric | QAOA | FALQON |
| --- | --- | --- |
| Best sampled feasible waiting cost | 0 slots | 0 slots |
| Feasible probability from simulated state | 0.236650 | 0.408951 |
| Optimal probability from simulated state | 0.172132 | 0.338561 |
| Empirical feasible frequency in final samples | 0.231689 | 0.410400 |
| Full QUBO energy from normalized distribution | 2.384798 | 2.131777 |
| Cost expectation queries | 161 | 65 |
| Feedback expectation queries | 0 | 64 |
| Logical gates in the final circuit | 136 | 4096 |
| Logical final-circuit depth | 50 | 1103 |

The classical exact optimum is zero waiting slots. The quantum methods found
samples matching that objective but retain heuristic status. Their nonzero
expected energies include infeasible states and penalties. Both QAOA restarts
reached the configured evaluation budget; neither is labeled optimizer-converged.
The FALQON raw energy trace records one increase, including roundoff effects.

These are single-run, finite-precision simulator observations with different
resource budgets, not a speedup result, an algorithm ranking, or industrial
validation. The relative approximation ratio dividing by a zero optimum is not
reported. Runtime values in the JSON are specific to this environment.
