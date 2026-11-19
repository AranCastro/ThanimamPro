---
title: "ThanimamPro: An open workflow linking synthesis conditions, XRD line-broadening analysis and literature data for TiO2 nanomaterials"
tags:
  - Python
  - materials informatics
  - titanium dioxide
  - X-ray diffraction
  - Scherrer analysis
  - band gap
  - Streamlit
authors:
  - name: Aran Castro
    orcid: 0000-0001-8038-606X
    affiliation: 1
affiliations:
  - name: Geospatial Campus, India
    index: 1
date: 19 November 2026
bibliography: paper.bib
---

# Summary

ThanimamPro is an open-source Python package with a Streamlit interface [@streamlit] for recording synthesis conditions of titanium dioxide (TiO2) and doped TiO2, analysing laboratory X-ray diffraction (XRD) scans, and comparing the result with a curated table of published measurements. The package contains four parts: a validated schema for synthesis and structural records; a line-broadening routine that returns crystallite size and microstrain from continuous Cu Kα scans; a literature table of 137 experimental records from 30 papers, each traceable to a DOI; and three linear relations fitted to that table, which are reported together with their leave-one-paper-out error. The interface adds property maps, a search over calcination temperature against property targets, scenario comparison and report export. This paper describes version 0.2.0; version 0.1.1 is archived on Zenodo (https://doi.org/10.5281/zenodo.18648129).

# Statement of need

Reports on oxide nanomaterials give synthesis conditions, XRD results and functional properties in separate places and in inconsistent forms. A researcher who wishes to compare a new sample with earlier work must collect values by hand, decide which temperature a paper refers to, and note whether a band gap came from a direct or an indirect Tauc analysis. The same researcher usually estimates crystallite size from one reflection in a spreadsheet, without recording how overlapping reflections, instrumental broadening or the Kα2 component were treated.

ThanimamPro addresses these two routine tasks for one well-studied system. It provides a single record format for conditions and descriptors, a documented and tested line-broadening analysis, and a literature table whose columns separate calcination, hydrothermal and combustion temperatures and record the form of the Tauc analysis. The intended users are students and researchers in photocatalysis and oxide synthesis who need a transparent first comparison, and developers who need a small, provenance-checked table for testing regression models.

# State of the field

Large computed databases such as the Materials Project [@jain2013materials], with analysis libraries such as pymatgen [@ong2013pymatgen] and feature libraries such as matminer [@ward2018matminer], serve data-driven work on calculated properties. They do not hold experimental band gaps or surface areas of nanoparticles as a function of synthesis conditions. Text-mined synthesis datasets [@kononova2019] give recipes at scale but no property values. For diffraction, GSAS-II [@toby2013gsas] and similar Rietveld programs give a full treatment of line profiles; they require a structural model and training that a first size estimate does not justify.

ThanimamPro does not compete with these tools. It occupies the gap between them: experimental synthesis–property records for one material family, with a size estimate that needs only a scan. A contribution to an existing package was considered unsuitable because the three parts depend on a common record format and on scope rules specific to the TiO2 literature, such as the separation of temperature types.

# Software design

The core package `thanimampro_api` has no dependency on the interface and uses only NumPy [@harris2020numpy] and pandas [@mckinney2010]; figures are drawn with Plotly [@plotly].

**Records.** `SynthesisInput`, `StructureFeatures` and `DesiredPropertyTargets` are dataclasses that reject non-finite and out-of-range values. A structural descriptor that a file does not determine is `None`. This was a deliberate change from the first release, which substituted default lattice parameters and count-based size estimates; an absent value cannot be mistaken for a measurement.

**XRD analysis.** For scans of at least 50 points with a step of 0.1° or less, the routine subtracts a rolling-percentile background, optionally removes Kα2 by the Rachinger recursion [@rachinger1948], detects maxima above five times a noise level estimated from second differences, and measures the full width at half maximum by interpolation. A reflection is used only if it is resolved from its neighbours. Instrumental broadening supplied by the user is removed in quadrature. Size and strain come from a Williamson–Hall fit [@williamson1953] when at least four resolved reflections exist and the strain exceeds twice its standard error; otherwise the intensity-weighted Scherrer size [@patterson1939] is returned and no strain is reported. Half-maximum widths were chosen over profile fitting to keep the method dependency-free and inspectable; the cost is that overlapping reflections are excluded, not deconvolved.

**Calibrated relations.** `scripts/fit_surrogate.py` fits the band gap to temperature and a doping indicator, and the logarithms of BET surface area and crystallite size to calcination temperature, by ordinary least squares. Each DOI is held out in turn. A unit test refits the shipped table and fails if the constants in the code differ, so the published coefficients cannot drift from the data. When a crystallite size has been measured, the surface area is taken from the geometric relation for dense spheres. Functions `scope_warnings` and `reachable_band_gap_range` state when an input lies outside the calibrated domain or a target cannot be met.

**Scope.** Seven further properties in the interface are illustrative expressions without validation and are labelled as such.

# Research impact statement

The software has not yet been used in a publication, thesis or course, and no external users are known to the author. The evidence offered is therefore the reproducible material in the repository.

*Benchmark.* On held-out papers the band-gap relation has a mean absolute error (MAE) of 0.145 eV and R² = 0.35 (n = 76 rows, 19 papers), against 0.186 eV and −0.08 for a constant. The temperature relation for surface area has an MAE of 46.5 m²/g and R² = −0.13 (n = 95 rows, 20 papers) and is no better than a constant by R². The geometric relation has an MAE of 33.7 m²/g and R² = 0.48 with a bias of +24.7 m²/g (n = 55 rows, 10 papers). The table mixes direct and indirect Tauc analyses, which differ by up to 0.29 eV for one sample in one source [@mancuso2021]; this limits the accuracy any model of the pooled column can reach.

*Validation.* On synthetic scans of known size the routine recovers 5, 10, 20, 50 and 100 nm within 5% and a strain of 0.30% as 0.30%. No measured reference scan is included.

*Data.* Twenty-two of the 137 rows were compared with the source full text, including all rows from @kim2021, and agreed. One DOI printed by a journal is not registered and is flagged in the table.

*Community readiness.* The repository has continuous integration on Python 3.10 to 3.13, 39 tests, contribution guidelines and an MIT licence.

# AI usage disclosure

Generative AI tools assisted the writing of the original release, version 0.1.1. A generative AI coding assistant (Claude Code, Anthropic) was then used in November 2026 for the following: an audit of version 0.1.1; the rewrite of the XRD routine, the calibration script, the validation of inputs, the tests and the interface; the compilation of the literature table by web search and retrieval of open-access papers; and the drafting of the documentation and of this manuscript. The search queries, inclusion decisions and withheld values are recorded in `docs/literature_search_log_v1.md` to `v6.md`.

Verification within those sessions consisted of the automated tests, the synthetic-scan checks, resolution of the dataset DOIs at Crossref, and a comparison of 22 table rows with source full text retrieved independently of the tool used for compilation. The remaining 115 rows were extracted through a summarising retrieval tool and have not been independently checked.

The author directed the work, took the decisions on scope (restriction to TiO2, removal of an unrelated package, the release) and approved the changes for merging. The automated checks above, and not a line-by-line human review, are the basis for the stated accuracy figures.

# Acknowledgements

The author acknowledges the developers of NumPy, pandas, Plotly and Streamlit. This work received no external funding.

# References
