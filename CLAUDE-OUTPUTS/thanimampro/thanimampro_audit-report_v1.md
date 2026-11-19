# ThanimamPro: Technical, Scientific and Publication Audit

**Repository:** AranCastro/ThanimamPro
**Date of audit:** 19 November 2026
**Revisions examined:** `main` at `dc0c5f7`; open draft pull request #1 (`claude/practical-cerf-6ppjhi` at `a1b15cf`)
**Environment:** Python 3.13.18, pandas 3.0.5, NumPy 2.5.3, Streamlit 1.67.0, Plotly 7.1.0, pytest 9.1.1

---

## Summary

The audit covered every tracked source file on `main` (about 1,400 lines) and the unmerged draft pull request #1, which already contains an earlier audit-and-fix pass, a redesigned interface, an X-ray diffraction (XRD) analysis routine and a 137-row literature dataset. Each suspected defect was reproduced by execution; nothing is reported from reading alone unless stated.

On `main`, the application starts and both tests pass, but the scientific content does not support the claims made in the README and the paper. The property predictor returns identical values for every material, ten of the thirteen synthesis inputs have no effect, and the structural descriptors are produced by counting decimal numbers in the uploaded file. The literature dataset advertised in the README and paper is absent. Seventeen defects were confirmed (three high, eight medium, six low).

Pull request #1 resolves thirteen of the seventeen and partly resolves the remaining four. It also adds evidence that the predictor has no skill: against the branch's own dataset the band-gap surrogate has a mean absolute error (MAE) of 0.314 eV, against 0.177 eV for a constant predictor (n = 76 rows, 19 papers). The new Williamson–Hall routine recovers crystallite sizes of 20–100 nm within 1.3% on clean synthetic scans but returns 25.6 nm for a true 10 nm sample. Of the 30 dataset DOIs, 29 resolve; 22 rows from seven papers were checked against the source full text and all agreed.

The paper (`paper/paper.md`) does not meet the current Journal of Open Source Software (JOSS) format: four required sections are missing, the body is 423 words against a 750–1,750 range, and the citations use LaTeX syntax that JOSS does not render.

---

## 1. Scope and Method

The audit addressed five questions: whether the code runs, whether it computes what it states, whether the data are traceable, whether the documentation and paper match the code, and whether the repository is in a publishable state. Table 1 lists the procedures.

**Table 1.** Audit procedures and the evidence each produced.

| No. | Procedure | Evidence |
|---|---|---|
| 1 | Full read of all source, test, sample, packaging, workflow and paper files on `main` and on pull request #1 | Line-referenced findings |
| 2 | Test suites executed on both revisions | `main`: 2 passed; pull request #1: 20 passed |
| 3 | Behavioural script exercising every public function with ordinary, boundary and malformed inputs | Reproduced outputs quoted in Tables 2 and 3 |
| 4 | Headless run of both Streamlit applications (`streamlit.testing.v1.AppTest`), with every enabled button clicked | No exceptions on either revision |
| 5 | Synthetic XRD scans with known crystallite size and strain (Cu Kα1, λ = 1.5406 Å, Scherrer K = 0.9) passed through the branch's analysis routine | Table 4 |
| 6 | The branch's own benchmark and leave-one-paper-out scripts executed | Table 5 |
| 7 | All 30 dataset DOIs queried at the Crossref REST API, with doi.org as fallback | Table 6 |
| 8 | Seven source papers retrieved as full text (six as XML from Europe PMC, one from the publisher page) and compared with 22 dataset rows | Table 6 |
| 9 | JOSS paper-format and review-criteria pages and the Zenodo record read on the audit date | Section 5 |
| 10 | Search of tracked files for credentials and unsafe constructs | Section 6 |

Severity is graded as follows. **High:** the output is scientifically wrong or a published claim is unsupported. **Medium:** a function fails, misleads, or blocks reproducibility under ordinary use. **Low:** maintenance, consistency or presentation.

---

## 2. Repository State

The `main` branch holds ten commits, all dated 15 February 2026. Tags `v0.1.0` and `v0.1.1` both point to commit `d0d5240`, in which `pyproject.toml` declares version 0.1.0. The Zenodo record (DOI 10.5281/zenodo.18648129) is labelled v0.1.1 and dated 15 February 2026, so the archived release predates the later edits to `README.md`, `CITATION.cff`, `paper/` and the upload of sample files.

Pull request #1 was opened on 18 November 2026 and remains an unmerged draft. It changes 62 files (+2,157 / −282 lines) in eight commits and its continuous-integration runs pass. Because it is unmerged, every finding in Section 3 is still present on the default branch that a reader, a reviewer or the Zenodo archive sees.

The repository contains two unrelated packages. `thanimampro_api` (about 370 lines on `main`) is the materials platform. `ugp` (about 330 lines) is a "Unified Geothermobarometry Platform" scaffold that the README and the paper do not mention.

---

## 3. Findings on `main`

**Table 2.** Confirmed defects on `main` (`dc0c5f7`) and their status in pull request #1.

| ID | Severity | Finding and reproduced evidence | Location | Status in PR #1 |
|---|---|---|---|---|
| M1 | High | The predictor ignores the material. TiO2, ZnO, SrTiO3, NiFe2O4 and Si all return a band gap of 3.1475 eV, a Curie temperature of 485 K and a saturation magnetisation of 24.4 emu/g. Of the 13 synthesis inputs, only temperature (nine outputs), pH (seven) and pressure (one) change any output; the other ten change none. Coefficients are hand-set and carry no source. | `thanimampro_api/predict.py:24-64` | Disclosed in the docstring, README and interface; behaviour unchanged |
| M2 | High | Crystallite size, microstrain and defect index are functions of the count of decimal numbers in the file (`size = max(6, 60 − 0.9N)`). The three cell lengths in the sample CIF are counted as peaks (57.3 nm). Scans of 300 and of 3,000 points both saturate at 6.0 nm, 2.5% strain and defect index 1.0. | `thanimampro_api/structure.py:43-50` | Replaced for continuous scans (≥ 50 points); the count-based rule remains for peak lists and CIF files and is labelled "heuristic" |
| M3 | High | Files without CIF cell tags receive anatase lattice parameters (a = b = 3.78 Å, c = 9.45 Å) without notice. The spinel and perovskite samples supplied in `samples/` are both reported with these values. | `thanimampro_api/structure.py:38-40` | Flagged in the `source` text; the anatase values are still displayed as metrics |
| M4 | Medium | Inverse design returns duplicates: the first eight candidates are all 850 °C, pH 11, differing only in annealing and calcination time, which the predictor does not use. The ranking is identical for any baseline. The grid spans 2.69–3.61 eV, so the default 2.5 eV target is unreachable and no warning is given. | `thanimampro_api/inverse.py:24-55` | Duplicates removed; unreachable targets still return silently |
| M5 | Medium | The heat map raises `ValueError: Index contains duplicate entries` when the temperature or pH slider is collapsed to a single value. | `thanimampro_api/mapper.py:20-21`, `streamlit_app.py:179` | Fixed |
| M6 | Medium | `data/literature_seed.csv` does not exist, so the Literature tab is always empty although the README and the paper describe a searchable seed dataset. | `streamlit_app.py:21` | Dataset added (Section 4.3) |
| M7 | Medium | The literature filter treats user text as a regular expression; the input `(` raises `ArrowInvalid`. The default 0–6 eV filter drops every row with a missing band gap. | `thanimampro_api/database.py:34-40` | Fixed |
| M8 | Medium | `README.md` ends inside an unclosed code block after `python -m venv .venv`; it contains no installation command, usage, or test instructions. | `README.md:41-43` | Fixed |
| M9 | Medium | Twenty-five `.pyc` files are tracked and there is no `.gitignore`. Two of them (`streamlit_app/__pycache__/app.cpython-314.pyc`, `tests/__pycache__/test_synthesispro.cpython-314.pyc`) correspond to source files that are not in the repository. | repository root | Fixed |
| M10 | Medium | Version numbers disagree: `pyproject.toml` 0.1.0, `thanimampro_api/__init__.py` 0.1.0, `CITATION.cff` 0.1.1; both release tags point to the same commit. | see Section 2 | Files aligned at 0.1.1; tags unchanged |
| M11 | Medium | `ugp`: the three engines return hard-coded pressure–temperature pairs; bootstrap over these constants reports a standard deviation of 0; the base result is computed and discarded; `UGPConfig.default_engine` is ignored; engines are unregistered unless `ugp.engines` is imported (`KeyError`); `--iterations 0` raises `StatisticsError`; the package is not installed by `pyproject.toml` and has no tests. | `ugp/` | Faults fixed and tested; the engines remain placeholders and the package is now installed with a `ugp` command |
| M12 | Low | Two tests exist. Nothing covers the structure parser, the mapper, the literature module, `ugp` or the application. | `tests/` | 20 tests |
| M13 | Low | Six calls use `use_container_width`, which Streamlit 1.67.0 reports as scheduled for removal after 31 December 2025. The calls still work in 1.67.0. | `streamlit_app.py:157-234` | Removed |
| M14 | Low | Continuous integration covers Python 3.10 and 3.11 only, runs on `main` only, and has no lint or build step. | `.github/workflows/python.yml` | 3.12 and 3.13 added |
| M15 | Low | The dataclasses accept any value (NaN, pH 15, an unknown method). | `thanimampro_api/schemas.py` | `SynthesisInput` and `StructureFeatures` validated; `DesiredPropertyTargets` is not (a NaN target yields a NaN score) |
| M16 | Low | Curie temperature and saturation magnetisation are reported for non-magnetic oxides; the unit in `active_site_density_mm2_g` is undefined. | `thanimampro_api/schemas.py:58` | Unit relabelled "a.u."; magnetic outputs remain |
| M17 | Low | Authorship is inconsistent: `LICENSE` and `pyproject.toml` name "ThanimamPro contributors", `CITATION.cff` names the author. | `LICENSE`, `pyproject.toml` | `pyproject.toml` corrected |

Two coefficients in the predictor can be compared with data already in the branch. The surrogate lowers the band gap by 0.0012 eV per °C; Kim et al. (2021, Table 3) report 3.05 eV at 300 °C and 2.98 eV at 1,100 °C, a slope of about 0.00009 eV per °C, one-thirteenth of the surrogate value. The inverse-design particle-size expression (`80 − 0.07T + 1.2t − 1.8pH`) decreases with temperature, whereas the same paper (Table 1) reports rutile crystallite size rising from 10.7 nm at 300 °C to 77.6 nm at 1,100 °C.

---

## 4. Findings Specific to Pull Request #1

**Table 3.** Defects and limitations introduced by, or remaining in, pull request #1 (`a1b15cf`).

| ID | Severity | Finding and reproduced evidence | Location |
|---|---|---|---|
| B1 | High | The surrogate is less accurate than a constant. Band gap: MAE 0.314 eV, bias +0.298 eV, against 0.177 eV for the mean (Table 5). The interface still shows surrogate values as the four headline metrics, with a disclaimer above them. | `thanimampro_api/predict.py`, `streamlit_app.py:218-232` |
| B2 | High | Williamson–Hall analysis fails at small sizes. A clean synthetic anatase scan with a true size of 10 nm and zero strain returns 25.56 nm and 0.91% strain (Table 4). The broadened 53.89° and 55.06° reflections merge and distort the fit. | `thanimampro_api/structure.py:70-123` |
| B3 | Medium | When the routine falls back to Scherrer, the microstrain shown is still the peak-count heuristic, but the interface labels the method "Scherrer". With Gaussian noise of 2% of the maximum intensity, 18 peaks are detected where six exist, and the reported strain is 2.5%. | `structure.py:174-188`, `streamlit_app.py:316-321` |
| B4 | Medium | Kα2 is not stripped. A 50 nm scan with a Kα2 component at half intensity returns 64.19 nm (+28%). The README states that sizes are lower bounds; rows B2 and B4 are both overestimates. | `structure.py:102-123`, `README.md` (Limitations) |
| B5 | Medium | Phase identification returns one label from four reference phases. An equal anatase–rutile mixture is reported as "rutile". A ZnO scan is reported as "mixed/unknown" with anatase lattice parameters. | `structure.py:55-60, 125-132` |
| B6 | Medium | The defect index (`0.1 + 0.12 × keyword hits + 0.02 × peaks`) has no physical basis yet enters nine of the ten predicted properties. | `structure.py:196-198` |
| B7 | Medium | The quick-start presets include ZnO, SrTiO3 and NiFe2O4. Because of M1, they produce TiO2-centred values under another material's name. | `streamlit_app.py:70-76` |
| B8 | Medium | The band-gap column mixes measurement methods: 41 indirect Tauc, 26 direct Tauc and nine other. Within single papers the methods differ by 0.06–0.07 eV (Kim et al., 2021) and by up to 0.29 eV for one sample (Mancuso et al., 2021: 2.74 eV and 3.03 eV). The standard deviation of the whole column is 0.25 eV. | `data/literature_seed.csv` |
| B9 | Medium | pH is present in 27 of 137 rows and absent for all sol-gel and combustion rows. `temperature_c` combines calcination (113 rows), hydrothermal (14) and combustion (10) temperatures. The benchmark substitutes pH 7 for the 110 missing values. | `data/literature_seed.csv`, `scripts/benchmark_surrogate.py:26` |
| B10 | Medium | DOI 10.22052/JNS.2020.03.017 (three rows) returns HTTP 404 at both Crossref and doi.org. | `data/literature_seed.csv` |
| B11 | Low | The ridge penalty is reported for three values and the best is read off the held-out results, so R² = 0.14 is optimistic. | `scripts/evaluate_models_lopo.py:72-73` |
| B12 | Low | `material_system` is interpolated into markup rendered with `unsafe_allow_html=True`. Markup typed into that field is rendered in the user's own session. Script execution was not tested. | `streamlit_app.py:193-199` |
| B13 | Low | The docstring of `analyze_structure_file` still states that the results are not Scherrer or Williamson–Hall values. | `structure.py:153-160` |
| B14 | Low | Mancuso et al. (2021) is classed as sol-gel; the source describes a 98 °C, 48 h hydrothermal step before calcination. | `data/literature_seed.csv` |
| B15 | Low | The pull request combines defect fixes, an interface redesign, a new analysis method and a dataset. `paper/paper.md` and `CITATION.cff` are unchanged, so the paper describes neither revision accurately. | pull request #1 |

### 4.1 XRD analysis validation

**Table 4.** Crystallite size returned by the pull-request routine for synthetic anatase scans (six reflections, 10–80° 2θ, step 0.02°, Gaussian profiles unless stated; n = 1 scan per case).

| Case | True size (nm) | True strain (%) | Returned size (nm) | Error (%) | Returned strain (%) | Method reported |
|---|---|---|---|---|---|---|
| Clean | 20 | 0 | 20.01 | +0.1 | 0.000 | Williamson–Hall |
| Clean | 50 | 0 | 50.15 | +0.3 | 0.001 | Williamson–Hall |
| Clean | 100 | 0 | 101.26 | +1.3 | 0.003 | Williamson–Hall |
| Clean | 10 | 0 | 25.56 | +156 | 0.910 | Williamson–Hall |
| Lorentzian profile | 20 | 0 | 20.37 | +1.9 | 0.013 | Williamson–Hall |
| Strained | 20 | 0.30 | 21.72 | +8.6 | 0.359 | Williamson–Hall |
| Noise, σ = 0.5% of maximum | 20 | 0 | 20.39 | +2.0 | 0.820 (heuristic) | Scherrer |
| Noise, σ = 2% of maximum | 20 | 0 | 21.64 | +8.2 | 2.500 (heuristic) | Scherrer |
| Kα2 present | 50 | 0 | 64.19 | +28 | 0.099 | Williamson–Hall |
| Step 0.05° | 20 | 0 | 19.90 | −0.5 | 0.220 (heuristic) | Scherrer |

The routine is accurate for well-separated peaks at 20 nm and above. It is not reliable below about 15 nm, which is the range of most entries in the branch's own dataset (median reported crystallite size 17 nm, n = 68).

### 4.2 Predictive skill

**Table 5.** Output of `scripts/benchmark_surrogate.py` and `scripts/evaluate_models_lopo.py` on `data/literature_seed.csv` (leave-one-paper-out; R² = 1 − SSE/SST over pooled held-out predictions).

| Target | n (rows) | Papers | Model | MAE | RMSE | R² |
|---|---|---|---|---|---|---|
| Band gap (eV) | 76 | 19 | Constant (training mean) | 0.186 | 0.261 | −0.08 |
| | | | Per-method mean | 0.179 | 0.259 | −0.07 |
| | | | Ridge, α = 30 | 0.163 | 0.233 | 0.14 |
| | | | Hand-set surrogate | 0.314 | 0.391 | −1.43 |
| BET surface area (m²/g) | 115 | 24 | Constant (training mean) | 60.1 | 77.7 | −0.44 |
| | | | Per-method mean | 58.3 | 67.3 | −0.08 |
| | | | Ridge, α = 30 | 46.3 | 61.7 | 0.09 |
| | | | Hand-set surrogate | 52.5 | 61.5 | 0.09 |

The surrogate's band-gap correlation with the observations is r = +0.42 (permutation p = 0.0001, 10,000 shuffles, seed 0); the script notes that rows from one paper are not independent, so this p-value is optimistic. No model in the repository explains more than 14% of held-out variance. The ridge MAE for band gap (0.163 eV) is of the same order as the between-method spread recorded in B8, which limits what any model fitted to this column can achieve.

### 4.3 Literature dataset verification

**Table 6.** Verification of `data/literature_seed.csv` (137 rows, 30 DOIs).

| Check | Result |
|---|---|
| Validator (`scripts/validate_literature_csv.py`) | 0 errors, 0 warnings |
| Exact duplicate rows | 0 |
| DOIs registered at Crossref with a TiO2 title matching the row content | 27 of 30 |
| DOIs not at Crossref but resolving at doi.org | 2 (10.14456/cast.1477.4, via the Thai registrar; 10.30495/ijc.2022.1941684.1875) |
| DOIs that do not resolve | 1 (10.22052/JNS.2020.03.017) |
| Rows compared with source full text | 22 rows from seven papers |
| Numeric values in agreement (band gap, BET area, crystallite size, temperature, time, pH, phase fractions) | 22 of 22 rows |

The seven papers checked were Kim et al. (2021), Tang et al. (2021), Mancuso et al. (2021), Wang et al. (2018), Soni et al. (2022), Safeen et al. (2022) and Lontio Fomekong et al. (2019). Six were read as XML from Europe PMC and parsed locally, which is independent of the summarising tool used when the dataset was compiled. The remaining 115 rows were not checked in this audit, and the open items in section 4 of `docs/literature_search_log_v5.md` still stand.

---

## 5. Paper and Publication Readiness

The JOSS paper-format page (read on 19 November 2026) requires six sections: Summary, Statement of need, State of the field, Software design, Research impact statement and AI usage disclosure. It specifies a length of 750–1,750 words and Pandoc citation syntax (`[@key]`). Table 7 compares `paper/paper.md` with these requirements and with the code.

**Table 7.** Paper and publication findings (identical on `main` and pull request #1).

| ID | Severity | Finding |
|---|---|---|
| J1 | High | Citations are written as `\cite{key}` (lines 30 and 64). JOSS requires `[@key]`; the present form will not produce citations. |
| J2 | High | Four required sections are absent: State of the field, Software design, Research impact statement and AI usage disclosure. The last is directly relevant, since the commits in pull request #1 carry an AI co-author trailer. |
| J3 | High | The body is 423 words; the stated range is 750–1,750. |
| J4 | High | Statements not supported by `main`: "literature seed dataset search" (no dataset, M6); "CIF/XRD upload with descriptor extraction" (M2, M3); "public deployment via Streamlit Community Cloud" (no deployment URL in the repository); "automated testing across supported Python versions" (two tests, M12). |
| J5 | Medium | The JOSS review criteria screen for at least six months of public development history with releases and public issues or pull requests. All ten commits on `main` are dated 15 February 2026, and the only pull request is the unmerged draft. |
| J6 | Medium | The research impact statement must rest on realised use or concrete near-term evidence. Table 5 is the only quantitative evidence in the repository and it is unfavourable to the predictor. |
| J7 | Low | `paper.bib` cites pandas 1.0.0 (2020) while the package requires pandas ≥ 2.2; NumPy and Plotly are dependencies and are not cited; the Streamlit entry has no version. |
| J8 | Low | There is no `CONTRIBUTING` file, code of conduct, or API documentation; the JOSS criteria ask for community guidelines and documented functionality. |

The reference to Jain et al. (2013) is correct (DOI 10.1063/1.4812323). The Zenodo record matches `CITATION.cff` in title, version, date and ORCID.

---

## 6. Security and Dependencies

No credentials, tokens or keys are present in tracked files. Uploaded files are decoded as text and matched with bounded regular expressions; no upload is executed, written to disk or passed to a shell. Streamlit's default upload limit (200 MB) applies and no smaller limit is set. The only injection surface found is B12. Dependencies are specified with lower bounds only, so a future major release of Streamlit, pandas or Plotly can break the application without any change in the repository; M13 is an instance of this. The workflow pins actions by tag (`actions/checkout@v4`, `actions/setup-python@v5`) and declares no `permissions` block.

---

## 7. Recommendations

The recommendations are ordered by the dependency between them.

1. **Decide the status of pull request #1.** It corrects 13 of the 17 defects on `main`. Splitting it into (a) defect fixes and repository hygiene, (b) interface and XRD analysis, and (c) dataset and scripts would allow (a) to be merged at once and (b) and (c) to be reviewed separately.
2. **Constrain the predictor to what the evidence supports.** Either restrict the application to TiO2 and remove the non-TiO2 presets, the magnetic outputs and the other unsupported properties, or present the tool as a data-entry and literature-comparison workflow in which the surrogate is an optional illustration. A fitted model should replace the surrogate only if it exceeds the constant baseline under leave-one-paper-out evaluation with the penalty chosen inside the training folds.
3. **Correct the XRD routine before it is described as Scherrer or Williamson–Hall analysis.** Required: profile fitting of overlapping reflections or exclusion of unresolved pairs, Kα2 handling, an instrumental-broadening input, a noise threshold for peak detection, and a strain field left empty when no strain was fitted. Table 4 can be converted directly into regression tests.
4. **Remove default lattice parameters.** Report "not available" when a file carries no cell tags.
5. **Homogenise the dataset target.** Add a column for the transition type used in the Tauc analysis and either fit within one type or carry the type as a feature. Resolve DOI 10.22052/JNS.2020.03.017 against the journal page. Complete the 10% independent re-check listed in the search log; the 22 rows verified here (16%) can count towards it.
6. **Move `ugp` to its own repository.** It is unrelated to the stated scope and its engines are placeholders.
7. **Rewrite the paper after the code is settled.** Add the four missing sections, convert the citations to `[@key]`, bring the length into range, remove the statements in J4 that the code does not support, and report Table 5 as it stands.
8. **Cut a new tagged release** once the above are merged, so that the Zenodo archive, `CITATION.cff`, `pyproject.toml` and the paper refer to the same code.

---

## 8. Limitations of this Audit

The applications were exercised headlessly; rendering, layout and the file-upload widget were not inspected in a browser. Synthetic XRD scans were used because the repository holds no measured continuous scan; behaviour on instrument data may differ. Dataset verification covered 22 of 137 rows. The JOSS requirements were read from the journal's documentation on the audit date and may change. No fix was applied to either branch.

---

## References

Jain, A., Ong, S. P., Hautier, G., Chen, W., Richards, W. D., Dacek, S., Cholia, S., Gunter, D., Skinner, D., Ceder, G., & Persson, K. A. (2013). Commentary: The Materials Project: A materials genome approach to accelerating materials innovation. *APL Materials, 1*(1), 011002. https://doi.org/10.1063/1.4812323

Journal of Open Source Software. (n.d.). *JOSS paper format*. Retrieved 19 November 2026, from https://joss.readthedocs.io/en/latest/paper.html

Journal of Open Source Software. (n.d.). *Review criteria*. Retrieved 19 November 2026, from https://joss.readthedocs.io/en/latest/review_criteria.html

Source papers used for dataset verification are identified by first author, year and DOI as returned by Crossref; full bibliographic details (co-authors, volume, pages) were not transcribed and should be taken from the DOI records.

- Kim et al. (2021), *ACS Omega*. https://doi.org/10.1021/acsomega.1c00043
- Tang et al. (2021), *Materials*. https://doi.org/10.3390/ma14195674
- Mancuso et al. (2021), *Materials*. https://doi.org/10.3390/ma14113105
- Wang et al. (2018), *Nanomaterials*. https://doi.org/10.3390/nano8050294
- Soni et al. (2022), *RSC Advances*. https://doi.org/10.1039/d2ra02847f
- Safeen et al. (2022), *RSC Advances*. https://doi.org/10.1039/D2RA01948E
- Lontio Fomekong et al. (2019), *Frontiers in Materials*. https://doi.org/10.3389/fmats.2019.00252
