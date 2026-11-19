from __future__ import annotations

from dataclasses import replace
from itertools import product
from typing import Dict, List

from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import DesiredPropertyTargets, StructureFeatures, SynthesisInput


def _score_candidate(pred: Dict[str, float], desired: DesiredPropertyTargets, particle_size_nm: float) -> float:
    band_gap_error = abs(pred["band_gap_ev"] - desired.target_band_gap_ev)
    surface_area_penalty = max(0.0, desired.min_surface_area_m2_g - pred["specific_surface_area_m2_g"]) / 25.0
    size_penalty = max(0.0, particle_size_nm - desired.max_particle_size_nm) / 10.0
    return band_gap_error + surface_area_penalty + size_penalty


def suggest_synthesis_conditions(
    baseline: SynthesisInput,
    desired: DesiredPropertyTargets,
    structure: StructureFeatures | None = None,
    top_k: int = 5,
) -> List[Dict[str, float | str]]:
    """
    Grid search over temperature, pH and calcination time.

    Annealing time is held at the baseline value because the surrogate model does
    not depend on it; scanning it would only return duplicate candidates.
    """
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    temp_grid = [450.0, 550.0, 650.0, 750.0, 850.0]
    ph_grid = [3.0, 5.0, 7.0, 9.0, 11.0]
    calcination_grid = [1.0, 2.0, 3.0, 5.0]

    candidates: List[Dict[str, float | str]] = []
    for temp, ph, calc_time in product(temp_grid, ph_grid, calcination_grid):
        trial = replace(
            baseline,
            temperature_c=temp,
            pH=ph,
            calcination_time_h=calc_time,
        )
        pred = predict_properties(trial, structure).to_dict()
        particle_size_nm = max(5.0, 80.0 - 0.07 * temp + 1.2 * calc_time - 1.8 * ph)
        score = _score_candidate(pred, desired, particle_size_nm)
        candidates.append(
            {
                "score": round(score, 4),
                "temperature_c": temp,
                "pH": ph,
                "annealing_time_h": baseline.annealing_time_h,
                "calcination_time_h": calc_time,
                "estimated_particle_size_nm": round(particle_size_nm, 2),
                "pred_band_gap_ev": pred["band_gap_ev"],
                "pred_surface_area_m2_g": pred["specific_surface_area_m2_g"],
            }
        )

    ranked = sorted(
        candidates,
        key=lambda item: (item["score"], item["temperature_c"], item["pH"], item["calcination_time_h"]),
    )
    # Candidates with identical predicted outcomes (e.g. particle size clamped at its floor) are
    # collapsed, keeping the first in rank order, i.e. the shortest calcination time.
    unique: List[Dict[str, float | str]] = []
    seen = set()
    for item in ranked:
        outcome = (item["temperature_c"], item["pH"], item["score"], item["estimated_particle_size_nm"])
        if outcome in seen:
            continue
        seen.add(outcome)
        unique.append(item)
    return unique[:top_k]
