"""Leave-one-paper-out (LOPO) evaluation of simple models on the literature table.

Usage: python scripts/evaluate_models_lopo.py [data/literature_seed.csv]

Each paper (DOI) is held out in turn; models are trained on all other papers. Compared:
  constant   training-set mean
  per-method training-set mean by synthesis method
  ridge      ridge regression (closed form) on temperature, temperature_type, method, doping flag,
             band-gap transition type (band-gap target only) and pH (training-mean imputed +
             missing flag). Fixed penalties are shown for reference; "ridge nested" chooses the
             penalty inside each training fold by an inner leave-one-paper-out loop, so its score
             does not depend on a penalty picked from the held-out results.
  surrogate  thanimampro_api.predict. Its calibrated coefficients were fitted to this table, so
             this row is an in-sample figure; scripts/fit_surrogate.py reports the held-out one.
             Its surface-area relation is calibrated on calcination temperatures only, so the
             hydrothermal and combustion rows included here lie outside its domain.
Surface area is modelled as log10(BET); errors are reported in m2/g after back-transformation.
Reported: pooled MAE, RMSE and R2 = 1 - SSE/SST over all held-out predictions.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from thanimampro_api.database import load_literature_data
from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import SynthesisInput

METHODS = ["sol-gel", "hydrothermal", "co-precipitation", "solid-state", "combustion", "other"]
TYPES = ["calcination", "hydrothermal", "combustion"]
TRANSITIONS = ["indirect", "other"]  # direct is the reference level
ALPHAS = (1.0, 3.0, 10.0, 30.0, 100.0)


def features(df: pd.DataFrame, ph_fill: float, transition: bool = False) -> np.ndarray:
    cols = [df["temperature_c"].to_numpy(float) / 1000.0]
    if transition and "band_gap_transition" in df.columns:
        cols += [(df["band_gap_transition"] == t).to_numpy(float) for t in TRANSITIONS]
    cols += [(df["temperature_type"] == t).to_numpy(float) for t in TYPES[1:]]
    cols += [(df["method"] == m).to_numpy(float) for m in METHODS]
    cols.append(df["material_system"].astype(str).str.contains(":").to_numpy(float))
    ph = df["pH"].to_numpy(float)
    cols += [np.where(np.isnan(ph), ph_fill, ph) / 14.0, np.isnan(ph).astype(float)]
    return np.column_stack(cols)


def ridge_fit_predict(train: pd.DataFrame, test: pd.DataFrame, y: np.ndarray, alpha: float,
                      transition: bool = False) -> np.ndarray:
    fill = float(np.nanmean(train["pH"])) if train["pH"].notna().any() else 7.0
    X, Xt = features(train, fill, transition), features(test, fill, transition)
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    X, Xt = (X - mu) / sd, (Xt - mu) / sd
    ym = y.mean()
    w = np.linalg.solve(X.T @ X + alpha * np.eye(X.shape[1]), X.T @ (y - ym))
    return Xt @ w + ym


def nested_alpha(train: pd.DataFrame, y: np.ndarray, transition: bool) -> float:
    """Penalty with the lowest inner leave-one-paper-out squared error on the training papers."""
    train = train.reset_index(drop=True)
    sse = {a: 0.0 for a in ALPHAS}
    for doi in train["doi"].unique():
        te = (train["doi"] == doi).to_numpy()
        if te.all():
            continue
        for a in ALPHAS:
            sse[a] += float(((ridge_fit_predict(train[~te], train[te], y[~te], a, transition) - y[te]) ** 2).sum())
    return min(sse, key=sse.get)


def surrogate(row, attr: str) -> float:
    s = SynthesisInput(temperature_c=float(row.temperature_c), heating_rate_c_min=5.0, annealing_time_h=2.0,
                       atmosphere="air", precursor_ratio=1.0, pH=float(row.pH) if pd.notna(row.pH) else 7.0,
                       solvent_type="water", concentration_m=0.5, pressure_bar=1.0, milling_time_h=0.0,
                       calcination_time_h=2.0, method="other", material_system=str(row.material_system))
    return getattr(predict_properties(s, None), attr)


def evaluate(frame: pd.DataFrame, target: str, attr: str, log: bool) -> None:
    d = frame.dropna(subset=[target, "temperature_c", "temperature_type"]).reset_index(drop=True)
    y = np.log10(d[target].to_numpy(float)) if log else d[target].to_numpy(float)
    back = (lambda v: 10 ** v) if log else (lambda v: v)
    obs = d[target].to_numpy(float)
    transition = target == "band_gap_ev"
    preds: dict[str, np.ndarray] = {k: np.zeros(len(d)) for k in ("constant", "per-method", "ridge a=1", "ridge a=10", "ridge a=30", "ridge nested")}
    sur = np.array([surrogate(r, attr) for r in d.itertuples()])
    for doi in d["doi"].unique():
        te = (d["doi"] == doi).to_numpy()
        tr, tt = d[~te], d[te]
        ytr = y[~te]
        preds["constant"][te] = ytr.mean()
        means = tr.assign(_y=ytr).groupby("method")["_y"].mean()
        preds["per-method"][te] = tt["method"].map(means).fillna(ytr.mean()).to_numpy()
        for a in (1, 10, 30):
            preds[f"ridge a={a}"][te] = ridge_fit_predict(tr, tt, ytr, float(a), transition)
        preds["ridge nested"][te] = ridge_fit_predict(tr, tt, ytr, nested_alpha(tr, ytr, transition), transition)
    sst = ((obs - obs.mean()) ** 2).sum()
    print(f"\n{target}: n={len(d)} rows, {d.doi.nunique()} papers (LOPO)")
    print(f"  {'model':<14}{'MAE':>10}{'RMSE':>10}{'R2':>8}")
    for name, p in [*preds.items(), ("surrogate*", sur)]:
        p = back(p) if name != "surrogate*" else p
        err = p - obs
        print(f"  {name:<14}{np.abs(err).mean():>10.3g}{np.sqrt((err ** 2).mean()):>10.3g}{1 - (err ** 2).sum() / sst:>8.2f}")


if __name__ == "__main__":
    data = load_literature_data(sys.argv[1] if len(sys.argv) > 1 else "data/literature_seed.csv")
    evaluate(data, "band_gap_ev", "band_gap_ev", log=False)
    evaluate(data, "surface_area_m2_g", "specific_surface_area_m2_g", log=True)
    print("\n* in-sample: the surrogate coefficients were fitted to this table (held-out figures: scripts/fit_surrogate.py)")
