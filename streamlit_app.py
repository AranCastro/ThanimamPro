from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thanimampro_api.database import load_literature_data, search_literature
from thanimampro_api.inverse import suggest_synthesis_conditions
from thanimampro_api.mapper import build_bandgap_map
from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import DesiredPropertyTargets, StructureFeatures, SynthesisInput
from thanimampro_api.structure import analyze_structure_file

SEED_DATA_PATH = ROOT / "data" / "literature_seed.csv"
LOGO_PATH = ROOT / "streamlit_app" / "assets" / "thanimampro_logo.svg"


def _init_state() -> None:
    defaults = {
        "temperature_c": 650.0,
        "heating_rate_c_min": 5.0,
        "annealing_time_h": 2.0,
        "atmosphere": "air",
        "precursor_ratio": 1.0,
        "pH": 7.0,
        "solvent_type": "water",
        "concentration_m": 0.5,
        "pressure_bar": 1.0,
        "milling_time_h": 2.0,
        "calcination_time_h": 2.0,
        "method": "sol-gel",
        "material_system": "TiO2",
        "structure": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _synthesis_from_state() -> SynthesisInput:
    return SynthesisInput(
        temperature_c=float(st.session_state.temperature_c),
        heating_rate_c_min=float(st.session_state.heating_rate_c_min),
        annealing_time_h=float(st.session_state.annealing_time_h),
        atmosphere=str(st.session_state.atmosphere),
        precursor_ratio=float(st.session_state.precursor_ratio),
        pH=float(st.session_state.pH),
        solvent_type=str(st.session_state.solvent_type),
        concentration_m=float(st.session_state.concentration_m),
        pressure_bar=float(st.session_state.pressure_bar),
        milling_time_h=float(st.session_state.milling_time_h),
        calcination_time_h=float(st.session_state.calcination_time_h),
        method=st.session_state.method,
        material_system=str(st.session_state.material_system),
    )


def _render_structure_metrics(features: StructureFeatures) -> None:
    left, right = st.columns(2)
    with left:
        st.metric("Phase", features.phase)
        st.metric("Lattice a", f"{features.lattice_a:.4f} A")
        st.metric("Lattice b", f"{features.lattice_b:.4f} A")
        st.metric("Lattice c", f"{features.lattice_c:.4f} A")
    with right:
        st.metric("Crystallite size", f"{features.crystallite_size_nm:.2f} nm")
        st.metric("Microstrain", f"{features.microstrain_pct:.3f} %")
        st.metric("Defect index", f"{features.defect_index:.3f}")
        st.caption(f"Source: {features.source}")


def main() -> None:
    st.set_page_config(page_title="ThanimamPro", layout="wide")
    _init_state()

    logo_col, text_col = st.columns([1, 5])
    with logo_col:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=150)
    with text_col:
        st.title("ThanimamPro")
        st.caption("Synthesis-Structure-Property Integration Platform")

    tabs = st.tabs(
        [
            "1) Synthesis Input",
            "2) Structure Analysis",
            "3) Property Prediction",
            "4) Relationship Mapper",
            "5) Inverse Design",
            "6) Literature Database",
        ]
    )

    with tabs[0]:
        st.subheader("Experimental Condition Entry")
        with st.form("synthesis_input"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.number_input("Temperature (C)", 100.0, 1500.0, key="temperature_c")
                st.number_input("Heating rate (C/min)", 0.1, 100.0, key="heating_rate_c_min")
                st.number_input("Annealing time (h)", 0.1, 48.0, key="annealing_time_h")
                st.text_input("Atmosphere", key="atmosphere")
            with col2:
                st.number_input("Precursor ratio", 0.01, 10.0, key="precursor_ratio")
                st.number_input("pH", 0.0, 14.0, key="pH")
                st.text_input("Solvent type", key="solvent_type")
                st.number_input("Concentration (M)", 0.001, 10.0, key="concentration_m")
            with col3:
                st.number_input("Pressure (bar)", 0.1, 500.0, key="pressure_bar")
                st.number_input("Milling time (h)", 0.0, 72.0, key="milling_time_h")
                st.number_input("Calcination time (h)", 0.1, 48.0, key="calcination_time_h")
                st.selectbox(
                    "Method",
                    options=[
                        "sol-gel",
                        "hydrothermal",
                        "co-precipitation",
                        "solid-state",
                        "combustion",
                        "other",
                    ],
                    key="method",
                )
            st.text_input("Material system", key="material_system")
            submitted = st.form_submit_button("Save Conditions")
        if submitted:
            st.success("Synthesis conditions saved.")

    with tabs[1]:
        st.subheader("CIF/XRD Upload")
        uploaded = st.file_uploader("Upload CIF/XRD file", type=["cif", "xrd", "xy", "txt"])
        if uploaded is not None and st.button("Analyze Structure", type="primary"):
            features = analyze_structure_file(uploaded.name, uploaded.getvalue())
            st.session_state["structure"] = features
        if st.session_state["structure"] is not None:
            _render_structure_metrics(st.session_state["structure"])
        else:
            st.info("No structure file analyzed yet. Prediction still works with default structural priors.")

    with tabs[2]:
        st.subheader("Predicted Functional Properties")
        synthesis = _synthesis_from_state()
        prediction = predict_properties(synthesis, st.session_state["structure"])
        pred_df = pd.DataFrame(
            [{"property": key, "value": value} for key, value in prediction.to_dict().items()]
        )
        c1, c2 = st.columns([2, 3])
        with c1:
            st.dataframe(pred_df, use_container_width=True, hide_index=True)
        with c2:
            fig = px.bar(pred_df, x="property", y="value", title="Predicted Property Profile")
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.subheader("Band Gap Sensitivity: Temperature vs pH")
        temp_range = st.slider("Temperature range (C)", 200, 1200, (450, 900), step=10)
        ph_range = st.slider("pH range", 0.0, 14.0, (2.0, 12.0), step=0.2)
        points = st.slider("Grid density", 10, 50, 25)
        if st.button("Generate Heatmap"):
            synthesis = _synthesis_from_state()
            map_df = build_bandgap_map(
                baseline=synthesis,
                structure=st.session_state["structure"],
                temp_min=float(temp_range[0]),
                temp_max=float(temp_range[1]),
                ph_min=float(ph_range[0]),
                ph_max=float(ph_range[1]),
                points=points,
            )
            pivot = map_df.pivot(index="pH", columns="temperature_c", values="band_gap_ev")
            fig = px.imshow(
                pivot,
                labels={"x": "Temperature (C)", "y": "pH", "color": "Band gap (eV)"},
                aspect="auto",
                title="Iso-performance map",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(map_df.head(20), use_container_width=True, hide_index=True)

    with tabs[4]:
        st.subheader("Target-Driven Inverse Design")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            target_bg = st.number_input("Target band gap (eV)", 0.5, 6.0, 2.5, step=0.05)
        with col_b:
            min_sa = st.number_input("Min surface area (m2/g)", 1.0, 500.0, 50.0, step=1.0)
        with col_c:
            max_ps = st.number_input("Max particle size (nm)", 2.0, 500.0, 20.0, step=1.0)
        if st.button("Suggest Synthesis Conditions", type="primary"):
            targets = DesiredPropertyTargets(
                target_band_gap_ev=float(target_bg),
                min_surface_area_m2_g=float(min_sa),
                max_particle_size_nm=float(max_ps),
            )
            baseline = _synthesis_from_state()
            suggestions = suggest_synthesis_conditions(
                baseline=baseline,
                desired=targets,
                structure=st.session_state["structure"],
                top_k=5,
            )
            st.dataframe(pd.DataFrame(suggestions), use_container_width=True, hide_index=True)

    with tabs[5]:
        st.subheader("Literature Records (Seed Dataset)")
        frame = load_literature_data(SEED_DATA_PATH)
        material_filter, method_filter = st.columns(2)
        with material_filter:
            mat = st.text_input("Filter by material system")
        with method_filter:
            meth = st.text_input("Filter by method")
        bg_min, bg_max = st.columns(2)
        with bg_min:
            min_bg = st.number_input("Min band gap filter", 0.0, 6.0, 0.0, step=0.1)
        with bg_max:
            max_bg = st.number_input("Max band gap filter", 0.0, 6.0, 6.0, step=0.1)

        filtered = search_literature(
            frame=frame,
            material_system=mat,
            method=meth,
            min_band_gap=float(min_bg),
            max_band_gap=float(max_bg),
        )
        st.dataframe(filtered, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
