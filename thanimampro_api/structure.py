from __future__ import annotations

import re

from thanimampro_api.schemas import StructureFeatures


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
    if "anatase" in lowered:
        return "anatase"
    if "rutile" in lowered:
        return "rutile"
    if "perovskite" in lowered:
        return "perovskite"
    if "spinel" in lowered:
        return "spinel"
    return "mixed/unknown"


def analyze_structure_file(filename: str, content: bytes) -> StructureFeatures:
    """
    Lightweight parser for CIF/XRD text content.
    """
    decoded = content.decode("utf-8", errors="ignore")
    source = "CIF" if filename.lower().endswith(".cif") else "XRD/text"

    lattice_a = _first_float(r"_cell_length_a\s+([0-9.]+)", decoded, 3.78)
    lattice_b = _first_float(r"_cell_length_b\s+([0-9.]+)", decoded, lattice_a)
    lattice_c = _first_float(r"_cell_length_c\s+([0-9.]+)", decoded, 9.45)

    # Fallbacks driven by rough peak count to keep this useful for quick demos.
    peak_like_values = re.findall(r"\b[0-9]{1,2}\.[0-9]{2,}\b", decoded)
    peak_count = len(peak_like_values)
    crystallite_size = max(6.0, 60.0 - 0.9 * peak_count)
    microstrain = min(2.5, 0.1 + 0.02 * peak_count)

    defect_words = ["vacancy", "defect", "oxygen-deficient", "disorder"]
    defect_hits = sum(decoded.lower().count(word) for word in defect_words)
    defect_index = min(1.0, 0.1 + 0.12 * defect_hits + 0.02 * peak_count)

    return StructureFeatures(
        phase=_infer_phase(decoded),
        lattice_a=round(lattice_a, 4),
        lattice_b=round(lattice_b, 4),
        lattice_c=round(lattice_c, 4),
        crystallite_size_nm=round(crystallite_size, 2),
        microstrain_pct=round(microstrain, 3),
        defect_index=round(defect_index, 3),
        source=source,
    )
