from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Literal

SynthesisMethod = Literal[
    "sol-gel",
    "hydrothermal",
    "co-precipitation",
    "solid-state",
    "combustion",
    "other",
]


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

