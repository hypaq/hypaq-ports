# Quantum reference experiment

`berth_experiment.json` defines the single-run configuration.
`run_berth_comparison.py` executes the original classical reference, Ket/KBW QAOA,
and Ket/KBW FALQON. The generated JSON and CSV contain actual simulator outputs.

```bash
python -m pip install -r requirements-quantum.txt
python results/quantum/run_berth_comparison.py
```

The JSON includes versions, seeds, algorithm settings, trajectories, probabilities,
sampled counts, feasible solutions, expectation-query counts and logical gate
resources. The CSV is a compact summary. CPU timings are environment-dependent
and should not be used to claim a quantum speedup.

The default final counts are seeded classical draws through Ket's snapshot
sampler from a KBW-computed state. Exact probabilities and analytic expectations
are simulator diagnostics. They are not shot-estimated training or hardware
measurements. The optional native KBW sampling mode is tested separately.

The two algorithms use different resource budgets. A comparison on one eight-qubit
instance is an integration demonstration, not a statistically supported ranking.
See `docs/quantum/README.md` for energy conventions and limitations.
