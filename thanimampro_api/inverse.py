from __future__ import annotations

from dataclasses import replace
from typing import Dict, List

from thanimampro_api.predict import CALIBRATION_T_RANGE_C, estimate_crystallite_size_nm, predict_properties
from thanimampro_api.schemas import DesiredPropertyTargets, StructureFeatures, SynthesisInput

REACHABLE_TOLERANCE_EV = 0.05


def _temperature_grid(step: float = 25.0) -> List[float]:
    lo, hi = CALIBRATION_T_RANGE_C
    return [lo + i * step for i in range(int((hi - lo) / step) + 1)]


def reachable_band_gap_range(
    baseline: SynthesisInput, structure: StructureFeatures | None = None
) -> tuple[float, float]:
    """Smallest and largest band gap the surrogate predicts over the calibrated temperature range."""
    gaps = [predict_properties(replace(baseline, temperature_c=t), structure).band_gap_ev for t in _temperature_grid()]
    return min(gaps), max(gaps)


def suggest_synthesis_conditions(
    baseline: SynthesisInput,
    desired: DesiredPropertyTargets,
    structure: StructureFeatures | None = None,
    top_k: int = 5,
) -> List[Dict[str, float | bool]]:
    """
    Rank calcination temperatures (calibrated range, 25 degC steps) against the targets.

    Temperature is the only synthesis variable that the calibrated band-gap and surface-area
    relations respond to, so it is the only variable searched; all other conditions, including
    whether the material is doped, are taken from ``baseline``. The crystallite size is the
    literature fit to calcination temperature and is compared with ``max_particle_size_nm``.

    score = |band-gap error| / eV + surface-area shortfall / 25 m2/g + size excess / 10 nm.
    Each row carries ``band_gap_error_ev``, ``meets_all_targets`` (band gap within
    ``REACHABLE_TOLERANCE_EV`` and both limits satisfied) and ``target_reachable`` (the target band
    gap lies inside ``reachable_band_gap_range``; the same for every row).
    """
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    lo, hi = reachable_band_gap_range(baseline, structure)
    reachable = lo - REACHABLE_TOLERANCE_EV <= desired.target_band_gap_ev <= hi + REACHABLE_TOLERANCE_EV
    candidates: List[Dict[str, float | bool]] = []
    for temp in _temperature_grid():
        pred = predict_properties(replace(baseline, temperature_c=temp), structure)
        size_nm = (structure.crystallite_size_nm if structure and structure.crystallite_size_nm is not None
                   else estimate_crystallite_size_nm(temp))
        gap_error = abs(pred.band_gap_ev - desired.target_band_gap_ev)
        area_shortfall = max(0.0, desired.min_surface_area_m2_g - pred.specific_surface_area_m2_g)
        size_excess = max(0.0, size_nm - desired.max_particle_size_nm)
        score = gap_error + area_shortfall / 25.0 + size_excess / 10.0
        candidates.append(
            {
                "score": round(score, 4),
                "temperature_c": temp,
                "estimated_crystallite_size_nm": round(size_nm, 2),
                "pred_band_gap_ev": pred.band_gap_ev,
                "pred_surface_area_m2_g": pred.specific_surface_area_m2_g,
                "band_gap_error_ev": round(gap_error, 4),
                "meets_all_targets": gap_error <= REACHABLE_TOLERANCE_EV and area_shortfall == 0.0 and size_excess == 0.0,
                "target_reachable": reachable,
            }
        )
    return sorted(candidates, key=lambda item: (item["score"], item["temperature_c"]))[:top_k]
