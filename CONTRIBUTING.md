# Contributing to ThanimamPro

## Reporting a defect or asking a question

Open an issue at <https://github.com/AranCastro/ThanimamPro/issues>. For a defect, give the input
(conditions or the structure file), the output obtained, the output expected, and the versions of
Python and of the packages in `requirements.txt`.

## Proposing a change

1. Fork the repository and create a branch from `main`.
2. Install the development tools: `pip install -e ".[dev]"`.
3. Make the change with a test that fails before it and passes after it.
4. Run `ruff check .` and `pytest -q`; both must pass.
5. Open a pull request that states what changed and why.

## Rules specific to this project

- **Literature data.** Every row of `data/literature_seed.csv` must carry the DOI of the paper the
  values were read from. Values are entered as printed; nothing is converted, interpolated or
  estimated. A value that is inconsistent within its source is left blank and described in
  `notes`. Run `python scripts/validate_literature_csv.py data/literature_seed.csv` before
  committing. The column rules are in `docs/LITERATURE_DATA_HANDOVER.md`.
- **Calibration.** The constants in `thanimampro_api/predict.py` are the output of
  `scripts/fit_surrogate.py`. After any change to the table, rerun the script, copy the
  coefficients and the leave-one-paper-out figures into `predict.py` and `README.md`, and confirm
  that `tests/test_calibration.py` passes.
- **Claims.** A property may be described as calibrated only if a held-out error is reported with
  it. Any other expression must be labelled illustrative.
- **XRD analysis.** A change to `thanimampro_api/structure.py` must keep the synthetic-scan
  accuracy tests passing.

## Conduct

Participation is governed by `CODE_OF_CONDUCT.md`.
