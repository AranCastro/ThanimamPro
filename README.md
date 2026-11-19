[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18648128.svg)](https://doi.org/10.5281/zenodo.18648128)
[![CI](https://github.com/AranCastro/ThanimamPro/actions/workflows/python.yml/badge.svg)](https://github.com/AranCastro/ThanimamPro/actions/workflows/python.yml)

# ThanimamPro

**ThanimamPro** links synthesis conditions, X-ray diffraction (XRD) line-broadening analysis and a
curated literature table for titanium dioxide (TiO2) and doped TiO2 in one open workflow. It is
written in Python with a Streamlit interface.

This is version 0.2.0. The DOI above is the Zenodo concept DOI, which resolves to the latest archived
release; version 0.1.1 is archived as https://doi.org/10.5281/zenodo.18648129. Changes are listed in
`CHANGELOG.md`.

---

## Statement of Need

Synthesis conditions, structural characterisation and functional properties of oxide
nanomaterials are reported in separate sections of papers and in inconsistent forms. ThanimamPro
provides (i) a schema for synthesis records, (ii) a documented line-broadening analysis of
laboratory XRD scans, (iii) a traceable table of experimental band gaps and BET surface areas, and
(iv) simple relations fitted to that table and reported together with their held-out error.

---

## Core Functionality

| Module | Content |
|---|---|
| `thanimampro_api.schemas` | Validated records for synthesis conditions, structural descriptors and targets |
| `thanimampro_api.structure` | CIF cell parameters; peak detection, Scherrer and Williamson–Hall analysis of continuous scans; phase matching against four reference phases |
| `thanimampro_api.predict` | Band gap and surface area fitted to the literature table; further illustrative, unvalidated properties |
| `thanimampro_api.mapper`, `sensitivity` | Property maps and one-factor-at-a-time sensitivity |
| `thanimampro_api.inverse` | Ranking of calcination temperatures against property targets, with a check that the target is attainable |
| `thanimampro_api.database` | Loading and filtering of the literature table |
| `streamlit_app.py` | Interface to all of the above, with scenario comparison and report export |

The function-level reference is in `docs/API.md`.

---

## Installation

```bash
python -m venv .venv
```

```bash
# Linux / macOS
source .venv/bin/activate
```

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

```bash
pip install -e ".[dev]"
```

Python 3.10 to 3.13 is supported. Dependencies: Streamlit ≥ 1.50, pandas ≥ 2.2, NumPy ≥ 2.1,
Plotly ≥ 5.24.

---

## Usage

### Web application

```bash
streamlit run streamlit_app.py
```

Sample files are in `samples/`: one CIF, three peak lists, and one synthetic continuous scan
(`sample_tio2_anatase_scan_synthetic.xy`, 15 nm anatase, labelled as synthetic in its header).

### Python API

```python
from thanimampro_api.predict import predict_properties, scope_warnings
from thanimampro_api.schemas import SynthesisInput
from thanimampro_api.structure import analyze_structure_file

synthesis = SynthesisInput(
    temperature_c=500.0, heating_rate_c_min=5.0, annealing_time_h=2.0, atmosphere="air",
    precursor_ratio=1.0, pH=7.0, solvent_type="water", concentration_m=0.5,
    pressure_bar=1.0, milling_time_h=0.0, calcination_time_h=2.0, method="sol-gel",
    material_system="TiO2:Fe",
)
print(scope_warnings(synthesis))          # [] inside the calibrated domain
print(predict_properties(synthesis).band_gap_ev)

with open("samples/sample_tio2_anatase_scan_synthetic.xy", "rb") as handle:
    features = analyze_structure_file("scan.xy", handle.read(), instrumental_fwhm_deg=0.0)
print(features.phase, features.crystallite_size_nm, features.size_method, features.notes)
```

### Reproducing the calibration

```bash
python scripts/validate_literature_csv.py data/literature_seed.csv
```

```bash
python scripts/fit_surrogate.py
```

```bash
python scripts/evaluate_models_lopo.py
```

### Tests

```bash
pytest -q
```

---

## Calibration and Accuracy

All figures are leave-one-paper-out (LOPO) results from `scripts/fit_surrogate.py` on
`data/literature_seed.csv` (137 rows, 30 papers); R² = 1 − SSE/SST over pooled held-out predictions.

| Relation | n (rows) | Papers | MAE | R² | Constant predictor (MAE, R²) |
|---|---|---|---|---|---|
| Band gap = 3.078 − 0.000577 (T − 600) − 0.308 × doped (eV) | 76 | 19 | 0.145 eV | 0.35 | 0.186 eV, −0.08 |
| log10(BET area) = 1.597 − 0.00342 (T − 500), calcination rows | 95 | 20 | 46.5 m²/g | −0.13 | 55.8 m²/g, −0.42 |
| log10(crystallite size) = 1.234 + 0.00130 (T − 500), calcination rows | 60 | 13 | 9.0 nm | 0.18 | 10.6 nm, −0.15 |
| BET area = 6000 / (3.9 D), no fitted parameter | 55 | 10 | 33.7 m²/g | 0.48 | — |

T is the temperature in °C and D the crystallite size in nm.

XRD analysis, checked on synthetic Cu Kα scans of known size (tests in `tests/test_calibration.py`):
sizes of 5, 10, 20, 50 and 100 nm are recovered within 5%; a strain of 0.30% is recovered as 0.30%;
noise of 2% of the maximum intensity produces no spurious peak and a size error below 10%.

---

## Limitations

- **Domain.** The calibration covers TiO2 and doped TiO2 between 200 and 1,100 °C. The interface
  and `scope_warnings` report inputs outside this domain; the values returned for other materials
  are TiO2 values.
- **Band gap.** The fit explains about one-third of the held-out variance. The table mixes direct
  (32 rows), indirect (32) and other (12) Tauc analyses, which differ by up to 0.29 eV for one
  sample in one source paper. pH is reported for 27 of 137 rows, so no pH term is fitted.
- **Surface area from temperature** is no better than a constant by R². It is shown for
  orientation. The geometric relation is used when a crystallite size has been measured and is an
  upper bound (bias +24.7 m²/g), because agglomeration lowers the measured area.
- **Other properties** (conductivity, photoluminescence, active-site density, capacitance, ion
  diffusivity, Curie temperature, saturation magnetisation) are illustrative expressions without
  experimental validation and are labelled as such in the interface.
- **XRD.** Widths are measured at half maximum on a background-subtracted profile; no profile
  fitting is done, so overlapping reflections are excluded, not deconvolved. Instrumental
  broadening is removed only when the user supplies it. Kα2 is removed only when the user enables
  the Rachinger correction; enabling it on Kα1-only data biases the result. Phase matching covers
  anatase, rutile, cubic perovskite (SrTiO3) and spinel (NiFe2O4-type). The validation uses
  synthetic scans; no measured reference scan is included.
- **Literature table.** 22 of 137 rows have been compared with the source full text; open checks
  are listed in `docs/literature_search_log_v6.md`.

---

## Contributing and Support

See `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`. Defects and questions:
<https://github.com/AranCastro/ThanimamPro/issues>.

## Citation

See `CITATION.cff`.

## Licence

MIT; see `LICENSE`.
