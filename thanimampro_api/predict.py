from __future__ import annotations

import re
from math import exp, log10
from typing import List, Optional

from thanimampro_api.schemas import PredictedProperties, StructureFeatures, SynthesisInput

# --- Calibration (scripts/fit_surrogate.py on data/literature_seed.csv; ordinary least squares) ---
# Band gap (eV) = BG_INTERCEPT + BG_PER_DEGC * (T - 600) + BG_DOPED * doped
#   n = 76 rows, 19 papers; leave-one-paper-out MAE 0.145 eV, R2 0.35 (constant predictor: 0.186 eV, -0.08)
BG_INTERCEPT, BG_PER_DEGC, BG_DOPED = 3.07803, -0.000576523, -0.308397
# log10(BET area, m2/g) = SA_LOG_INTERCEPT + SA_LOG_PER_DEGC * (T - 500); calcination rows
#   n = 95 rows, 20 papers; leave-one-paper-out MAE 46.5 m2/g, R2 -0.13 (constant: 55.8 m2/g, -0.42)
SA_LOG_INTERCEPT, SA_LOG_PER_DEGC = 1.597, -0.00342217
# log10(crystallite size, nm) = CS_LOG_INTERCEPT + CS_LOG_PER_DEGC * (T - 500); calcination rows
#   n = 60 rows, 13 papers; leave-one-paper-out MAE 9.0 nm, R2 0.18 (constant: 10.6 nm, -0.15)
CS_LOG_INTERCEPT, CS_LOG_PER_DEGC = 1.23428, 0.0013027
# Geometric area of dense spheres, S = 6000 / (rho * D), used when a crystallite size was measured.
#   Parameter-free; n = 55 rows, 10 papers: MAE 33.7 m2/g, bias +24.7 m2/g, R2 0.48 (an upper bound:
#   agglomeration and sintering necks lower the measured area).
ANATASE_DENSITY_G_CM3 = 3.9
CALIBRATION_T_RANGE_C = (200.0, 1100.0)

DEFAULT_DEFECT_INDEX = 0.25
_MAGNETIC_CATIONS = re.compile(r"(Fe|Co|Ni|Mn|Cr|Gd)(?![a-z])")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def is_doped(material_system: str) -> bool:
    """Dopants follow a colon in the dataset convention, e.g. ``TiO2:Fe``."""
    return ":" in material_system


def is_supported_material(material_system: str) -> bool:
    """The calibration covers TiO2 and doped TiO2 only."""
    return material_system.split(":")[0].strip().lower() == "tio2"


def estimate_crystallite_size_nm(temperature_c: float) -> float:
    """Crystallite size expected after calcination at ``temperature_c`` (literature fit)."""
    return _clamp(10 ** (CS_LOG_INTERCEPT + CS_LOG_PER_DEGC * (temperature_c - 500.0)), 1.0, 500.0)


def scope_warnings(synthesis: SynthesisInput) -> List[str]:
    """Reasons why a prediction for these conditions lies outside the calibrated domain."""
    out: List[str] = []
    if not is_supported_material(synthesis.material_system):
        out.append(
            f"The calibration covers TiO2 and doped TiO2 (written 'TiO2:Fe'). Values shown for "
            f"'{synthesis.material_system}' are TiO2 values and do not describe that material."
        )
    if synthesis.method == "hydrothermal":
        out.append("The temperature is read as a calcination temperature. Hydrothermal reaction "
                   "temperatures are not calibrated (14 literature rows from three papers).")
    lo, hi = CALIBRATION_T_RANGE_C
    if not lo <= synthesis.temperature_c <= hi:
        out.append(f"Temperature {synthesis.temperature_c:g} degC is outside the calibrated range "
                   f"{lo:g}-{hi:g} degC; the prediction is an extrapolation.")
    return out


def predict_properties(
    synthesis: SynthesisInput,
    structure: StructureFeatures | None = None,
) -> PredictedProperties:
    """
    Surrogate for synthesis -> structure -> property behaviour of TiO2 and doped TiO2.

    Calibrated outputs (coefficients and held-out errors in the module constants):
      * ``band_gap_ev``: linear in temperature, with an offset for doped samples. The literature
        table does not support a pH term (pH is reported for 27 of 137 rows), so pH has no effect.
      * ``specific_surface_area_m2_g``: geometric area from the measured crystallite size when a
        structure file supplied one; otherwise a log-linear fit to calcination temperature, which
        is no better than a constant on held-out papers by R2 and is shown for orientation only.
      * ``absorption_edge_nm`` = 1239.84 / band gap.

    The other outputs are illustrative hand-set expressions with no experimental validation. They
    use temperature, pH, pressure and, when the user supplies one, the defect index. Heating rate,
    annealing, calcination and milling time, atmosphere, precursor ratio, solvent, concentration
    and method are stored but do not enter any expression. Curie temperature and saturation
    magnetisation are returned only for systems that contain Fe, Co, Ni, Mn, Cr or Gd.
    """
    s = synthesis
    defect_factor = DEFAULT_DEFECT_INDEX
    measured_size: Optional[float] = None
    if structure is not None:
        if structure.defect_index is not None:
            defect_factor = structure.defect_index
        measured_size = structure.crystallite_size_nm
    crystallite_size = measured_size if measured_size is not None else estimate_crystallite_size_nm(s.temperature_c)

    band_gap = BG_INTERCEPT + BG_PER_DEGC * (s.temperature_c - 600.0) + (BG_DOPED if is_doped(s.material_system) else 0.0)
    band_gap = _clamp(band_gap, 1.1, 4.5)
    absorption_edge = 1239.84 / band_gap

    if measured_size is not None:
        surface_area = 6000.0 / (ANATASE_DENSITY_G_CM3 * measured_size)
    else:
        surface_area = 10 ** (SA_LOG_INTERCEPT + SA_LOG_PER_DEGC * (s.temperature_c - 500.0))
    surface_area = _clamp(surface_area, 0.5, 400.0)

    # ---- illustrative, unvalidated expressions ----
    conductivity = 10 ** _clamp(
        -6.0 + 0.0024 * (s.temperature_c - 550.0) - 0.045 * abs(s.pH - 7.0) + 0.15 * defect_factor,
        -8.0, log10(5.0),
    )
    pl_intensity = _clamp(400.0 * exp(-0.8 * defect_factor) + 2.0 * crystallite_size, 20.0, 1200.0)
    active_site_density = _clamp(0.35 * surface_area * (1.0 + 0.6 * defect_factor), 0.1, 300.0)
    capacitance = _clamp(0.8 * surface_area + 15.0 * defect_factor + 0.05 * s.pressure_bar, 1.0, 900.0)
    ion_diff = _clamp(
        1e-12 * exp(min(0.09 * s.pH + 0.0009 * s.temperature_c + 0.7 * defect_factor, 50.0)),
        1e-13, 1e-6,
    )
    curie_temperature = saturation = None
    if _MAGNETIC_CATIONS.search(s.material_system):
        curie_temperature = round(_clamp(250.0 + 0.35 * s.temperature_c + 30.0 * defect_factor, 10.0, 1500.0), 2)
        saturation = round(_clamp(8.0 + 0.03 * s.temperature_c + 10.0 * defect_factor - 0.2 * crystallite_size, 0.1, 180.0), 2)

    return PredictedProperties(
        band_gap_ev=round(band_gap, 4),
        conductivity_s_cm=round(conductivity, 8),
        absorption_edge_nm=round(absorption_edge, 2),
        photoluminescence_intensity_au=round(pl_intensity, 2),
        specific_surface_area_m2_g=round(surface_area, 2),
        active_site_density_mm2_g=round(active_site_density, 2),
        capacitance_f_g=round(capacitance, 2),
        ion_diffusivity_cm2_s=ion_diff,
        curie_temperature_k=curie_temperature,
        saturation_magnetization_emu_g=saturation,
    )
