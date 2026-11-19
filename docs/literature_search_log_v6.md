# ThanimamPro literature seed: curation log (v6)

Date: 19 November 2026. No new search was run and no row was added or removed. This log records
the changes made after the audit of 19 November 2026
(`CLAUDE-OUTPUTS/thanimampro/thanimampro_audit-report_v1.md`) and extends the v5 log, whose
sections 1 to 6 still apply.

## 1. Changes to the table

| Change | Rows | Basis |
|---|---|---|
| New column `band_gap_transition` (direct, indirect, other), filled wherever `band_gap_ev` is given | 76 | Derived from `measurement_method_band_gap`. Direct: the method names a direct transition or a squared ordinate. Indirect: it names an indirect transition or a square-root ordinate. Other: the form is not stated, or the printed relation is ambiguous. Counts: direct 32, indirect 32, other 12. |
| `band_gap_transition` set to `indirect` for 10.1039/d2ra02847f | 4 | The source gives (F(R)hν)^1/2 against hν (read from the Europe PMC full text, PMC9244643). |
| `band_gap_transition` set to `other` for the rows whose relation is printed as (αhν) = A(hν − Eg)^1/2 | 5 | The exponent on the right-hand side corresponds to a direct transition, while the earlier note called it the indirect form; the source wording is ambiguous, so neither is asserted. |
| Note added: DOI not registered | 3 | 10.22052/JNS.2020.03.017 returned HTTP 404 at the Crossref API and at doi.org on 19 November 2026. The journal site was unavailable (HTTP 503), so the printed DOI could not be confirmed. |
| Note added: hydrothermal ageing step | 4 | 10.3390/ma14113105 describes hydrothermal treatment at 98 °C for 48 h before calcination at 450 °C for 4 h. The method class stays `sol-gel`. |

No numeric value was altered; this was checked by comparing every non-note cell with the v5 file.

## 2. Verification carried out in the audit

DOIs: 27 of 30 are registered at Crossref with titles that match the row content; two resolve at
doi.org through other registrars (10.14456/cast.1477.4, 10.30495/ijc.2022.1941684.1875); one does
not resolve (above).

Rows compared with source full text (band gap, BET area, crystallite size, temperature, time, pH
and phase fractions, as applicable): 22 rows from seven papers, all in agreement.

| DOI | Rows | Source read |
|---|---|---|
| 10.1021/acsomega.1c00043 | 5 | Europe PMC XML (PMC8153737), Tables 1 to 3 |
| 10.3390/ma14195674 | 3 | Europe PMC XML (PMC8510127), Table 1 |
| 10.3390/ma14113105 | 4 | Europe PMC XML (PMC8201317), Table 2 and footnotes |
| 10.3390/nano8050294 | 1 | Europe PMC XML (PMC5977308), running text |
| 10.1039/d2ra02847f | 4 | Europe PMC XML (PMC9244643), Table 2 and running text |
| 10.1039/D2RA01948E | 2 | Europe PMC XML (PMC9132072), running text |
| 10.3389/fmats.2019.00252 | 3 | Publisher page, through a summarising retrieval tool |

The six Europe PMC texts were parsed locally and are independent of the summarising tool used
when the table was compiled. The remaining 115 rows have not been independently checked; the 10%
re-check required by protocol item 7 is met in number (16%) but not as a second-person check.

## 3. Open items

Items 3 to 8 of section 4 of the v5 log remain open, except that the DOIs 10.15251/DJNB.2024.193.999,
10.1039/C5NJ01001B, 10.3906/kim-1808-6, 10.1039/c6ra27924d, 10.11113/jt.v70.3437,
10.1590/S0104-66322011000200011 and 10.1590/1980-5373-MR-2015-0381 are now confirmed as registered
at Crossref. New open item: confirm the Journal of Nanostructures DOI against the journal page.

## 4. Use of the table for calibration

`scripts/fit_surrogate.py` fits three relations to this table and reports leave-one-paper-out
errors; the coefficients are stored in `thanimampro_api/predict.py`. The band-gap fit pools the
three transition classes. Fitting within one class, or carrying the class as a covariate, is the
next step once more rows are available (32 direct and 32 indirect rows at present).
