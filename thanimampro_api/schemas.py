from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Dict, Literal, Optional, get_args

SynthesisMethod = Literal[
    "sol-gel",
    "hydrothermal",
    "co-precipitation",
    "solid-state",
    "combustion",
    "other",
]

SYNTHESIS_METHODS = get_args(SynthesisMethod)


def _require_finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}")


@dataclass
class SynthesisInput:
    temperature_c: float
    heating_rate_c_min: float
    annealing_time_h: float
    atmosphere: str
    precursor_ratio: float
    pH: float
    solvent_type: str
    concentration_m: float
    pressure_bar: float
    milling_time_h: float
    calcination_time_h: float
    method: SynthesisMethod
    material_system: str = "TiO2"

    def __post_init__(self) -> None:
        numeric = (
            "temperature_c", "heating_rate_c_min", "annealing_time_h", "precursor_ratio",
            "pH", "concentration_m", "pressure_bar", "milling_time_h", "calcination_time_h",
        )
        for name in numeric:
            _require_finite(name, getattr(self, name))
        if not 0.0 <= self.temperature_c <= 3000.0:
            raise ValueError("temperature_c must lie between 0 and 3000 degC")
        if not 0.0 <= self.pH <= 14.0:
            raise ValueError("pH must lie between 0 and 14")
        for name in ("heating_rate_c_min", "annealing_time_h", "milling_time_h",
                     "calcination_time_h", "pressure_bar", "concentration_m"):
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name} must be non-negative")
        if self.precursor_ratio <= 0.0:
            raise ValueError("precursor_ratio must be positive")
        if self.method not in SYNTHESIS_METHODS:
            raise ValueError(f"method must be one of {SYNTHESIS_METHODS}, got {self.method!r}")

    def to_dict(self) -> Dict[str, float | str]:
        return asdict(self)


@dataclass
class StructureFeatures:
    """
    Descriptors read or measured from a CIF / XRD file.

    A field is ``None`` when the file does not determine it: lattice parameters need CIF
    ``_cell_length_*`` tags; crystallite size needs a continuous scan with resolved peaks;
    microstrain needs a Williamson-Hall fit. ``defect_index`` (0 to 1) cannot be derived from a
    diffraction pattern and is only set when the user supplies an estimate.
    """

    phase: str
    lattice_a: Optional[float] = None
    lattice_b: Optional[float] = None
    lattice_c: Optional[float] = None
    crystallite_size_nm: Optional[float] = None
    microstrain_pct: Optional[float] = None
    defect_index: Optional[float] = None
    source: str = ""
    size_method: str = "none"  # "Williamson-Hall", "Scherrer" or "none"
    n_peaks: int = 0  # peaks detected
    n_peaks_used: int = 0  # resolved peaks used for the size / strain estimate
    notes: str = ""

    def __post_init__(self) -> None:
        for name in ("lattice_a", "lattice_b", "lattice_c", "crystallite_size_nm",
                     "microstrain_pct", "defect_index"):
            if getattr(self, name) is not None:
                _require_finite(name, getattr(self, name))
        for name in ("lattice_a", "lattice_b", "lattice_c", "crystallite_size_nm"):
            if getattr(self, name) is not None and getattr(self, name) <= 0.0:
                raise ValueError(f"{name} must be positive")
        if self.defect_index is not None and not 0.0 <= self.defect_index <= 1.0:
            raise ValueError("defect_index must lie between 0 and 1")

    def to_dict(self) -> Dict[str, float | str | None]:
        return asdict(self)


@dataclass
class PredictedProperties:
    """
    ``band_gap_ev``, ``absorption_edge_nm`` and ``specific_surface_area_m2_g`` are calibrated
    against the literature table (see ``thanimampro_api.predict``). The remaining fields are
    illustrative and unvalidated. The two magnetic fields are ``None`` unless the material
    system contains a magnetic cation.
    """

    band_gap_ev: float
    conductivity_s_cm: float
    absorption_edge_nm: float
    photoluminescence_intensity_au: float
    specific_surface_area_m2_g: float
    active_site_density_mm2_g: float
    capacitance_f_g: float
    ion_diffusivity_cm2_s: float
    curie_temperature_k: Optional[float] = None
    saturation_magnetization_emu_g: Optional[float] = None

    def to_dict(self) -> Dict[str, Optional[float]]:
        return asdict(self)


CALIBRATED_PROPERTIES = ("band_gap_ev", "absorption_edge_nm", "specific_surface_area_m2_g")


@dataclass
class DesiredPropertyTargets:
    target_band_gap_ev: float
    min_surface_area_m2_g: float
    max_particle_size_nm: float  # compared with the estimated crystallite size

    def __post_init__(self) -> None:
        for name in ("target_band_gap_ev", "min_surface_area_m2_g", "max_particle_size_nm"):
            _require_finite(name, getattr(self, name))
        if self.target_band_gap_ev <= 0.0:
            raise ValueError("target_band_gap_ev must be positive")
        if self.min_surface_area_m2_g < 0.0:
            raise ValueError("min_surface_area_m2_g must be non-negative")
        if self.max_particle_size_nm <= 0.0:
            raise ValueError("max_particle_size_nm must be positive")
