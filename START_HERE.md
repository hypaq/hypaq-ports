# HYPAQ Ports — initial development assets

This package adds initial content to all six directories planned in the existing
HYPAQ Ports README. Content is in English. Merge the ZIP's **contents** into the
root of `hypaq/hypaq-ports`, preserving your existing `README.md` and `LICENSE`.
This package deliberately does not replace either file. No GitHub changes have
been made automatically.

## What is included

- Three executable notebooks: berth allocation, crane allocation, and replanning.
- Standard-library Python reference functions and an independent berth validator.
- A tiny berth QUBO and Ising mapping with constant offsets preserved.
- Three documented synthetic JSON inputs.
- Generated classical reference outputs and a regeneration script.
- Behavioral tests and a development guide.

## Verify

With Python 3.10+ in the repository root:

```bash
python -m unittest discover -s tests -v
python results/generate_reference.py
```

Open the notebooks in order. The code cells use only Python's standard library.
Jupyter or Google Colab provides the notebook interface. No OR-Tools or Ket
installation is required for this first package because their adapters have not
yet been implemented.

## Suggested README update after upload

Update the existing README's project-status, repository-layout and getting-started
paragraphs to reflect that initial classical notebooks, data, code and references
are now present. Retain CP-SAT, Ket/KBW, QAOA, AI assistance and visualizations as
planned work. Link the exercise notebooks and `docs/README.md` from that page.
The complete v0.1.0 quantum exercise remains a future milestone.

Suggested commit message: `Add initial smart-port exercises and exact reference models`.

## License

These new original materials are intended for the existing Apache-2.0 repository.
Preserve its full `LICENSE` file when uploading. No code from HYPAQ's GPL-licensed
research repository is included. Third-party dependencies and trademarks retain
their own terms.
