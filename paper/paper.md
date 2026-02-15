---
title: "ThanimamPro: An open platform for synthesis–structure–property integration in materials research"
tags:
  - materials-informatics
  - synthesis-optimization
  - inverse-design
  - computational-materials
  - streamlit
authors:
  - name: Aran Castro
    orcid: 0000-0001-8038-606X
    affiliation: 1
affiliations:
  - name: Geospatial Campus, India
    index: 1
date: 15 February 2026
bibliography: paper.bib
---

# Summary

ThanimamPro is an open-source computational platform that integrates synthesis parameters, structural descriptors, and functional property prediction within a unified workflow for materials research. The software combines an interactive web-based interface built using Streamlit with a modular Python backend that implements schema handling, lightweight structural parsing, surrogate modelling, and inverse parameter exploration.

The current release enables structured synthesis parameter entry, CIF/XRD upload with descriptor extraction, baseline multi-domain property prediction, synthesis–property heatmap visualization, inverse design assistance, and literature seed dataset search. The platform is designed to support iterative integration of curated datasets and benchmarked models while maintaining reproducibility through versioned releases and archival DOI registration.

# Statement of Need

Materials research frequently reports synthesis conditions, structural characterization, and functional properties in fragmented formats across publications and laboratory records. This fragmentation limits reproducibility and constrains systematic exploration of process–structure–property relationships.

Data-driven materials initiatives, such as the Materials Project \cite{jain2013materials}, have demonstrated the value of structured and accessible computational materials data. However, many experimental workflows still lack integrated tools linking synthesis inputs directly to structural indicators and predicted functional outputs.

ThanimamPro addresses this gap by providing a structured computational environment where researchers can:

1. Enter experimental synthesis settings.
2. Extract compact descriptors from uploaded structural files.
3. Estimate functional properties through surrogate models.
4. Visualize synthesis–property trends interactively.
5. Generate inverse suggestions from target property inputs.

The software is intended for researchers in catalysis, electrochemical materials, oxide systems, and related domains where synthesis–structure–property coupling is central to materials optimization.

# Implementation

ThanimamPro is implemented in Python and organised into two primary layers:

- **`thanimampro_api`**: a reusable core package responsible for schema definitions, structure descriptor derivation, surrogate prediction logic, inverse search routines, and dataset filtering.
- **`streamlit_app.py`**: an interactive front-end enabling local execution and public deployment via Streamlit Community Cloud.

The prediction component currently uses a transparent baseline surrogate formulation to validate the end-to-end integration pipeline. The modular architecture allows replacement with benchmarked regression models trained on curated open datasets.

Continuous integration is configured through GitHub Actions to ensure automated testing across supported Python versions. The software is archived via Zenodo with a versioned DOI to ensure reproducibility and citability.

# Future Work

Planned extensions include:

- Integration of literature-trained and benchmarked regression models.
- Expanded CIF parsing and XRD-based phase identification workflows.
- Community data submission and validation pipelines.
- Versioned benchmark datasets with uncertainty-aware prediction reporting.

# Acknowledgements

The author acknowledges the open-source Python ecosystem, including pandas \cite{pandas2020} and Streamlit \cite{streamlit2024}, and the JOSS editorial community for advancing reproducible research software standards.

# References
