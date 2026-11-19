# Changelog

## 0.2.0 (19 November 2026)

Changes follow the audit recorded in `CLAUDE-OUTPUTS/thanimampro/`.

### Changed
- **Predictor.** Band gap, surface area and crystallite size are fitted to the literature table
  (`scripts/fit_surrogate.py`) and reported with leave-one-paper-out errors. The band gap responds
  to temperature and to doping (`TiO2:Fe`); pH no longer affects it. Version 0.1.1 used hand-set
  coefficients and returned the same values for every material.
- **Structure analysis.** Crystallite size and microstrain come from measured line widths
  (Scherrer, Williamson–Hall), with optional Kα2 stripping and instrumental-width correction.
  Descriptors that a file does not determine are `None`. Version 0.1.1 derived them from a count of
  numbers in the file and substituted anatase lattice parameters.
- **Inverse search** runs over calcination temperature and reports whether the target is attainable.
- **Scope.** The software is restricted to TiO2 and doped TiO2; inputs outside the calibrated
  domain raise warnings.
- Curie temperature and saturation magnetisation are returned only for systems that contain a
  magnetic cation.
- Minimum Streamlit version is 1.50; dependencies carry upper bounds on the major version.

### Added
- Literature table `data/literature_seed.csv` (137 rows, 30 papers), validator, search logs.
- Scripts for fitting, benchmarking and leave-one-paper-out model comparison.
- Redesigned interface: presets, sensitivity chart, property maps, scenario comparison, report export.
- Input validation in all record types; `scope_warnings`; `reachable_band_gap_range`.
- 39 tests; lint, table validation and package build in continuous integration (Python 3.10–3.13).
- `docs/API.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.

### Removed
- The `ugp` geothermobarometry scaffold, which was unrelated to the package and held placeholder
  engines. It remains available in the git history and in tag `v0.1.1`.
- Tracked bytecode files.

### Breaking changes for users of 0.1.1
- `StructureFeatures` fields may be `None`; `PredictedProperties.curie_temperature_k` and
  `saturation_magnetization_emu_g` may be `None`.
- `suggest_synthesis_conditions` returns different keys (`estimated_crystallite_size_nm`,
  `band_gap_error_ev`, `meets_all_targets`, `target_reachable`) and no longer varies pH or time.

## 0.1.1 (15 February 2026)

First archived release (https://doi.org/10.5281/zenodo.18648129).
