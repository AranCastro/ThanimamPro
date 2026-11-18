from __future__ import annotations

import re
from statistics import median
from typing import List, Tuple

from thanimampro_api.schemas import StructureFeatures

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_DEFAULT_A, _DEFAULT_C = 3.78, 9.45  # anatase-like priors used when no cell is given


def _first_float(pattern: str, text: str, default: float) -> float:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return default
    try:
        return float(match.group(1))
    except ValueError:
        return default


def _infer_phase(text: str) -> str:
    lowered = text.lower()
    for phase in ("anatase", "rutile", "perovskite", "spinel"):
        if phase in lowered:
            return phase
    return "mixed/unknown"


def _read_pattern(text: str) -> List[Tuple[float, float]]:
    """Return (2theta, intensity) rows from numeric two-column lines; comments are skipped."""
    rows: List[Tuple[float, float]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tokens = re.split(r"[\s,;]+", line)
        if len(tokens) < 2 or not all(re.fullmatch(_NUM, t) for t in tokens[:2]):
            continue
        two_theta, intensity = float(tokens[0]), float(tokens[1])
        if 0.0 < two_theta < 180.0 and intensity >= 0.0:
            rows.append((two_theta, intensity))
    return rows


def _count_peaks(rows: List[Tuple[float, float]]) -> int:
    """Count peaks in a discrete peak list or a continuous scan (local maxima above 5 % of max)."""
    if len(rows) < 3:
        return len(rows)
    rows = sorted(rows)
    spacing = median(b[0] - a[0] for a, b in zip(rows, rows[1:]))
    if spacing > 0.5:  # sparse list: every row is a reported reflection
        return len(rows)
    threshold = 0.05 * max(y for _, y in rows)
    return sum(
        1
        for i in range(1, len(rows) - 1)
        if rows[i][1] >= threshold and rows[i][1] > rows[i - 1][1] and rows[i][1] >= rows[i + 1][1]
    )


def analyze_structure_file(filename: str, content: bytes) -> StructureFeatures:
    """
    Lightweight heuristic parser for CIF / XRD text content.

    Lattice parameters are read from CIF ``_cell_length_*`` tags; without them
    anatase-like priors are used and flagged in ``source``. Crystallite size,
    microstrain and defect index are rough proxies derived from the number of
    diffraction peaks and defect keywords. They are not Scherrer or
    Williamson-Hall results.
    """
    decoded = content.decode("utf-8", errors="ignore")
    is_cif = filename.lower().endswith(".cif")
    source = "CIF" if is_cif else "XRD/text"

    has_cell = bool(re.search(r"_cell_length_a\s", decoded, flags=re.IGNORECASE))
    lattice_a = _first_float(rf"_cell_length_a\s+({_NUM})", decoded, _DEFAULT_A)
    lattice_b = _first_float(rf"_cell_length_b\s+({_NUM})", decoded, lattice_a)
    lattice_c = _first_float(rf"_cell_length_c\s+({_NUM})", decoded, _DEFAULT_C)
    if not has_cell:
        source += " (lattice parameters not found; default priors)"

    peak_count = _count_peaks(_read_pattern(decoded))
    crystallite_size = max(6.0, 60.0 - 0.9 * peak_count)
    microstrain = min(2.5, 0.1 + 0.02 * peak_count)

    defect_words = ["vacancy", "defect", "oxygen-deficient", "disorder"]
    defect_hits = sum(decoded.lower().count(word) for word in defect_words)
    defect_index = min(1.0, 0.1 + 0.12 * defect_hits + 0.02 * peak_count)

    return StructureFeatures(
        phase=_infer_phase(decoded),
        lattice_a=round(max(lattice_a, 0.0), 4),
        lattice_b=round(max(lattice_b, 0.0), 4),
        lattice_c=round(max(lattice_c, 0.0), 4),
        crystallite_size_nm=round(crystallite_size, 2),
        microstrain_pct=round(microstrain, 3),
        defect_index=round(defect_index, 3),
        source=source,
    )
