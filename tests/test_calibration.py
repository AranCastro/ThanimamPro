"""Calibration, scope and XRD-accuracy tests added with the audit fixes."""
import importlib.util
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from thanimampro_api import predict
from thanimampro_api.database import load_literature_data
from thanimampro_api.inverse import reachable_band_gap_range, suggest_synthesis_conditions
from thanimampro_api.mapper import build_property_map
from thanimampro_api.predict import predict_properties, scope_warnings
from thanimampro_api.schemas import DesiredPropertyTargets, StructureFeatures, SynthesisInput
from thanimampro_api.structure import analyze_structure_file

ROOT = Path(__file__).resolve().parent.parent
K_LAMBDA_NM = 0.9 * 0.1540562
ANATASE = [(25.28, 1000), (37.80, 200), (48.05, 300), (53.89, 180), (55.06, 170), (62.69, 130)]
RUTILE = [(27.45, 1000), (36.09, 500), (41.23, 250), (54.32, 600), (56.64, 200), (69.01, 200)]


def _load(script: str):
    spec = importlib.util.spec_from_file_location(script, ROOT / "scripts" / f"{script}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base(**kw) -> SynthesisInput:
    args = dict(
        temperature_c=600.0, heating_rate_c_min=5.0, annealing_time_h=2.0, atmosphere="air",
        precursor_ratio=1.0, pH=7.0, solvent_type="water", concentration_m=0.5,
        pressure_bar=1.0, milling_time_h=0.0, calcination_time_h=2.0, method="sol-gel",
    )
    args.update(kw)
    return SynthesisInput(**args)


def _scan(peaks, size_nm, strain=0.0, step=0.02, noise=0.0, ka2=False, instrument=0.0, lorentz=False) -> bytes:
    """Synthetic Cu K-alpha scan, 10-80 deg, with Scherrer + strain broadening of known magnitude."""
    x = np.arange(10, 80, step)
    y = np.full_like(x, 20.0)
    for centre, height in peaks:
        theta = np.radians(centre / 2)
        fwhm = np.hypot(np.degrees(K_LAMBDA_NM / (size_nm * np.cos(theta)) + 4 * strain * np.tan(theta)), instrument)
        lines = [(centre, height)]
        if ka2:
            lines.append((2 * np.degrees(np.arcsin(np.sin(theta) * 1.544390 / 1.540562)), height / 2))
        for c, h in lines:
            y = y + (h / (1 + 4 * ((x - c) / fwhm) ** 2) if lorentz else h * np.exp(-4 * np.log(2) * ((x - c) / fwhm) ** 2))
    if noise:
        y = y + np.random.default_rng(0).normal(0, noise, len(y))
    return "\n".join(f"{a:.3f} {max(b, 0):.2f}" for a, b in zip(x, y)).encode()


# ---------------------------------------------------------------- calibration
def test_predict_constants_match_refit_of_shipped_data():
    fits = _load("fit_surrogate").fit_all(load_literature_data(ROOT / "data" / "literature_seed.csv"))
    assert fits["band_gap_ev"]["coef"] == pytest.approx(
        [predict.BG_INTERCEPT, predict.BG_PER_DEGC, predict.BG_DOPED], rel=1e-4)
    assert fits["surface_area_m2_g"]["coef"] == pytest.approx(
        [predict.SA_LOG_INTERCEPT, predict.SA_LOG_PER_DEGC], rel=1e-4)
    assert fits["crystallite_size_nm"]["coef"] == pytest.approx(
        [predict.CS_LOG_INTERCEPT, predict.CS_LOG_PER_DEGC], rel=1e-4)


def test_band_gap_beats_constant_on_held_out_papers():
    res = _load("fit_surrogate").fit_all(load_literature_data(ROOT / "data" / "literature_seed.csv"))["band_gap_ev"]
    assert res["model"]["mae"] < res["constant"]["mae"]
    assert res["model"]["r2"] > 0.2


def test_band_gap_responds_to_temperature_and_doping_only():
    base = predict_properties(_base()).band_gap_ev
    assert base == pytest.approx(predict.BG_INTERCEPT, abs=1e-4)
    assert predict_properties(_base(temperature_c=900.0)).band_gap_ev < base
    assert predict_properties(_base(material_system="TiO2:Fe")).band_gap_ev == pytest.approx(base + predict.BG_DOPED, abs=1e-4)
    for change in ({"pH": 2.0}, {"pressure_bar": 50.0}, {"method": "combustion"}):
        assert predict_properties(_base(**change)).band_gap_ev == base


def test_measured_crystallite_size_sets_geometric_surface_area():
    feats = StructureFeatures(phase="anatase", crystallite_size_nm=20.0)
    assert predict_properties(_base(), feats).specific_surface_area_m2_g == pytest.approx(6000 / (3.9 * 20.0), abs=0.01)


def test_scope_warnings_and_magnetic_outputs():
    assert scope_warnings(_base()) == []
    assert any("TiO2" in w for w in scope_warnings(_base(material_system="ZnO")))
    assert any("extrapolation" in w for w in scope_warnings(_base(temperature_c=1400.0)))
    assert predict_properties(_base()).curie_temperature_k is None
    assert predict_properties(_base(material_system="TiO2:Fe")).curie_temperature_k is not None
    with pytest.raises(ValueError):
        build_property_map(_base(), None, 400, 800, 3, 9, prop="curie_temperature_k")


def test_unreachable_target_is_flagged():
    lo, hi = reachable_band_gap_range(_base())
    assert 2.7 < lo < hi < 3.4
    out = suggest_synthesis_conditions(_base(), DesiredPropertyTargets(1.5, 50.0, 20.0), top_k=3)
    assert not any(r["target_reachable"] or r["meets_all_targets"] for r in out)
    assert min(r["band_gap_error_ev"] for r in out) >= lo - 1.5 - 1e-3


@pytest.mark.parametrize("bad", [(float("nan"), 50.0, 20.0), (2.5, -1.0, 20.0), (2.5, 50.0, 0.0), (0.0, 50.0, 20.0)])
def test_targets_are_validated(bad):
    with pytest.raises(ValueError):
        DesiredPropertyTargets(*bad)


# ---------------------------------------------------------------- XRD accuracy (audit Table 4)
@pytest.mark.parametrize("size", [5.0, 10.0, 20.0, 50.0, 100.0])
def test_scherrer_recovers_known_size(size):
    f = analyze_structure_file("s.xy", _scan(ANATASE, size))
    assert f.phase == "anatase" and f.size_method == "Scherrer"
    assert f.crystallite_size_nm == pytest.approx(size, rel=0.05)
    assert f.microstrain_pct is None  # no strain present: none reported


def test_lorentzian_profile_and_coarser_step():
    assert analyze_structure_file("s.xy", _scan(ANATASE, 20.0, lorentz=True)).crystallite_size_nm == pytest.approx(20.0, rel=0.05)
    assert analyze_structure_file("s.xy", _scan(ANATASE, 20.0, step=0.05)).crystallite_size_nm == pytest.approx(20.0, rel=0.05)


def test_williamson_hall_recovers_size_and_strain():
    f = analyze_structure_file("s.xy", _scan(ANATASE, 20.0, strain=0.003))
    assert f.size_method == "Williamson-Hall"
    assert f.crystallite_size_nm == pytest.approx(20.0, rel=0.05)
    assert f.microstrain_pct == pytest.approx(0.30, rel=0.05)


def test_noise_does_not_create_peaks_or_strain():
    f = analyze_structure_file("s.xy", _scan(ANATASE, 20.0, noise=20.0))  # sigma = 2 % of the maximum
    assert f.n_peaks == 6 and f.microstrain_pct is None
    assert f.crystallite_size_nm == pytest.approx(20.0, rel=0.10)


def test_ka2_stripping_and_instrument_correction():
    assert analyze_structure_file("s.xy", _scan(ANATASE, 50.0, ka2=True), strip_ka2=True).crystallite_size_nm == pytest.approx(50.0, rel=0.05)
    raw = analyze_structure_file("s.xy", _scan(ANATASE, 50.0, instrument=0.1))
    fixed = analyze_structure_file("s.xy", _scan(ANATASE, 50.0, instrument=0.1), instrumental_fwhm_deg=0.1)
    assert raw.crystallite_size_nm < 45.0 and "underestimated" in raw.notes
    assert fixed.crystallite_size_nm == pytest.approx(50.0, rel=0.05)
    with pytest.raises(ValueError):
        analyze_structure_file("s.xy", b"", instrumental_fwhm_deg=-0.1)


def test_mixture_and_unknown_phase():
    mix = analyze_structure_file("s.xy", _scan(ANATASE + [(t, 0.9 * h) for t, h in RUTILE], 25.0))
    assert set(mix.phase.split(" + ")) == {"anatase", "rutile"}
    assert mix.crystallite_size_nm == pytest.approx(25.0, rel=0.05)
    zno = [(31.77, 570), (34.42, 440), (36.25, 1000), (47.54, 230), (56.60, 320), (62.86, 290), (67.96, 230)]
    f = analyze_structure_file("zno.xy", _scan(zno, 30.0))
    assert f.phase == "unknown" and f.lattice_a is None
    assert f.crystallite_size_nm == pytest.approx(30.0, rel=0.05)


def test_flat_and_empty_inputs_report_nothing():
    flat = "\n".join(f"{10 + i * 0.02:.2f} 50" for i in range(500)).encode()
    for name, data in (("flat.xy", flat), ("empty.cif", b""), ("bad.cif", b"_cell_length_a -3.2\n_cell_length_c 1e400\n")):
        f = analyze_structure_file(name, data)
        assert f.crystallite_size_nm is None and f.lattice_a is None and f.lattice_c is None and f.n_peaks == 0


def test_user_defect_index_only_affects_illustrative_outputs():
    plain = predict_properties(_base())
    with_defects = predict_properties(_base(), StructureFeatures(phase="anatase", defect_index=0.9))
    assert with_defects.band_gap_ev == plain.band_gap_ev
    assert with_defects.conductivity_s_cm != plain.conductivity_s_cm
    assert replace(StructureFeatures(phase="x"), defect_index=None).defect_index is None
