from thanimampro_api.inverse import suggest_synthesis_conditions
from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import DesiredPropertyTargets, SynthesisInput


def _baseline() -> SynthesisInput:
    return SynthesisInput(
        temperature_c=650.0,
        heating_rate_c_min=5.0,
        annealing_time_h=2.0,
        atmosphere="air",
        precursor_ratio=1.0,
        pH=7.0,
        solvent_type="water",
        concentration_m=0.5,
        pressure_bar=1.0,
        milling_time_h=2.0,
        calcination_time_h=2.0,
        method="sol-gel",
    )


def test_predict_properties_ranges() -> None:
    pred = predict_properties(_baseline()).to_dict()
    assert 1.0 <= pred["band_gap_ev"] <= 5.0
    assert pred["specific_surface_area_m2_g"] > 0.0
    assert pred["capacitance_f_g"] > 0.0


def test_inverse_returns_ranked_candidates() -> None:
    desired = DesiredPropertyTargets(
        target_band_gap_ev=2.5,
        min_surface_area_m2_g=50.0,
        max_particle_size_nm=20.0,
    )
    suggestions = suggest_synthesis_conditions(_baseline(), desired, top_k=3)
    assert len(suggestions) == 3
    assert suggestions[0]["score"] <= suggestions[1]["score"]
