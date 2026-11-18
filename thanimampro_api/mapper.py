from __future__ import annotations

from dataclasses import replace
from typing import List

import pandas as pd

from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import StructureFeatures, SynthesisInput


def _axis(low: float, high: float, points: int, name: str) -> List[float]:
    """Evenly spaced axis values; collapses to a single value when low == high."""
    if low > high:
        raise ValueError(f"{name}: minimum ({low}) exceeds maximum ({high})")
    if low == high or points == 1:
        return [float(low)]
    step = (high - low) / (points - 1)
    return [low + i * step for i in range(points)]


def build_bandgap_map(
    baseline: SynthesisInput,
    structure: StructureFeatures | None,
    temp_min: float,
    temp_max: float,
    ph_min: float,
    ph_max: float,
    points: int = 25,
) -> pd.DataFrame:
    """Predicted band gap over a temperature (degC) x pH grid, one row per grid node."""
    if points < 1:
        raise ValueError("points must be at least 1")
    temps = _axis(temp_min, temp_max, points, "temperature")
    phs = _axis(ph_min, ph_max, points, "pH")

    rows = []
    for temp in temps:
        for ph in phs:
            trial = replace(baseline, temperature_c=temp, pH=ph)
            pred = predict_properties(trial, structure)
            rows.append({"temperature_c": temp, "pH": ph, "band_gap_ev": pred.band_gap_ev})
    return pd.DataFrame(rows)
