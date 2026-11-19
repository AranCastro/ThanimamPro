"""Fit the calibrated part of the surrogate to the literature table and report held-out skill.

Usage: python scripts/fit_surrogate.py [data/literature_seed.csv]

Three ordinary-least-squares relations are fitted (no regularisation, no tuned hyper-parameter):
  band gap (eV)            = b0 + b1 * (T - 600) + b2 * doped        all rows with a band gap
  log10(BET area, m2/g)    = s0 + s1 * (T - 500)                     calcination rows only
  log10(crystallite, nm)   = c0 + c1 * (T - 500)                     calcination rows only
T is the temperature in degC; doped = 1 when material_system carries a dopant ("TiO2:Fe").
Each relation is evaluated by leave-one-paper-out (LOPO): every DOI is held out in turn and
predicted from a fit to the remaining papers. Reported: MAE, RMSE and R2 = 1 - SSE/SST over the
pooled held-out predictions, with a constant (training-mean) predictor for scale. Errors of the
two log relations are reported after back-transformation.

The coefficients printed under "full-data fit" are the constants in thanimampro_api/predict.py;
tests/test_calibration.py fails if the two drift apart.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from thanimampro_api.database import load_literature_data


def _design(frame: pd.DataFrame, centre: float, doped: bool) -> np.ndarray:
    cols = [np.ones(len(frame)), frame["temperature_c"].to_numpy(float) - centre]
    if doped:
        cols.append(frame["material_system"].astype(str).str.contains(":").to_numpy(float))
    return np.column_stack(cols)


def _subset(frame: pd.DataFrame, target: str, calcination_only: bool) -> pd.DataFrame:
    sub = frame.dropna(subset=[target, "temperature_c"])
    if calcination_only:
        sub = sub[sub["temperature_type"] == "calcination"]
    return sub.reset_index(drop=True)


def fit(frame: pd.DataFrame, target: str, centre: float, doped: bool, log: bool, calcination_only: bool) -> dict:
    """Full-data coefficients and LOPO metrics for one relation."""
    sub = _subset(frame, target, calcination_only)
    obs = sub[target].to_numpy(float)
    y = np.log10(obs) if log else obs
    X = _design(sub, centre, doped)
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    pred, const = np.zeros(len(sub)), np.zeros(len(sub))
    for doi in sub["doi"].unique():
        te = (sub["doi"] == doi).to_numpy()
        w = np.linalg.lstsq(X[~te], y[~te], rcond=None)[0]
        pred[te] = X[te] @ w
        const[te] = y[~te].mean()
    if log:
        pred, const = 10 ** pred, 10 ** const
    sst = ((obs - obs.mean()) ** 2).sum()

    def metrics(p: np.ndarray) -> dict:
        err = p - obs
        return {"mae": float(np.abs(err).mean()), "rmse": float(np.sqrt((err ** 2).mean())),
                "r2": float(1 - (err ** 2).sum() / sst)}

    return {"coef": [float(c) for c in coef], "n": len(sub), "papers": int(sub["doi"].nunique()),
            "t_range": (float(sub["temperature_c"].min()), float(sub["temperature_c"].max())),
            "model": metrics(pred), "constant": metrics(const)}


RELATIONS = {
    "band_gap_ev": dict(centre=600.0, doped=True, log=False, calcination_only=False),
    "surface_area_m2_g": dict(centre=500.0, doped=False, log=True, calcination_only=True),
    "crystallite_size_nm": dict(centre=500.0, doped=False, log=True, calcination_only=True),
}


def fit_all(frame: pd.DataFrame) -> dict:
    return {target: fit(frame, target, **kw) for target, kw in RELATIONS.items()}


def geometric_surface_area_check(frame: pd.DataFrame, density_g_cm3: float = 3.9) -> dict:
    """Parameter-free check of S = 6000 / (rho * D) on rows that report both D and BET area."""
    sub = frame.dropna(subset=["crystallite_size_nm", "surface_area_m2_g"])
    obs = sub["surface_area_m2_g"].to_numpy(float)
    err = 6000.0 / (density_g_cm3 * sub["crystallite_size_nm"].to_numpy(float)) - obs
    sst = ((obs - obs.mean()) ** 2).sum()
    return {"n": len(sub), "papers": int(sub["doi"].nunique()), "mae": float(np.abs(err).mean()),
            "rmse": float(np.sqrt((err ** 2).mean())), "bias": float(err.mean()),
            "r2": float(1 - (err ** 2).sum() / sst)}


if __name__ == "__main__":
    data = load_literature_data(sys.argv[1] if len(sys.argv) > 1 else "data/literature_seed.csv")
    for target, res in fit_all(data).items():
        print(f"\n{target}: n={res['n']} rows, {res['papers']} papers, T {res['t_range'][0]:.0f}-{res['t_range'][1]:.0f} degC")
        print("  full-data fit:", ", ".join(f"{c:.6g}" for c in res["coef"]))
        for name in ("model", "constant"):
            m = res[name]
            print(f"  LOPO {name:<9} MAE={m['mae']:.3g}  RMSE={m['rmse']:.3g}  R2={m['r2']:.2f}")
    g = geometric_surface_area_check(data)
    print(f"\ngeometric surface area 6000/(3.9 D): n={g['n']} rows, {g['papers']} papers  "
          f"MAE={g['mae']:.3g}  RMSE={g['rmse']:.3g}  bias={g['bias']:+.3g}  R2={g['r2']:.2f}")
