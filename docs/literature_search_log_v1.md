# ThanimamPro literature seed: search and curation log (v1)

Date of search: 18 November 2026. Scope fixed before searching: TiO2 and doped TiO2, methods sol-gel, hydrothermal, co-precipitation, solid-state, combustion. Computed (DFT) band gaps were not used; all `band_gap_ev` values are experimental.

## 1. Sources searched

Web search (open web, standard mode) followed by retrieval of the open-access full text of each paper. Scopus, Web of Science and publisher paywalled content were not available in this session.

Queries (verbatim):
1. TiO2 nanoparticles sol-gel calcination temperature band gap BET surface area table
2. TiO2 hydrothermal synthesis pH band gap BET surface area Tauc open access
3. TiO2 co-precipitation calcination temperature band gap specific surface area anatase rutile
4. TiO2 solution combustion synthesis band gap BET surface area
5. Fe-doped TiO2 sol-gel Tauc band gap BET surface area table calcination 500 °C mdpi
6. N-doped TiO2 sol-gel band gap BET surface area table nanomaterials open access calcination
7. TiO2 hydrothermal temperature time pH band gap surface area table anatase brookite open access
8. solid-state reaction TiO2 doped calcination band gap BET surface area photocatalyst table open access
9. TiO2 co-precipitation pH ammonia calcination temperature band gap BET surface area anatase table
10. combustion synthesis TiO2 glycine urea fuel BET surface area band gap Tauc table

## 2. Papers included (15 DOIs, 76 rows)

| No. | DOI | Method class | Rows |
|---|---|---|---|
| 1 | 10.1021/acsomega.1c00043 | other (TiOCl2 hydrolysis, pH 7) | 5 |
| 2 | 10.3390/catal15010064 | sol-gel | 11 |
| 3 | 10.3390/ma14113105 | sol-gel | 4 |
| 4 | 10.3311/PPch.11789 | sol-gel | 4 |
| 5 | 10.11113/jt.v70.3437 | sol-gel | 4 |
| 6 | 10.3389/fmats.2019.00252 | co-precipitation | 3 |
| 7 | 10.15251/DJNB.2024.193.999 | co-precipitation | 3 |
| 8 | 10.7717/peerj-matsci.13 | sol-gel (3), hydrothermal (3) | 6 |
| 9 | 10.9767/bcrec.20056 | hydrothermal | 7 |
| 10 | 10.1557/s43578-022-00885-8 | solid-state | 6 |
| 11 | 10.1016/j.oceram.2024.100562 | combustion | 14 |
| 12 | 10.1039/C5NJ01001B | combustion (1), hydrothermal (1) | 2 |
| 13 | 10.3906/kim-1808-6 | combustion | 1 |
| 14 | 10.1039/c6ra27924d | combustion | 1 |
| 15 | 10.1039/d2ra02847f | combustion | 5 |

## 3. Conventions applied

- `temperature_c` is the final calcination or annealing temperature. For combustion samples without a separate calcination step it is the furnace or reaction temperature stated by the authors (rows 12 to 15, stated in `notes`).
- `pH` is filled only when the paper reports a synthesis-stage pH. Where the pH is a peptization or washing pH (Catalysts 2025 Table 3; BCREC 2023), the row says so in `notes`.
- `crystallite_size_nm` holds the size of the dominant phase as reported by the authors; the phase fractions are in `phase`.
- Where a paper reports several band gaps for one sample (direct and indirect, or two extrapolation methods), the value matching the method named in `measurement_method_band_gap` is entered and the others are listed in `notes`.
- No value was converted, interpolated or estimated. Approximate values given as "~" in running text were not used.

## 4. Items that require a second check before use in a fit

1. No independent second-person check (protocol item 7) has been done. Text was retrieved through a web fetch tool that summarises pages, so a 10 % re-check against the original PDFs is needed. In this session the following were re-read a second time against the source: Zahwa et al. (5 rows), BCREC (all 7 rows), Catalysts 2025 Table 2 (all 6 rows).
2. DOIs of papers 7, 12, 13 and 14 were taken from the fetched page or the journal URL; resolve them at doi.org before acceptance. DOIs of papers 4, 5, 9, 11, 15 and 3 were seen on the publisher or repository page text.
3. Catalysts 2025: the text gives inconsistent peptization pH values (4.0, 5.0, 6.0) and the 800 °C phase fractions in Table 2 are on mixed scales. pH was left blank for the temperature series.
4. Periodica Polytechnica 2019: crystallite size for R = 0.25 is 9 nm in Table 1 and 11 nm in the text.
5. Zahwa et al. 2024: the Tauc exponent n = 1/2 corresponds to an indirect transition, while the text refers to direct transitions. Treat the 14 band gap values as method-ambiguous.
6. RSC Advances 2022: undoped TiO2 band gap of 2.94 eV is low for anatase; verify against the original figure.
7. Mancuso et al. 2021: calcination temperature for the Fe-doped samples is inferred from the "similar procedure" wording.
8. Rosa et al. 2023: source Methods list four Fe loadings, Table 1 lists three.

## 5. Records located but not entered

| Source | Reason |
|---|---|
| Azeez et al. 2018, Sci. Rep. (10.1038/s41598-018-25673-5), hydrothermal at pH 1.6, 7.0, 10 | Full text blocked by a browser-verification page; the pH series is the most useful hydrothermal pH data found. Retrieve manually. |
| Dodoo-Arhin et al. 2018, Heliyon (10.1016/j.heliyon.2018.e00681) | BET values appear only as approximate text values; no band gap; sol-gel and hydrothermal values at 200 °C are identical in the extraction. Check the figure. |
| Santos et al. 2021, Cerâmica (10.1590/0366-69132021673843084) | Per-sample BET and band gap are in tables that were not retrievable; text gives only the range 3.29 to 3.40 eV. |
| Oriental J. Chem. 2017 (10.13005/ojc/330105) | Gives pH and calcination series but no BET or band gap. |
| Nano 12(19) 3402 (Fe-doped sol-gel) | Only one BET value retrievable. |
| Ni/Co co-doped sol-gel (Opt. Quant. Electron., Springer s11082-017-1064-x); Fe-doped TiO2 (Thai-Jo nuej 26091); N-doped TiO2 (Iran. J. Mater. Sci. Eng. 2012) | Found in search; tables not extracted in this run. |
| Preprints.org 202502.2124 (pH series, BET up to 232 m²/g) | Preprint, not peer reviewed. |
| Diallo et al. 2026, RSC Adv. (ZnO:TiO2 solid-state) | ZnO-based composite, outside the TiO2 scope. |
| Commercial P25 rows in several papers | Not a synthesis record. |

## 6. Coverage against the protocol targets

76 rows from 15 papers; 52 rows carry both band gap and BET; 20 rows carry a pH. Methods: sol-gel 26, combustion 22, hydrothermal 11, co-precipitation 6, solid-state 6, other 5. The first-fit target (at least 200 rows, at least 20 per method) is not yet met for hydrothermal, co-precipitation and solid-state. Combustion rows come predominantly from one paper (14 of 22), and the split by paper must be respected in any train–test division.
