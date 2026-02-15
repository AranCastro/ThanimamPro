from __future__ import annotations

from dataclasses import replace

import pandas as pd

from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import StructureFeatures, SynthesisInput


def build_bandgap_map(
    baseline: SynthesisInput,
    structure: StructureFeatures | None,
    temp_min: float,
    temp_max: float,
    ph_min: float,
    ph_max: float,
    points: int = 25,
) -> pd.DataFrame:
    temps = [temp_min + i * (temp_max - temp_min) / max(points - 1, 1) for i in range(points)]
    phs = [ph_min + j * (ph_max - ph_min) / max(points - 1, 1) for j in range(points)]

    rows = []
    for temp in temps:
        for ph in phs:
            trial = replace(baseline, temperature_c=temp, pH=ph)
            pred = predict_properties(trial, structure)
            rows.append(
                {
                    "temperature_c": round(temp, 3),
                    "pH": round(ph, 3),
                    "band_gap_ev": pred.band_gap_ev,
                }
            )
    return pd.DataFrame(rows)
