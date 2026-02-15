from __future__ import annotations

from math import exp

from thanimampro_api.schemas import PredictedProperties, StructureFeatures, SynthesisInput


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def predict_properties(
    synthesis: SynthesisInput,
    structure: StructureFeatures | None = None,
) -> PredictedProperties:
    """
    Baseline surrogate model for Synthesis -> Structure -> Property behavior.
    Replace with trained regressors once literature-scale datasets are loaded.
    """
    s = synthesis
    defect_factor = structure.defect_index if structure else 0.25
    crystallite_size = structure.crystallite_size_nm if structure else 28.0

    band_gap = (
        3.2
        - 0.0012 * (s.temperature_c - 600.0)
        - 0.055 * (s.pH - 7.0)
        + 0.03 * defect_factor
    )
    band_gap = _clamp(band_gap, 1.1, 4.5)

    conductivity = 10 ** (
        -6.0
        + 0.0024 * (s.temperature_c - 550.0)
        - 0.045 * abs(s.pH - 7.0)
        + 0.15 * defect_factor
    )
    conductivity = _clamp(conductivity, 1e-8, 5.0)

    absorption_edge = 1240.0 / band_gap
    pl_intensity = _clamp(400.0 * exp(-0.8 * defect_factor) + 2.0 * crystallite_size, 20.0, 1200.0)

    surface_area = (
        90.0
        - 0.06 * (s.temperature_c - 500.0)
        - 0.55 * crystallite_size
        + 1.8 * s.pH
    )
    surface_area = _clamp(surface_area, 2.0, 220.0)
    active_site_density = _clamp(0.35 * surface_area * (1.0 + 0.6 * defect_factor), 5.0, 300.0)

    capacitance = _clamp(
        0.8 * surface_area + 15.0 * defect_factor + 0.05 * s.pressure_bar,
        5.0,
        900.0,
    )
    ion_diff = _clamp(
        1e-12 * exp(0.09 * s.pH + 0.0009 * s.temperature_c + 0.7 * defect_factor),
        1e-13,
        1e-6,
    )

    curie_temperature = _clamp(250.0 + 0.35 * s.temperature_c + 30.0 * defect_factor, 10.0, 1500.0)
    sat_mag = _clamp(8.0 + 0.03 * s.temperature_c + 10.0 * defect_factor - 0.2 * crystallite_size, 0.1, 180.0)

    return PredictedProperties(
        band_gap_ev=round(band_gap, 4),
        conductivity_s_cm=round(conductivity, 8),
        absorption_edge_nm=round(absorption_edge, 2),
        photoluminescence_intensity_au=round(pl_intensity, 2),
        specific_surface_area_m2_g=round(surface_area, 2),
        active_site_density_mm2_g=round(active_site_density, 2),
        capacitance_f_g=round(capacitance, 2),
        ion_diffusivity_cm2_s=ion_diff,
        curie_temperature_k=round(curie_temperature, 2),
        saturation_magnetization_emu_g=round(sat_mag, 2),
    )
