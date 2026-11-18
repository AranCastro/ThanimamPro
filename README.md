[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18648129.svg)](https://doi.org/10.5281/zenodo.18648129)

# ThanimamPro

**ThanimamPro** is an integrated data-driven synthesis–structure–property platform designed to support materials research and development. The software provides a unified workflow linking experimental synthesis parameters, structural descriptors, and predicted functional properties within an open and reproducible computational framework.

---

## Statement of Need

In materials research, synthesis parameters, crystal structure, and functional properties are often reported separately, making systematic exploration and inverse design challenging. ThanimamPro addresses this gap by providing a structured computational interface that integrates synthesis input, lightweight structural parsing, surrogate property prediction, and interactive parameter mapping within a single research workflow.

---

## Core Functionality

ThanimamPro includes:

- **Synthesis Parameter Entry Module**  
  Structured input of thermal, chemical, and processing variables.

- **Structure Analysis Module**  
  CIF/XRD parsing and derivation of structural descriptors.

- **Property Prediction Engine**  
  Baseline surrogate modelling for functional property estimation.

- **Synthesis–Property Mapper**  
  Interactive heatmaps and sensitivity exploration.

- **Inverse Design Assistant**  
  Property-targeted parameter suggestion.

- **Literature Dataset Interface**  
  Searchable seed dataset for exploratory modelling.

---

## Installation

### Create environment
```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### Install dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

---

## Usage

### Web application
```bash
streamlit run streamlit_app.py
```
The interface has a quick-start preset picker, live results with a light-absorption window, a
sensitivity (tornado) chart, selectable-property heatmap / 3D maps with a current-conditions marker,
inverse design with one-click "apply to sidebar", saved-scenario comparison, and Markdown / JSON report
export.
Sample structure files are provided in `samples/` (CIF, XRD, XY and text formats).
The Literature Database tab reads `data/literature_seed.csv` (columns: `material_system`,
`method`, `temperature_c`, `pH`, `band_gap_ev`, `surface_area_m2_g`, `doi`); the tab shows an
empty table until that file is supplied.

### Python API
```python
from thanimampro_api.schemas import SynthesisInput
from thanimampro_api.predict import predict_properties

synthesis = SynthesisInput(
    temperature_c=650.0, heating_rate_c_min=5.0, annealing_time_h=2.0, atmosphere="air",
    precursor_ratio=1.0, pH=7.0, solvent_type="water", concentration_m=0.5,
    pressure_bar=1.0, milling_time_h=2.0, calcination_time_h=2.0, method="sol-gel",
)
print(predict_properties(synthesis).to_dict())
```

### Tests
```bash
pip install -e ".[dev]"
pytest -q
```

---

## Limitations

- The property predictor is an illustrative baseline surrogate with hand-set coefficients; it is not
  fitted to experimental data. Only temperature, pH, pressure and the structural descriptors affect
  its output.
- For continuous XRD scans (≥ 50 points, Cu Kα1, λ = 1.5406 Å) crystallite size and microstrain come from
  Williamson–Hall (≥ 3 peaks) or Scherrer (K = 0.9) fits without instrumental-broadening correction, so sizes
  are lower bounds. For peak lists and CIF files they are peak-count and keyword heuristics, and the
  interface labels which method was used. Phase identification matches peaks against a small reference table
  (anatase, rutile, cubic perovskite, spinel).
- The `ugp` subpackage (Unified Geothermobarometry Platform, command `ugp`) is a separate scaffold whose
  calculator engines are placeholders and return fixed demonstration values flagged `not-implemented`.

## Licence

MIT; see `LICENSE`.
