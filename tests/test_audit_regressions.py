import json

import pytest

from thanimampro_api.database import load_literature_data, search_literature
from thanimampro_api.inverse import suggest_synthesis_conditions
from thanimampro_api.mapper import build_bandgap_map
from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import DesiredPropertyTargets, SynthesisInput
from thanimampro_api.structure import analyze_structure_file
from ugp.cli import main as ugp_main
from ugp.config import UGPConfig
from ugp.core.pipeline import run_pipeline
from ugp.models import ThermoDataset, UncertaintyConfig
import ugp.engines  # noqa: F401


def _base(**kw) -> SynthesisInput:
    args = dict(
        temperature_c=650.0, heating_rate_c_min=5.0, annealing_time_h=2.0, atmosphere="air",
        precursor_ratio=1.0, pH=7.0, solvent_type="water", concentration_m=0.5,
        pressure_bar=1.0, milling_time_h=2.0, calcination_time_h=2.0, method="sol-gel",
    )
    args.update(kw)
    return SynthesisInput(**args)


@pytest.mark.parametrize("bad", [{"pH": 15.0}, {"temperature_c": float("nan")}, {"method": "magic"},
                                 {"precursor_ratio": 0.0}, {"pressure_bar": -1.0}])
def test_synthesis_input_validation(bad):
    with pytest.raises(ValueError):
        _base(**bad)


def test_inverse_has_no_duplicate_candidates():
    desired = DesiredPropertyTargets(2.5, 50.0, 20.0)
    out = suggest_synthesis_conditions(_base(), desired, top_k=5)
    keys = {(r["temperature_c"], r["pH"], r["pred_band_gap_ev"], r["estimated_particle_size_nm"]) for r in out}
    assert len(keys) == 5
    with pytest.raises(ValueError):
        suggest_synthesis_conditions(_base(), desired, top_k=0)


def test_mapper_degenerate_range_and_validation():
    df = build_bandgap_map(_base(), None, 500, 500, 7.0, 7.0, points=10)
    assert len(df) == 1
    df = build_bandgap_map(_base(), None, 400, 800, 3, 9, points=5)
    assert len(df) == 25 and df.pivot(index="pH", columns="temperature_c", values="band_gap_ev").shape == (5, 5)
    with pytest.raises(ValueError):
        build_bandgap_map(_base(), None, 800, 400, 3, 9)


def test_cif_lattice_values_are_not_counted_as_peaks():
    cif = b"data_x\n_cell_length_a 3.7842(5)\n_cell_length_b 3.7842\n_cell_length_c 9.5146\n"
    f = analyze_structure_file("x.cif", cif)
    assert (f.lattice_a, f.lattice_c) == (3.7842, 9.5146)
    assert f.crystallite_size_nm == 60.0 and f.source == "CIF"


def test_xrd_without_cell_is_flagged_and_peaks_counted():
    f = analyze_structure_file("p.xy", b"# c\n27.44 1000\n36.08 612\n39.19 455\n")
    assert "default" in f.source
    assert f.crystallite_size_nm == pytest.approx(60.0 - 0.9 * 3)


def test_continuous_scan_peak_detection():
    rows = "\n".join(f"{20 + 0.05 * i:.2f} {100 if i in (50, 150) else 1}" for i in range(300))
    f = analyze_structure_file("scan.xy", rows.encode())
    assert f.n_peaks == 2


def test_literature_search_is_literal_and_handles_missing(tmp_path):
    csv = tmp_path / "lit.csv"
    csv.write_text("material_system,method,band_gap_ev\nTiO2 (anatase,sol-gel,3.2\nZnO,hydrothermal,\n")
    frame = load_literature_data(csv)
    assert len(search_literature(frame, material_system="TiO2 (anatase")) == 1  # no regex error
    assert len(search_literature(frame)) == 2  # NaN band gap kept when unfiltered
    assert load_literature_data(tmp_path / "none.csv").empty


def test_predict_extremes_do_not_overflow():
    predict_properties(_base(temperature_c=3000.0, pH=14.0))


def test_bootstrap_seeded_ci_and_status():
    cfg = UGPConfig(uncertainty_enabled=True)
    ds = ThermoDataset(analyses=[])
    res = run_pipeline(ds, "perplex", cfg, UncertaintyConfig(bootstrap_iterations=20, confidence=0.9, random_seed=1))
    assert res.summary["status"] == "not-implemented"
    assert "p_ci_gpa" in res.summary and res.summary["iterations"] == 20
    with pytest.raises(ValueError):
        run_pipeline(ds, None, cfg, UncertaintyConfig(bootstrap_iterations=0))


def test_pipeline_honours_default_engine():
    cfg = UGPConfig(default_engine="pywerami", uncertainty_enabled=False)
    assert run_pipeline(ThermoDataset(analyses=[]), None, cfg).results[0].method == "PyWerami"


def test_cli_errors_and_output(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        ugp_main(["run", str(tmp_path / "missing.json")])
    assert e.value.code == 1
    data = tmp_path / "d.json"
    data.write_text(json.dumps({"analyses": []}))
    with pytest.raises(SystemExit) as e:
        ugp_main(["run", str(data), "-e", "nope"])
    assert e.value.code == 1
    out = tmp_path / "sub" / "o.json"
    ugp_main(["run", str(data), "-e", "thermocalc", "-o", str(out)])
    assert json.loads(out.read_text())["summary"]["status"] == "not-implemented"


def test_williamson_hall_recovers_size_and_strain():
    import numpy as np
    lam, size, eps = 0.15406, 20.0, 0.002
    x = np.arange(20, 70, 0.02)
    y = np.full_like(x, 50.0)
    for c, i in [(25.28, 1000), (37.80, 250), (48.05, 350), (53.89, 200), (55.06, 190), (62.69, 150)]:
        th = np.radians(c / 2)
        beta = 0.9 * lam / (size * np.cos(th)) + 4 * eps * np.sin(th) / np.cos(th)
        y += i * np.exp(-0.5 * ((x - c) / (np.degrees(beta) / 2.355)) ** 2)
    f = analyze_structure_file("a.xy", "\n".join(f"{a:.2f} {b:.1f}" for a, b in zip(x, y)).encode())
    assert f.size_method == "Williamson-Hall" and f.phase == "anatase"
    assert f.crystallite_size_nm == pytest.approx(size, rel=0.05)
    assert f.microstrain_pct == pytest.approx(0.2, rel=0.1)


def test_property_map_and_sensitivity():
    from thanimampro_api.mapper import build_property_map
    from thanimampro_api.sensitivity import one_at_a_time
    df = build_property_map(_base(), None, 400, 800, 3, 9, points=4, prop="specific_surface_area_m2_g")
    assert list(df.columns) == ["temperature_c", "pH", "value"] and len(df) == 16
    with pytest.raises(ValueError):
        build_property_map(_base(), None, 400, 800, 3, 9, prop="nope")
    rows = one_at_a_time(_base(), None, "band_gap_ev")
    assert rows[0]["swing"] >= rows[-1]["swing"]
    assert next(r for r in rows if r["variable"] == "pressure_bar")["swing"] == 0.0  # band gap ignores pressure
    t = next(r for r in rows if r["variable"] == "temperature_c")
    assert t["delta_high"] < 0 < t["delta_low"]  # hotter -> smaller band gap in the surrogate
