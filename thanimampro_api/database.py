from __future__ import annotations

from pathlib import Path

import pandas as pd

COLUMNS = [
    "material_system",
    "method",
    "temperature_c",
    "pH",
    "band_gap_ev",
    "surface_area_m2_g",
    "doi",
]


def load_literature_data(csv_path: str | Path) -> pd.DataFrame:
    """Load the literature table; a missing file yields an empty frame with the standard columns."""
    path = Path(csv_path)
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    frame = pd.read_csv(path)
    for column in COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    for column in ("temperature_c", "pH", "band_gap_ev", "surface_area_m2_g"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def search_literature(
    frame: pd.DataFrame,
    material_system: str = "",
    method: str = "",
    min_band_gap: float | None = None,
    max_band_gap: float | None = None,
) -> pd.DataFrame:
    """Filter records; text filters are literal, case-insensitive substring matches."""
    filtered = frame.copy()
    if material_system:
        mask = filtered["material_system"].astype("string").str.contains(
            material_system, case=False, regex=False, na=False
        )
        filtered = filtered[mask]
    if method:
        mask = filtered["method"].astype("string").str.contains(method, case=False, regex=False, na=False)
        filtered = filtered[mask]
    if min_band_gap is not None:
        filtered = filtered[filtered["band_gap_ev"] >= min_band_gap]
    if max_band_gap is not None:
        filtered = filtered[filtered["band_gap_ev"] <= max_band_gap]
    return filtered.reset_index(drop=True)
