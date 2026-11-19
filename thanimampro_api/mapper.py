from __future__ import annotations

from dataclasses import replace
from typing import List

import pandas as pd

from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import PredictedProperties, StructureFeatures, SynthesisInput


def _axis(low: float, high: float, points: int, name: str) -> List[float]:
    """Evenly spaced axis values; collapses to a single value when low == high."""
    if low > high:
        raise ValueError(f"{name}: minimum ({low}) exceeds maximum ({high})")
    if low == high or points == 1:
        return [float(low)]
    step = (high - low) / (points - 1)
    return [low + i * step for i in range(points)]


def build_property_map(
    baseline: SynthesisInput,
    structure: StructureFeatures | None,
    temp_min: float,
    temp_max: float,
    ph_min: float,
    ph_max: float,
    points: int = 25,
    prop: str = "band_gap_ev",
) -> pd.DataFrame:
    """Predicted property over a temperature (degC) x pH grid; columns temperature_c, pH, value."""
    if points < 1:
        raise ValueError("points must be at least 1")
    if not hasattr(PredictedProperties, "__dataclass_fields__") or prop not in PredictedProperties.__dataclass_fields__:
        raise ValueError(f"unknown property {prop!r}")
    temps = _axis(temp_min, temp_max, points, "temperature")
    phs = _axis(ph_min, ph_max, points, "pH")

    rows = []
    for temp in temps:
        for ph in phs:
            trial = replace(baseline, temperature_c=temp, pH=ph)
            pred = predict_properties(trial, structure)
            rows.append({"temperature_c": temp, "pH": ph, "value": getattr(pred, prop)})
    return pd.DataFrame(rows)


def build_bandgap_map(*args, **kwargs) -> pd.DataFrame:
    """Band-gap map (backward-compatible wrapper; value column named band_gap_ev)."""
    return build_property_map(*args, prop="band_gap_ev", **kwargs).rename(columns={"value": "band_gap_ev"})
