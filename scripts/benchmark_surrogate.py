"""Compare the baseline surrogate with the experimental literature table.

Usage: python scripts/benchmark_surrogate.py [data/literature_seed.csv]

Rows without a reported pH are evaluated at pH 7 (neutral prior); all other inputs are the
SynthesisInput defaults, with no structural descriptors. Reported: MAE, RMSE, mean error (bias),
Pearson r with a two-sided permutation p-value (10,000 shuffles, seed 0;
rows from one paper are not independent, so p is optimistic), and the MAE of a constant predictor (training-set mean) for scale.
"""
from __future__ import annotations

import sys
from math import sqrt

import numpy as np
import pandas as pd

from thanimampro_api.database import load_literature_data
from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import SynthesisInput


def _predict(row: pd.Series):
    s = SynthesisInput(
        temperature_c=float(row.temperature_c), heating_rate_c_min=5.0, annealing_time_h=2.0, atmosphere="air",
        precursor_ratio=1.0, pH=float(row.pH) if pd.notna(row.pH) else 7.0, solvent_type="water",
        concentration_m=0.5, pressure_bar=1.0, milling_time_h=0.0, calcination_time_h=2.0, method="other",
    )
    return predict_properties(s, None)


def _pearson_perm(x: np.ndarray, y: np.ndarray, n_perm: int = 10_000, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    r = float(np.corrcoef(x, y)[0, 1])
    null = np.array([np.corrcoef(x, rng.permutation(y))[0, 1] for _ in range(n_perm)])
    return r, float((np.abs(null) >= abs(r)).mean())


def report(frame: pd.DataFrame, column: str, attr: str) -> None:
    sub = frame.dropna(subset=[column, "temperature_c"])
    obs = sub[column].to_numpy(float)
    pred = np.array([getattr(_predict(r), attr) for r in sub.itertuples()])
    err = pred - obs
    r, p = _pearson_perm(pred, obs)
    print(f"{column}: n={len(sub)} papers={sub.doi.nunique()}  MAE={np.abs(err).mean():.3g}  RMSE={sqrt((err**2).mean()):.3g}  "
          f"bias={err.mean():+.3g}  Pearson r={r:+.2f} (p={p:.2g})  constant-mean MAE={np.abs(obs - obs.mean()).mean():.3g}")


if __name__ == "__main__":
    data = load_literature_data(sys.argv[1] if len(sys.argv) > 1 else "data/literature_seed.csv")
    report(data, "band_gap_ev", "band_gap_ev")
    report(data, "surface_area_m2_g", "specific_surface_area_m2_g")
