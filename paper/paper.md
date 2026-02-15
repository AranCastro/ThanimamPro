---
title: "ThanimamPro: An open platform for synthesis-structure-property integration in materials research"
tags:
  - materials informatics
  - synthesis optimization
  - inverse design
  - streamlit
authors:
  - name: Primary Contributor
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Independent Research
    index: 1
date: 15 February 2026
bibliography: paper.bib
---

# Summary

ThanimamPro is an open-source software platform that connects synthesis conditions, structure indicators, and functional property prediction for materials development workflows. The software provides an interactive user interface built with Streamlit and a reusable Python core package for model logic and data operations.

The current version includes: synthesis parameter entry, CIF/XRD upload with structure descriptor extraction, multi-domain property prediction, sensitivity heatmaps, inverse design suggestions, and searchable literature records. The project is designed for transparent iteration toward community-scale materials datasets and model upgrades.

# Statement of need

Many materials studies report synthesis parameters, structural characterization, and measured properties in fragmented forms across literature and lab notebooks. This limits reproducibility and slows data-driven optimization. ThanimamPro addresses this gap by standardizing these components into one workflow where users can:

1. Enter experimental synthesis settings.
2. Analyze uploaded structure files for compact descriptors.
3. Predict multiple classes of properties.
4. Visualize synthesis-property trends.
5. Request inverse recommendations from target properties.

The software is intended for researchers in catalysis, energy materials, oxide systems, and other materials domains where process-structure-property relationships are central.

# Implementation

ThanimamPro is implemented in Python and organized into two layers:

1. `thanimampro_api`: core package for schema definitions, structure parsing, prediction logic, inverse design search, and literature filtering.
2. `streamlit_app`: front-end interface for interactive use and public deployment via Streamlit Community Cloud.

The prediction component currently uses a transparent baseline surrogate formulation to support end-to-end workflow testing while larger curated datasets and trained models are integrated.

# Future work

Planned development includes:

1. Model replacement with literature-trained and benchmarked regressors.
2. Robust CIF parsing and full XRD phase identification pipelines.
3. Community data contribution workflows with validation.
4. Versioned benchmark datasets and uncertainty-aware prediction reporting.

# Acknowledgements

The authors acknowledge the open-source Python ecosystem and the JOSS editorial community.

# References
