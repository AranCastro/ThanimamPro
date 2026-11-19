from __future__ import annotations

from dataclasses import replace
from typing import Dict, List

from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import PredictedProperties, StructureFeatures, SynthesisInput

# variable -> (absolute step, lower bound, upper bound)
_STEPS = {"temperature_c": (50.0, 0.0, 3000.0), "pH": (1.0, 0.0, 14.0), "pressure_bar": (None, 0.0, 1e4)}


def one_at_a_time(
    synthesis: SynthesisInput,
    structure: StructureFeatures | None,
    prop: str = "band_gap_ev",
) -> List[Dict[str, float | str]]:
    """
    One-factor-at-a-time sensitivity of a predicted property.

    Each variable is moved down and up by a step (temperature 50 degC, pH 1, pressure 10 %)
    with the others held at the baseline; values are clamped to valid ranges. Returns the
    change in the property for each move, sorted by total swing.
    """
    if prop not in PredictedProperties.__dataclass_fields__:
        raise ValueError(f"unknown property {prop!r}")
    base = getattr(predict_properties(synthesis, structure), prop)
    rows = []
    for var, (step, lo, hi) in _STEPS.items():
        value = getattr(synthesis, var)
        step = step if step is not None else max(1.0, 0.1 * value)
        low_v, high_v = max(lo, value - step), min(hi, value + step)
        out = []
        for v in (low_v, high_v):
            out.append(getattr(predict_properties(replace(synthesis, **{var: v}), structure), prop) - base)
        rows.append({
            "variable": var, "baseline": value, "low_value": low_v, "high_value": high_v,
            "delta_low": out[0], "delta_high": out[1], "swing": abs(out[1] - out[0]),
        })
    return sorted(rows, key=lambda r: r["swing"], reverse=True)
