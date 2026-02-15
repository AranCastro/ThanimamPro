[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18648129.svg)](https://doi.org/10.5281/zenodo.18648129)

# ThanimamPro

**ThanimamPro** is an integrated data-driven synthesis–structure–property platform designed to support materials research and development. The software provides a unified workflow linking experimental synthesis parameters, structural descriptors, and predicted functional properties within an open and reproducible computational framework.

---

## Statement of Need

In materials research, synthesis parameters, crystal structure, and functional properties are often reported separately, making systematic exploration and inverse design challenging. ThanimamPro addresses this gap by providing a structured computational interface that integrates synthesis input, lightweight structural parsing, surrogate property prediction, and interactive parameter mapping within a single research workflow.

---

## Core Functionality

ThanimamPro includes:

- **Synthesis Parameter Entry Module**  
  Structured input of thermal, chemical, and processing variables.

- **Structure Analysis Module**  
  CIF/XRD parsing and derivation of structural descriptors.

- **Property Prediction Engine**  
  Baseline surrogate modelling for functional property estimation.

- **Synthesis–Property Mapper**  
  Interactive heatmaps and sensitivity exploration.

- **Inverse Design Assistant**  
  Property-targeted parameter suggestion.

- **Literature Dataset Interface**  
  Searchable seed dataset for exploratory modelling.

---

## Installation

### Create environment
```bash
python -m venv .venv
