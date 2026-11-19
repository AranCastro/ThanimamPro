# ThanimamPro: Resolution of Audit Findings

**Date:** 19 November 2026
**Refers to:** `thanimampro_audit-report_v1.md` (same folder)
**Branch:** `claude/adoring-davinci-mnzy0a`, which contains the commits of draft pull request #1 and the changes described here
**Verification:** 42 tests passed; `ruff check .` clean; literature validator 0 errors; package builds; the Streamlit application was run headlessly with every control exercised and raised no exception (Python 3.13.18, pandas 3.0.5, NumPy 2.5.3, Streamlit 1.67.0, Plotly 7.1.0)

Status codes: **Fixed**; **Partly fixed** (the limit is stated); **Not changed** (a decision or an action outside the repository is needed).

## 1. Findings on `main` (Table 2 of the report)

| ID | Status | Resolution |
|---|---|---|
| M1 | Partly fixed | Band gap and surface area are now fitted to the literature table and respond to temperature and to doping (`TiO2:Fe`). Held-out band-gap MAE fell from 0.314 eV to 0.145 eV (R² from −1.43 to 0.35; n = 76 rows, 19 papers). `scope_warnings` and the interface state when the material is not TiO2 or the temperature is outside 200–1,100 °C. Seven other properties remain illustrative and are labelled so. Ten synthesis inputs still have no effect because the table gives no basis for them. |
| M2 | Fixed | The count-based size, strain and defect rules are removed. Size and strain are reported only from measured line widths; otherwise the field is empty with a reason. |
| M3 | Fixed | No default lattice parameters. Without CIF cell tags the fields are empty. |
| M4 | Fixed | The search runs over calcination temperature only, returns no duplicates, and marks each row with `target_reachable` and `meets_all_targets`. The interface warns for an unattainable band gap and for conflicting targets. The particle-size expression is replaced by a crystallite-size fit to the table (n = 60 rows, 13 papers; held-out MAE 9.0 nm). |
| M5–M9 | Fixed | From pull request #1. The README is rewritten for the present code. |
| M10 | Partly fixed | `pyproject.toml` and `thanimampro_api/__init__.py` read 0.2.0.dev0; `CITATION.cff` keeps 0.1.1, the archived release. The two tags on one commit are not changed. |
| M11 | Partly fixed | Faults fixed and tested (pull request #1). The engines remain placeholders and the package remains in this repository. |
| M12 | Fixed | 42 tests, including XRD accuracy on synthetic scans and a test that refits the shipped table and compares the result with the constants in the code. |
| M13 | Fixed | From pull request #1. |
| M14 | Fixed | The workflow runs on Python 3.10–3.13 for every pull request, with lint, table validation, tests and a package build, and declares read-only permissions. |
| M15 | Fixed | `DesiredPropertyTargets` is validated. |
| M16 | Fixed | Curie temperature and saturation magnetisation are returned only for systems that contain Fe, Co, Ni, Mn, Cr or Gd. |
| M17 | Partly fixed | `pyproject.toml` names the author. `LICENSE` is not changed. |

## 2. Findings on pull request #1 (Table 3 of the report)

| ID | Status | Resolution |
|---|---|---|
| B1 | Fixed for band gap; partly for surface area | See M1. The temperature relation for surface area has a held-out MAE of 46.5 m²/g against 55.8 m²/g for a constant, but R² = −0.13 (n = 95 rows, 20 papers). When a crystallite size is measured, the geometric relation is used (MAE 33.7 m²/g, R² 0.48, bias +24.7 m²/g; n = 55 rows, 10 papers). |
| B2 | Fixed | A true 10 nm scan returns 9.93 nm (Table 1 below). Overlapping reflections are excluded. |
| B3 | Fixed | Strain is reported only from a Williamson–Hall fit whose slope exceeds twice its standard error. Noise of 2% of the maximum yields six peaks of six, and no strain. |
| B4 | Fixed | Optional Rachinger Kα2 removal and an instrumental-width input. The README no longer states that sizes are lower bounds. |
| B5 | Partly fixed | Mixtures are reported (`rutile + anatase`) and sized on the best-matched phase. The reference list still holds four phases; others are reported as unknown. |
| B6 | Fixed | The parser sets no defect index. The user may supply one; it affects only illustrative properties. |
| B7 | Fixed | The presets are TiO2 and Fe-doped TiO2 only. |
| B8 | Partly fixed | New column `band_gap_transition` (direct 32, indirect 32, other 12), validated. The band-gap fit still pools the classes. |
| B9 | Partly fixed | The calibrated relations use no pH term, and the surface-area and crystallite-size fits use calcination rows only. The missing pH values themselves are a property of the sources. |
| B10 | Not changed | The DOI is flagged in `notes`. The journal site returned HTTP 503, so the correct DOI could not be established. |
| B11 | Fixed | The ridge penalty is chosen by an inner leave-one-paper-out loop. With it, ridge reaches R² = 0.08 for band gap. |
| B12 | Fixed | User text is escaped before it enters markup; confirmed with the input `<b>ZnO</b>`. |
| B13 | Fixed | Docstrings rewritten. |
| B14 | Fixed | The hydrothermal ageing step is recorded in `notes`; the class stays sol-gel, as the authors describe it. |
| B15 | Partly fixed | The paper now describes this branch. The earlier pull request was not split. |

## 3. Paper and publication (Table 7 of the report)

| ID | Status | Resolution |
|---|---|---|
| J1 | Fixed | Citations use `[@key]`; all 14 keys exist in `paper.bib`. Eleven entries were generated from Crossref records. |
| J2 | Fixed, with two author statements pending | The four sections are added. The research impact statement and the AI usage disclosure each contain a bracketed line that only the author can complete. |
| J3 | Fixed | The body is 1,229 words. |
| J4 | Fixed | Unsupported statements removed. |
| J5 | Not changed | Development history cannot be created retrospectively. |
| J6 | Partly fixed | The statement reports the benchmark and validation as they stand. No external use is recorded in the repository. |
| J7 | Fixed | NumPy, pandas, Plotly and Streamlit are cited. |
| J8 | Fixed | `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` and `docs/API.md` added. |

Section 6 of the report: dependencies now carry upper bounds on the major version.

## 4. XRD validation after the changes

**Table 1.** Crystallite size returned for synthetic anatase scans (six reflections, 10–80° 2θ, step 0.02°, Gaussian profiles unless stated; n = 1 scan per case). The second column repeats the values in Table 4 of the report.

| Case | True size (nm) | Before (nm) | After (nm) | Error after (%) | Strain after (%) | Method |
|---|---|---|---|---|---|---|
| Clean | 5 | not tested | 4.81 | −3.8 | none | Scherrer |
| Clean | 10 | 25.56 | 9.93 | −0.7 | none | Scherrer |
| Clean | 20 | 20.01 | 19.74 | −1.3 | none | Scherrer |
| Clean | 50 | 50.15 | 49.40 | −1.2 | none | Scherrer |
| Clean | 100 | 101.26 | 98.83 | −1.2 | none | Scherrer |
| Lorentzian profile | 20 | 20.37 | 19.57 | −2.2 | none | Scherrer |
| Strain 0.30% | 20 | 21.72 | 19.77 | −1.2 | 0.301 | Williamson–Hall |
| Noise, σ = 0.5% of maximum | 20 | 20.39 | 19.88 | −0.6 | none | Scherrer |
| Noise, σ = 2% of maximum | 20 | 21.64 | 20.46 | +2.3 | none | Scherrer |
| Noise, σ = 5% of maximum | 20 | not tested | 21.31 | +6.6 | none | Scherrer |
| Kα2 present, stripping enabled | 50 | 64.19 (no stripping available) | 49.35 | −1.3 | none | Scherrer |
| Instrumental width 0.1°, supplied | 50 | not tested | 48.58 | −2.8 | none | Scherrer |
| Step 0.05° | 20 | 19.90 | 19.90 | −0.5 | none | Scherrer |

Two misuse cases remain inaccurate and are stated in the interface notes: Kα2 present with stripping disabled (62.28 nm for a true 50 nm, with a spurious strain of 0.099%), and stripping enabled on Kα1-only data (56.23 nm for a true 50 nm).

## 5. Items that need the author

1. **Pull request #1.** Its commits are included in this branch. It can be closed in favour of this one.
2. **`ugp`.** Decide whether it moves to its own repository. It was not removed.
3. **Paper.** Complete the two bracketed author statements and the funding line. The JOSS requirement of six months of public development history with releases and issues (J5) is not met by the present history.
4. **Release.** Tag a new version after merging, so that Zenodo, `CITATION.cff` and the paper refer to the same code; then update `CITATION.cff`.
5. **Dataset.** Confirm DOI 10.22052/JNS.2020.03.017 on the journal page; 115 of 137 rows are still unchecked against their sources.
6. **Measured scan.** The XRD validation uses synthetic data. A measured scan of a reference material with a known instrumental width would complete it.
7. **`LICENSE`.** The copyright holder reads "ThanimamPro contributors"; change it only if that is not intended.
