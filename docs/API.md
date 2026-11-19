# ThanimamPro API reference

Units: temperature in °C, lengths in nm (crystallite size) or Å (lattice parameters), band gap in
eV, surface area in m²/g, 2θ in degrees for Cu Kα radiation.

## `thanimampro_api.schemas`

| Object | Purpose |
|---|---|
| `SynthesisInput` | Synthesis conditions. Raises `ValueError` for non-finite numbers, temperature outside 0–3,000 °C, pH outside 0–14, negative times, pressure or concentration, non-positive precursor ratio, or an unknown method. |
| `SYNTHESIS_METHODS` | `sol-gel`, `hydrothermal`, `co-precipitation`, `solid-state`, `combustion`, `other`. |
| `StructureFeatures` | Descriptors from a structure file. `lattice_a/b/c`, `crystallite_size_nm`, `microstrain_pct` and `defect_index` are `None` when not determined. `size_method` is `Williamson-Hall`, `Scherrer` or `none`; `n_peaks` and `n_peaks_used` count detected and resolved peaks; `notes` explains every absent value. |
| `PredictedProperties` | Ten outputs. `CALIBRATED_PROPERTIES` lists the three fitted to data; the rest are illustrative. The two magnetic outputs are `None` for systems without Fe, Co, Ni, Mn, Cr or Gd. |
| `DesiredPropertyTargets` | Target band gap, minimum surface area, maximum crystallite size; validated. |

## `thanimampro_api.structure`

| Function | Returns |
|---|---|
| `analyze_structure_file(filename, content, instrumental_fwhm_deg=0.0, strip_ka2=False)` | `StructureFeatures`. Lattice parameters from CIF tags; for continuous scans (≥ 50 points, step ≤ 0.1°) phase, crystallite size and, where supported, microstrain. |
| `detect_peaks(rows, strip_ka2=False)` | List of `Peak(two_theta, intensity, fwhm, resolved)`. |
| `scherrer_williamson_hall(peaks, instrumental_fwhm_deg=0.0)` | `(size_nm, strain_pct or None, method, peaks_used)` or `None`. |
| `match_phases(two_thetas, tol=0.35)` | Reference phases with at least three matched reflections and 50% coverage, best first. |
| `read_pattern(text)` | `(2θ, intensity)` rows from two-column numeric text. |

Constants: `CU_KA1_ANGSTROM = 1.540562`, `CU_KA2_ANGSTROM = 1.544390`, `SCHERRER_K = 0.9`,
`MIN_WH_PEAKS = 4`, `REFERENCE_PEAKS`. The algorithm is described step by step in the module
docstring.

## `thanimampro_api.predict`

| Function | Returns |
|---|---|
| `predict_properties(synthesis, structure=None)` | `PredictedProperties`. Coefficients and held-out errors are module constants. |
| `scope_warnings(synthesis)` | List of reasons why the input is outside the calibrated domain (empty inside it). |
| `estimate_crystallite_size_nm(temperature_c)` | Literature fit of crystallite size to calcination temperature. |
| `is_doped(material_system)`, `is_supported_material(material_system)` | Dopant convention `TiO2:Fe`; supported base material `TiO2`. |

## `thanimampro_api.inverse`

| Function | Returns |
|---|---|
| `suggest_synthesis_conditions(baseline, desired, structure=None, top_k=5)` | Calcination temperatures ranked by score, each with `band_gap_error_ev`, `meets_all_targets` and `target_reachable`. |
| `reachable_band_gap_range(baseline, structure=None)` | Minimum and maximum band gap over the calibrated temperature range. |

## `thanimampro_api.mapper` and `thanimampro_api.sensitivity`

| Function | Returns |
|---|---|
| `build_property_map(baseline, structure, temp_min, temp_max, ph_min, ph_max, points=25, prop="band_gap_ev")` | DataFrame with `temperature_c`, `pH`, `value`. |
| `build_bandgap_map(...)` | Same, with the value column named `band_gap_ev`. |
| `one_at_a_time(synthesis, structure, prop="band_gap_ev")` | Change in a property for ±50 °C, ±1 pH unit and ±10% pressure. |

## `thanimampro_api.database`

| Function | Returns |
|---|---|
| `load_literature_data(csv_path)` | DataFrame with the standard columns; empty if the file is absent. |
| `search_literature(frame, material_system="", method="", min_band_gap=None, max_band_gap=None)` | Filtered DataFrame; text filters are literal, case-insensitive substrings. |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/validate_literature_csv.py` | Column, range, DOI-format and category checks for the literature table. |
| `scripts/fit_surrogate.py` | Fits the calibrated relations and reports leave-one-paper-out errors. |
| `scripts/evaluate_models_lopo.py` | Compares constant, per-method and ridge models; the ridge penalty is chosen inside each training fold. |
| `scripts/benchmark_surrogate.py` | In-sample comparison of the shipped surrogate with the table. |
