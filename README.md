# ThanimamPro

[![CI](https://github.com/your-org/thanimampro/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/thanimampro/actions/workflows/ci.yml)

Synthesis-Structure-Property Integration Platform for materials R&D.

ThanimamPro links experimental synthesis settings, structure descriptors, and predicted functional properties in one open workflow. It includes:

1. Synthesis parameter entry
2. CIF/XRD structure analysis (lightweight parser + derived descriptors)
3. Property prediction engine (baseline surrogate model)
4. Synthesis-property heatmap mapper
5. Inverse design assistant
6. Literature dataset search panel

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Streamlit public deployment

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud and create a new app from the repo.
3. Set main file path to `streamlit_app.py`.
4. Deploy.

## Project layout

- `streamlit_app.py`: user interface entrypoint
- `thanimampro_api/`: reusable core logic
- `data/literature_seed.csv`: starter literature dataset
- `paper/paper.md`: JOSS manuscript draft
- `paper/paper.bib`: bibliography for JOSS paper

## JOSS readiness

This repository includes initial JOSS assets:

- `paper/paper.md`
- `paper/paper.bib`
- `LICENSE`
- `CITATION.cff`

Before submission, update author metadata, archive a tagged release on Zenodo, and replace placeholder citations/DOIs where needed.
