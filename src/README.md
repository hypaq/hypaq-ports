# Shared reference code

`hypaq_ports/reference.py` provides the small, standard-library-only reference
functions used by all three notebooks:

| Function | Purpose |
| --- | --- |
| `load_json`, `save_json` | Read inputs and write reproducible reports. |
| `solve_berth_exact` | Enumerate one-slot berth assignments, optionally penalizing changes. |
| `validate_berth_schedule`, `berth_metrics` | Check operational constraints and calculate waiting/stability metrics. |
| `build_berth_qubo` | Build the full binary encoding with explicit constraint penalties. |
| `qubo_energy`, `decode_berth_bits` | Evaluate and decode binary assignments. |
| `qubo_to_ising` | Produce Ising coefficients with the constant offset preserved. |
| `solve_crane_exact`, `evaluate_crane_schedule` | Enumerate crane allocations and validate demand/resource metrics. |
| `apply_arrival_delay` | Make a copied berth instance with a structured arrival change. |

Use Python 3.10+. Notebooks configure their import path automatically. For scripts,
add `src/` to `PYTHONPATH` or use the root-detection pattern shown in the notebooks.
No package installation or command-line application is provided in this stage.

These references are exponential teaching implementations. They are not CP-SAT
adapters, quantum simulators, operational schedulers, or an AI agent. See
`docs/README.md` for model assumptions and planned extensions.
