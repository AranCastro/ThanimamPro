"""Validate a literature CSV before it is placed at data/literature_seed.csv.

Usage: python scripts/validate_literature_csv.py path/to/file.csv
Exit status 0 = no errors (warnings may remain); 1 = errors found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

REQUIRED = ["material_system", "method", "temperature_c", "pH", "band_gap_ev", "surface_area_m2_g", "doi"]
RANGES = {"temperature_c": (0, 3000), "pH": (0, 14), "band_gap_ev": (0, 12), "surface_area_m2_g": (0, 3000)}
METHODS = {"sol-gel", "hydrothermal", "co-precipitation", "solid-state", "combustion", "other"}
TEMPERATURE_TYPES = {"calcination", "hydrothermal", "combustion"}
TRANSITIONS = {"direct", "indirect", "other"}
DOI = re.compile(r"^10\.\d{4,9}/\S+$")


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    frame = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        return [f"missing columns: {missing}"], warnings
    for col, (lo, hi) in RANGES.items():
        values = pd.to_numeric(frame[col], errors="coerce")
        bad = frame[col].notna() & values.isna()
        for i in frame.index[bad]:
            errors.append(f"row {i + 2}: {col} is not numeric ({frame.at[i, col]!r})")
        for i in values.index[(values < lo) | (values > hi)]:
            errors.append(f"row {i + 2}: {col}={values[i]} outside [{lo}, {hi}]")
    for i, doi in frame["doi"].items():
        if pd.isna(doi) or not DOI.match(str(doi).strip()):
            errors.append(f"row {i + 2}: doi missing or malformed ({doi!r}); give the bare DOI, e.g. 10.xxxx/yyyy")
    for i, m in frame["method"].items():
        if str(m).strip().lower() not in METHODS:
            warnings.append(f"row {i + 2}: method {m!r} not in {sorted(METHODS)} (use 'other' if none fits)")
    for i in frame.index[frame["material_system"].isna()]:
        errors.append(f"row {i + 2}: material_system is empty")
    if "temperature_type" in frame.columns:  # optional column; if present it must be filled and valid
        for i, t in frame["temperature_type"].items():
            if str(t).strip().lower() not in TEMPERATURE_TYPES:
                errors.append(f"row {i + 2}: temperature_type {t!r} not in {sorted(TEMPERATURE_TYPES)}")
    if "band_gap_transition" in frame.columns:  # optional; required wherever a band gap is given
        for i in frame.index:
            has_gap = pd.notna(frame.at[i, "band_gap_ev"])
            t = frame.at[i, "band_gap_transition"]
            if has_gap and str(t).strip().lower() not in TRANSITIONS:
                errors.append(f"row {i + 2}: band_gap_transition {t!r} not in {sorted(TRANSITIONS)}")
            if not has_gap and pd.notna(t):
                errors.append(f"row {i + 2}: band_gap_transition given without a band gap")
    dup = frame.duplicated(keep="first")
    for i in frame.index[dup]:
        warnings.append(f"row {i + 2}: exact duplicate of an earlier row")
    return errors, warnings


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    errs, warns = validate(Path(sys.argv[1]))
    for w in warns:
        print("WARNING", w)
    for e in errs:
        print("ERROR  ", e)
    print(f"{len(errs)} error(s), {len(warns)} warning(s)")
    sys.exit(1 if errs else 0)
