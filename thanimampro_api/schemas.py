from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Dict, Literal, get_args

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
    phase: str
    lattice_a: float
    lattice_b: float
    lattice_c: float
    crystallite_size_nm: float
    microstrain_pct: float
    defect_index: float
    source: str

    def __post_init__(self) -> None:
        for name in ("lattice_a", "lattice_b", "lattice_c", "crystallite_size_nm",
                     "microstrain_pct", "defect_index"):
            _require_finite(name, getattr(self, name))
        if self.crystallite_size_nm <= 0.0:
            raise ValueError("crystallite_size_nm must be positive")
        if not 0.0 <= self.defect_index <= 1.0:
            raise ValueError("defect_index must lie between 0 and 1")

    def to_dict(self) -> Dict[str, float | str]:
        return asdict(self)


@dataclass
class PredictedProperties:
    band_gap_ev: float
    conductivity_s_cm: float
    absorption_edge_nm: float
    photoluminescence_intensity_au: float
    specific_surface_area_m2_g: float
    active_site_density_mm2_g: float
    capacitance_f_g: float
    ion_diffusivity_cm2_s: float
    curie_temperature_k: float
    saturation_magnetization_emu_g: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class DesiredPropertyTargets:
    target_band_gap_ev: float
    min_surface_area_m2_g: float
    max_particle_size_nm: float
