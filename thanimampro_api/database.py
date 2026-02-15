from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_literature_data(csv_path: str | Path) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "material_system",
                "method",
                "temperature_c",
                "pH",
                "band_gap_ev",
                "surface_area_m2_g",
                "doi",
            ]
        )
    return pd.read_csv(path)


def search_literature(
    frame: pd.DataFrame,
    material_system: str = "",
    method: str = "",
    min_band_gap: float | None = None,
    max_band_gap: float | None = None,
) -> pd.DataFrame:
    filtered = frame.copy()
    if material_system:
        filtered = filtered[filtered["material_system"].str.contains(material_system, case=False, na=False)]
    if method:
        filtered = filtered[filtered["method"].str.contains(method, case=False, na=False)]
    if min_band_gap is not None:
        filtered = filtered[filtered["band_gap_ev"] >= min_band_gap]
    if max_band_gap is not None:
        filtered = filtered[filtered["band_gap_ev"] <= max_band_gap]
    return filtered.reset_index(drop=True)

