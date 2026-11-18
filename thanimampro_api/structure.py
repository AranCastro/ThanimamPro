from __future__ import annotations

import re
from dataclasses import dataclass
from math import cos, radians, sin
from statistics import median
from typing import Dict, List, Optional, Tuple

import numpy as np

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


CU_KA1_ANGSTROM = 1.5406
SCHERRER_K = 0.9

# Strongest Cu K-alpha reflections (2theta, deg) of common phases, for peak-matching phase ID.
REFERENCE_PEAKS: Dict[str, List[float]] = {
    "anatase": [25.28, 37.80, 48.05, 53.89, 55.06, 62.69],
    "rutile": [27.45, 36.09, 41.23, 54.32, 56.64, 69.01],
    "perovskite": [22.76, 32.40, 39.97, 46.48, 57.79],  # cubic SrTiO3
    "spinel": [30.10, 35.46, 43.10, 57.00, 62.60],  # NiFe2O4-type
}


@dataclass
class Peak:
    two_theta: float
    intensity: float
    fwhm: Optional[float]  # degrees 2theta; None when the width cannot be measured


def detect_peaks(rows: List[Tuple[float, float]]) -> List[Peak]:
    """Peaks of a continuous scan (local maxima, FWHM by half-maximum interpolation)."""
    pts = sorted(rows)
    x = np.array([p[0] for p in pts])
    y = np.array([p[1] for p in pts])
    if len(x) < 5:
        return []
    base = float(np.median(y))
    top = float(y.max())
    if top - base <= 0:
        return []
    floor = base + 0.1 * (top - base)
    peaks: List[Peak] = []
    w = 3
    for i in range(w, len(x) - w):
        if y[i] < floor or y[i] != y[i - w:i + w + 1].max() or y[i] == y[i - 1]:
            continue
        half = base + (y[i] - base) / 2.0
        left = right = None
        for j in range(i, 0, -1):
            if y[j - 1] <= half:
                left = x[j - 1] + (half - y[j - 1]) * (x[j] - x[j - 1]) / (y[j] - y[j - 1])
                break
        for j in range(i, len(x) - 1):
            if y[j + 1] <= half:
                right = x[j] + (y[j] - half) * (x[j + 1] - x[j]) / (y[j] - y[j + 1])
                break
        fwhm = float(right - left) if left is not None and right is not None else None
        peaks.append(Peak(float(x[i]), float(y[i]), fwhm))
    return peaks


def scherrer_williamson_hall(peaks: List[Peak]) -> Optional[Tuple[float, Optional[float], str]]:
    """
    Crystallite size (nm) and microstrain (%) from peak widths.

    Uses Williamson-Hall (beta cos(theta) = K*lambda/D + 4*eps*sin(theta)) with >= 3 peaks when the
    fit is physical, otherwise the intensity-weighted Scherrer size. Widths are not corrected for
    instrumental broadening, so sizes are lower bounds.
    """
    valid = [p for p in peaks if p.fwhm and 0.02 < p.fwhm < 5.0]
    if not valid:
        return None
    theta = np.array([radians(p.two_theta / 2.0) for p in valid])
    beta = np.array([radians(p.fwhm) for p in valid])
    kl = SCHERRER_K * CU_KA1_ANGSTROM / 10.0  # nm
    sizes = kl / (beta * np.cos(theta))
    weights = np.array([p.intensity for p in valid])
    if len(valid) >= 3 and np.ptp(np.sin(theta)) > 0.05:
        slope, intercept = np.polyfit(4.0 * np.sin(theta), beta * np.cos(theta), 1)
        if intercept > 0 and slope >= 0:
            return float(kl / intercept), float(slope * 100.0), "Williamson-Hall"
    return float(np.average(sizes, weights=weights)), None, "Scherrer"


def match_phase(two_thetas: List[float], tol: float = 0.35) -> Optional[str]:
    """Phase whose reference reflections are best matched (needs >= 3 matches and >= 50 % coverage)."""
    best, best_hits = None, 0
    for phase, refs in REFERENCE_PEAKS.items():
        hits = sum(any(abs(t - r) <= tol for t in two_thetas) for r in refs)
        if hits > best_hits and hits >= 3 and hits / len(refs) >= 0.5:
            best, best_hits = phase, hits
    return best


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

    rows = _read_pattern(decoded)
    peak_count = _count_peaks(rows)
    crystallite_size = max(6.0, 60.0 - 0.9 * peak_count)
    microstrain = min(2.5, 0.1 + 0.02 * peak_count)
    size_method = "heuristic"
    phase = _infer_phase(decoded)

    if len(rows) >= 50:  # continuous scan: measure peak widths
        peaks = detect_peaks(rows)
        peak_count = len(peaks) or peak_count
        fit = scherrer_williamson_hall(peaks)
        if fit:
            crystallite_size = min(max(fit[0], 1.0), 500.0)
            if fit[1] is not None:
                microstrain = min(fit[1], 5.0)
            size_method = fit[2]
        matched = match_phase([p.two_theta for p in peaks])
        if matched:
            phase = matched
    elif len(rows) >= 3:
        matched = match_phase([r[0] for r in rows])
        if matched:
            phase = matched

    defect_words = ["vacancy", "defect", "oxygen-deficient", "disorder"]
    defect_hits = sum(decoded.lower().count(word) for word in defect_words)
    defect_index = min(1.0, 0.1 + 0.12 * defect_hits + 0.02 * peak_count)

    return StructureFeatures(
        phase=phase,
        lattice_a=round(max(lattice_a, 0.0), 4),
        lattice_b=round(max(lattice_b, 0.0), 4),
        lattice_c=round(max(lattice_c, 0.0), 4),
        crystallite_size_nm=round(crystallite_size, 2),
        microstrain_pct=round(microstrain, 3),
        defect_index=round(defect_index, 3),
        source=source,
        size_method=size_method,
        n_peaks=peak_count,
    )

read_pattern = _read_pattern  # public alias for UI plotting
