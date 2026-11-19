"""
CIF / XRD reader and line-broadening analysis.

Continuous scans (>= 50 points, step <= 0.1 deg 2theta, Cu K-alpha) are analysed as follows:

1. Background: rolling 20th percentile over +/- 3 deg, then smoothed.
2. Optional K-alpha2 removal by the Rachinger (1948) recursion, I1(x) = I(x) - 0.5 * I1(x - d),
   d = 2 tan(theta) * (lambda2 - lambda1) / lambda1.
3. Peak detection on the smoothed, background-subtracted profile: local maxima higher than
   five times the noise level and 3 % of the strongest peak. The noise level is estimated from
   second differences of the raw intensities.
4. Width: full width at half maximum (FWHM) by linear interpolation. A peak is *resolved* only
   if the profile falls to half maximum on both sides before the neighbouring peak is reached and
   the two half-widths agree within a factor of two, the width spans at least three steps, the
   height exceeds ten times the noise level, and no other peak lies within 2.5 widths.
   Unresolved peaks are excluded.
5. Instrumental broadening, when supplied, is removed in quadrature (Gaussian approximation).
6. Size and strain: Williamson-Hall (1953), beta cos(theta) = K lambda / D + 4 eps sin(theta),
   when at least four resolved peaks are available and the fitted strain exceeds twice its
   standard error; otherwise the intensity-weighted Scherrer size (K = 0.9) with no strain.

Peak lists and CIF files carry no line widths, so no size or strain is reported for them.
Lattice parameters are read from CIF ``_cell_length_*`` tags only. A defect index cannot be
obtained from a diffraction pattern and is never set here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from math import radians
from typing import Dict, List, Optional, Tuple

import numpy as np

from thanimampro_api.schemas import StructureFeatures

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"

CU_KA1_ANGSTROM = 1.540562
CU_KA2_ANGSTROM = 1.544390
SCHERRER_K = 0.9
MIN_SCAN_POINTS = 50
MAX_SCAN_STEP_DEG = 0.1
MIN_WH_PEAKS = 4

# Strongest Cu K-alpha reflections (2theta, deg) of the phases that can be recognised.
REFERENCE_PEAKS: Dict[str, List[float]] = {
    "anatase": [25.28, 37.80, 48.05, 53.89, 55.06, 62.69],
    "rutile": [27.45, 36.09, 41.23, 54.32, 56.64, 69.01],
    "perovskite": [22.76, 32.40, 39.97, 46.48, 57.79],  # cubic SrTiO3
    "spinel": [30.10, 35.46, 43.10, 57.00, 62.60],  # NiFe2O4-type
}


@dataclass
class Peak:
    two_theta: float
    intensity: float  # height above background
    fwhm: Optional[float]  # degrees 2theta; None when the width cannot be measured
    resolved: bool = False  # True when the peak is separated from its neighbours


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


read_pattern = _read_pattern  # public alias for plotting


def _cell_length(tag: str, text: str) -> Optional[float]:
    match = re.search(rf"_cell_length_{tag}\s+({_NUM})", text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return round(value, 4) if 0.0 < value < 1e4 else None


def _phase_from_text(text: str) -> Optional[str]:
    lowered = text.lower()
    found = [phase for phase in REFERENCE_PEAKS if phase in lowered]
    return " + ".join(found) if found else None


def _scan_arrays(rows: List[Tuple[float, float]]) -> Tuple[np.ndarray, np.ndarray]:
    pts = sorted(rows)
    x = np.array([p[0] for p in pts])
    y = np.array([p[1] for p in pts])
    keep = np.concatenate(([True], np.diff(x) > 0))  # drop repeated angles
    return x[keep], y[keep]


def is_continuous_scan(rows: List[Tuple[float, float]]) -> bool:
    if len(rows) < MIN_SCAN_POINTS:
        return False
    x, _ = _scan_arrays(rows)
    return len(x) >= MIN_SCAN_POINTS and float(np.median(np.diff(x))) <= MAX_SCAN_STEP_DEG


def _moving_average(y: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return y.copy()
    pad = k // 2
    return np.convolve(np.pad(y, pad, mode="edge"), np.ones(k) / k, mode="valid")


def _background(y: np.ndarray, half_window: int) -> np.ndarray:
    padded = np.pad(y, half_window, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, 2 * half_window + 1)
    return _moving_average(np.percentile(windows, 20, axis=1), 2 * (half_window // 2) + 1)


def _noise_sigma(y: np.ndarray) -> float:
    d2 = np.diff(y, n=2)
    if len(d2) == 0:
        return 0.0
    mad = float(np.median(np.abs(d2 - np.median(d2))))
    return 1.4826 * mad / np.sqrt(6.0)


def _strip_ka2(x: np.ndarray, net: np.ndarray) -> np.ndarray:
    """Rachinger recursion on a background-subtracted profile (K-alpha2 : K-alpha1 = 0.5)."""
    ratio = (CU_KA2_ANGSTROM - CU_KA1_ANGSTROM) / CU_KA1_ANGSTROM
    shift = np.degrees(2.0 * np.tan(np.radians(x / 2.0)) * ratio)
    out = np.zeros_like(net)
    for i in range(len(x)):
        target = x[i] - shift[i]
        j = int(np.searchsorted(x, target))
        if j <= 0 or j > i:
            previous = 0.0
        else:
            frac = (target - x[j - 1]) / (x[j] - x[j - 1])
            previous = out[j - 1] + frac * (out[j] - out[j - 1]) if j < i else out[j - 1]
        out[i] = net[i] - 0.5 * previous
    return out


def _half_maximum_width(x: np.ndarray, profile: np.ndarray, i: int, lo: int, hi: int) -> Tuple[Optional[float], Optional[float]]:
    """Left and right half-maximum positions of the peak at index ``i`` within (lo, hi)."""
    half = profile[i] / 2.0
    left = right = None
    for j in range(i, lo, -1):
        if profile[j - 1] <= half:
            left = x[j - 1] + (half - profile[j - 1]) * (x[j] - x[j - 1]) / (profile[j] - profile[j - 1])
            break
    for j in range(i, hi):
        if profile[j + 1] <= half:
            right = x[j] + (profile[j] - half) * (x[j + 1] - x[j]) / (profile[j] - profile[j + 1])
            break
    return left, right


def detect_peaks(rows: List[Tuple[float, float]], strip_ka2: bool = False) -> List[Peak]:
    """Peaks of a continuous scan with FWHM and a resolved / unresolved flag (see module docstring)."""
    if len(rows) < 7:
        return []
    x, y = _scan_arrays(rows)
    if len(x) < 7:
        return []
    step = float(np.median(np.diff(x)))
    sigma = _noise_sigma(y)
    # The 20th percentile of Gaussian noise lies 0.84 sigma below its mean; add that back.
    net = y - (_background(y, max(3, int(round(3.0 / step)))) + 0.8416 * sigma)
    if strip_ka2:
        net = _strip_ka2(x, net)
    k = int(min(11, max(3, 2 * round(0.05 / step) + 1)))
    smooth = _moving_average(net, k)
    top = float(smooth.max())
    if top <= 0:
        return []
    threshold = max(5.0 * sigma / np.sqrt(k), 0.03 * top)
    w = max(2, int(round(0.15 / step)))

    maxima: List[int] = []
    for i in range(w, len(x) - w):
        window = smooth[i - w:i + w + 1]
        if smooth[i] >= threshold and smooth[i] == window.max() and smooth[i] > smooth[i - 1]:
            maxima.append(i)

    peaks: List[Peak] = []
    for n, i in enumerate(maxima):
        lo = maxima[n - 1] if n > 0 else 0
        hi = maxima[n + 1] if n + 1 < len(maxima) else len(x) - 1
        left, right = _half_maximum_width(x, smooth, i, lo, hi)
        fwhm, resolved, height, position = None, False, float(smooth[i]), float(x[i])
        if left is not None and right is not None:
            # Re-measure with a smoothing window of at most one fifth of the first width estimate,
            # so that narrow peaks are not broadened by the detection smoothing.
            k2 = int(max(1, min(k, 2 * int((right - left) / step / 10.0) + 1)))
            fine = _moving_average(net, k2)
            j0, j1 = max(lo, i - k), min(hi, i + k)
            apex = j0 + int(np.argmax(fine[j0:j1 + 1]))
            left, right = _half_maximum_width(x, fine, apex, lo, hi)
            if left is not None and right is not None and right > left:
                fwhm, height, position = float(right - left), float(fine[apex]), float(x[apex])
                l_half, r_half = position - left, right - position
                resolved = (l_half > 0 and r_half > 0 and 0.5 <= l_half / r_half <= 2.0
                            and fwhm >= 3.0 * step and height >= 10.0 * sigma / np.sqrt(k2))
        peaks.append(Peak(position, height, fwhm, bool(resolved)))
    # A neighbour closer than 2.5 widths adds its tail to the profile: treat both as unresolved.
    for a, b in zip(peaks, peaks[1:]):
        widths = [p.fwhm for p in (a, b) if p.fwhm]
        if widths and b.two_theta - a.two_theta < 2.5 * max(widths):
            a.resolved = b.resolved = False
    return peaks


def scherrer_williamson_hall(
    peaks: List[Peak], instrumental_fwhm_deg: float = 0.0
) -> Optional[Tuple[float, Optional[float], str, int]]:
    """
    Crystallite size (nm), microstrain (% or None), method and number of peaks used.

    Only resolved peaks enter. ``instrumental_fwhm_deg`` is removed in quadrature. Without it the
    widths include the instrument contribution and the size is underestimated.
    """
    theta, beta, weight = [], [], []
    for p in peaks:
        if not (p.resolved and p.fwhm and 0.02 < p.fwhm < 5.0):
            continue
        sample_sq = p.fwhm ** 2 - instrumental_fwhm_deg ** 2
        if sample_sq <= (0.1 * p.fwhm) ** 2:  # width is essentially instrumental
            continue
        theta.append(radians(p.two_theta / 2.0))
        beta.append(radians(sample_sq ** 0.5))
        weight.append(p.intensity)
    if not theta:
        return None
    th, b, wgt = np.array(theta), np.array(beta), np.array(weight)
    kl = SCHERRER_K * CU_KA1_ANGSTROM / 10.0  # nm
    scherrer = float(np.average(kl / (b * np.cos(th)), weights=wgt))
    if len(th) >= MIN_WH_PEAKS and np.ptp(np.sin(th)) > 0.1:
        xs, ys = 4.0 * np.sin(th), b * np.cos(th)
        slope, intercept = np.polyfit(xs, ys, 1)
        residual = ys - (slope * xs + intercept)
        sxx = float(((xs - xs.mean()) ** 2).sum())
        slope_se = float(np.sqrt((residual ** 2).sum() / (len(xs) - 2) / sxx)) if sxx > 0 else float("inf")
        if intercept > 0 and slope > 2.0 * slope_se and slope * 100.0 >= 0.01:
            return float(kl / intercept), float(slope * 100.0), "Williamson-Hall", len(th)
    return scherrer, None, "Scherrer", len(th)


def match_phases(two_thetas: List[float], tol: float = 0.35) -> List[str]:
    """Reference phases with >= 3 matched reflections and >= 50 % coverage, best match first."""
    scored = []
    for phase, refs in REFERENCE_PEAKS.items():
        hits = sum(any(abs(t - r) <= tol for t in two_thetas) for r in refs)
        if hits >= 3 and hits / len(refs) >= 0.5:
            scored.append((hits / len(refs), phase))
    return [phase for _, phase in sorted(scored, reverse=True)]


def match_phase(two_thetas: List[float], tol: float = 0.35) -> Optional[str]:
    """Best-matching single phase, or None (kept for backward compatibility)."""
    phases = match_phases(two_thetas, tol)
    return phases[0] if phases else None


def analyze_structure_file(
    filename: str,
    content: bytes,
    instrumental_fwhm_deg: float = 0.0,
    strip_ka2: bool = False,
) -> StructureFeatures:
    """
    Read a CIF or an XRD text file (two numeric columns: 2theta in degrees, intensity).

    Returns only what the file determines; every other descriptor is ``None`` and the reason is
    given in ``notes``. See the module docstring for the analysis of continuous scans.
    """
    if instrumental_fwhm_deg < 0.0 or not np.isfinite(instrumental_fwhm_deg):
        raise ValueError("instrumental_fwhm_deg must be a non-negative finite number")
    decoded = content.decode("utf-8", errors="ignore")
    source = "CIF" if filename.lower().endswith(".cif") else "XRD/text"
    notes: List[str] = []

    lattice_a = _cell_length("a", decoded)
    lattice_b = _cell_length("b", decoded)
    lattice_c = _cell_length("c", decoded)
    if lattice_a is None:
        notes.append("No CIF cell tags in the file, so lattice parameters are not available.")

    rows = _read_pattern(decoded)
    size = strain = None
    size_method, n_peaks, n_used = "none", 0, 0
    phases: List[str] = []

    if is_continuous_scan(rows):
        peaks = detect_peaks(rows, strip_ka2=strip_ka2)
        n_peaks = len(peaks)
        phases = match_phases([p.two_theta for p in peaks])
        sizing = peaks
        if len(phases) > 1:  # mixture: size the best-matched phase only
            refs = REFERENCE_PEAKS[phases[0]]
            sizing = [p for p in peaks if any(abs(p.two_theta - r) <= 0.35 for r in refs)]
            notes.append(f"More than one phase matched; size and strain refer to {phases[0]}.")
        fit = scherrer_williamson_hall(sizing, instrumental_fwhm_deg)
        if fit:
            size, strain, size_method, n_used = min(max(fit[0], 1.0), 500.0), fit[1], fit[2], fit[3]
            if strain is None:
                notes.append("Microstrain not reported: it needs a Williamson-Hall fit on at least "
                             f"{MIN_WH_PEAKS} resolved peaks with a strain above twice its standard error.")
            if instrumental_fwhm_deg == 0.0:
                notes.append("No instrumental broadening supplied; the size is underestimated by the instrument contribution.")
            if not strip_ka2:
                notes.append("K-alpha2 not removed; if the scan contains it, enable stripping.")
        elif peaks:
            notes.append("Peaks were found but none is resolved well enough for a width measurement.")
        else:
            notes.append("No peak rises above the noise threshold.")
    elif len(rows) >= 3:
        n_peaks = len(rows)
        phases = match_phases([r[0] for r in rows])
        notes.append("Peak list without line profiles: crystallite size and microstrain need a continuous scan.")
    elif source == "CIF":
        notes.append("A CIF holds no line profiles: crystallite size and microstrain need a continuous scan.")

    if phases:
        phase = " + ".join(phases)
    else:
        phase = _phase_from_text(decoded)
        if phase:
            notes.append("Phase taken from text in the file, not from peak positions.")
        else:
            phase = "unknown"
            if n_peaks:
                notes.append("Peak positions match none of the reference phases (" + ", ".join(REFERENCE_PEAKS) + ").")

    return StructureFeatures(
        phase=phase,
        lattice_a=lattice_a,
        lattice_b=lattice_b,
        lattice_c=lattice_c,
        crystallite_size_nm=round(size, 2) if size is not None else None,
        microstrain_pct=round(strain, 3) if strain is not None else None,
        defect_index=None,
        source=source,
        size_method=size_method,
        n_peaks=n_peaks,
        n_peaks_used=n_used,
        notes=" ".join(notes),
    )
