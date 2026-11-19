# Literature dataset: hand-over note for the data curator

## 1. Purpose
ThanimamPro needs a curated table of experimental synthesis–property records. It serves two uses:
(i) the Literature tab (search and filter), and (ii) training and validating a data-driven
replacement for the surrogate. Since v6 of the table, band gap and surface area are fitted to it
(`scripts/fit_surrogate.py`); the remaining properties still use hand-set expressions. The model is only as credible as this table, so provenance and consistency matter
more than volume.

## 2. Deliverable
One UTF-8 CSV, `data/literature_seed.csv`, one row per reported sample.

| Column | Type | Unit / rule |
|---|---|---|
| `material_system` | text | Chemical formula, e.g. `TiO2`, `SrTiO3`, `NiFe2O4`; dopants in the string, e.g. `TiO2:N` |
| `method` | text | One of `sol-gel`, `hydrothermal`, `co-precipitation`, `solid-state`, `combustion`, `other` |
| `temperature_c` | number | Final calcination / reaction temperature, °C |
| `pH` | number | 0–14; leave blank if not reported (do not guess) |
| `band_gap_ev` | number | eV; leave blank if not reported |
| `surface_area_m2_g` | number | BET specific surface area, m²/g; leave blank if not reported |
| `doi` | text | Bare DOI of the source paper, e.g. `10.xxxx/yyyy` |

Template: `data/literature_template.csv` (header only).

Optional extra columns are welcome (the app ignores them): `temperature_type` (calcination | hydrothermal | combustion; validated when present), `phase`, `crystallite_size_nm`, `atmosphere`,
`calcination_time_h`, `measurement_method_band_gap` (as the authors state it), `band_gap_transition` (direct | indirect | other; required wherever a band gap is given, validated when the column is present), `notes`. Recording how
the band gap was obtained matters, because Tauc direct and indirect values for the same sample differ.

## 3. Where to obtain records
Record data only from the published paper (or a repository entry that cites it). Do not type values from memory.

| Source | Content | Access |
|---|---|---|
| Materials Project (materialsproject.org) | Computed (DFT) band gaps and structures; **not experimental** | Free API key |
| NOMAD (nomad-lab.eu) | Uploaded computational and experimental datasets | Open |
| Crystallography Open Database (crystallography.net) | Experimental crystal structures (CIF) | Open |
| Text-mined synthesis recipes (Kononova et al., *Scientific Data*, 2019) | Solid-state and sol-gel recipes extracted from papers; no property values | Open [verify DOI before citing] |
| Journal articles via Scopus / Web of Science / Google Scholar | Primary source for experimental band gap, BET and conditions | Institutional access |
| Supplementary files of review articles on the chosen material | Pre-tabulated comparisons, to be traced back to originals | Journal |

Computed (DFT) band gaps must not be mixed into `band_gap_ev` without a flag, because they
systematically underestimate experimental values. If used, add a column `value_origin` (`experimental` or `DFT`).

Suggested search string (Scopus): `TITLE-ABS-KEY("TiO2" AND ("band gap" OR "bandgap") AND ("BET" OR "surface area") AND ("sol-gel" OR hydrothermal))`.

## 4. Curation protocol
1. Fix the scope first (e.g. TiO2 and doped TiO2, four methods). Mixing unrelated systems weakens any fit.
2. One row per sample, not per paper; a paper with five calcination temperatures gives five rows.
3. Take values from tables or text; if only a figure is available, mark it in `notes` and give the digitisation tool used.
4. Keep the reported unit conversion explicit (e.g. K → °C, J/g → none). Never silently convert.
5. Leave unreported fields blank. Do not interpolate.
6. Record the DOI for every row; rows without a verifiable DOI are rejected.
7. Have a second person re-check a random 10 % of rows against the sources.
8. Target size: at least 200 rows with ≥ 20 per method for a first fit; more for any claim of generalisation.

## 5. Validation
```bash
python scripts/validate_literature_csv.py data/literature_seed.csv
```
Checks required columns, numeric ranges, DOI format, empty material names and duplicates.

## 6. Licensing and ethics
Facts (numerical values with citation) are generally reusable, but copying tables or figures verbatim
may not be. Check each publisher's terms; cite every source through the `doi` column. Retain the
list of sources searched, the date and the query string for the methods section of any paper.

## 7. What happens next
Once `data/literature_seed.csv` is in place, the Literature tab fills automatically. A trained model
additionally needs a held-out test split (by paper, not by row, to avoid leakage), reported with
MAE/RMSE, R² and a cross-validation scheme, and is then swapped in for the baseline in `thanimampro_api/predict.py`.

## 8. Contact
Questions on the schema: open an issue at https://github.com/AranCastro/ThanimamPro/issues.
