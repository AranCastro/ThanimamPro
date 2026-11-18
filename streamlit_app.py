from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thanimampro_api.database import load_literature_data, search_literature
from thanimampro_api.inverse import suggest_synthesis_conditions
from thanimampro_api.mapper import build_bandgap_map
from thanimampro_api.predict import predict_properties
from thanimampro_api.schemas import (
    SYNTHESIS_METHODS,
    DesiredPropertyTargets,
    StructureFeatures,
    SynthesisInput,
)
from thanimampro_api.structure import analyze_structure_file, detect_peaks, read_pattern

SEED_DATA_PATH = ROOT / "data" / "literature_seed.csv"
LOGO_PATH = ROOT / "streamlit_app" / "assets" / "thanimampro_logo.svg"
SAMPLES_DIR = ROOT / "samples"
TEAL, INK = "#0F766E", "#1B2733"

CSS = """
<style>
.block-container {padding-top: 2.2rem; max-width: 1280px;}
h1, h2, h3 {letter-spacing: -0.01em;}
div[data-testid="stMetric"] {background:#F3F6F8; border:1px solid #E2E8EE; border-radius:12px; padding:14px 16px;}
div[data-testid="stMetricLabel"] p {font-size:0.8rem; color:#5B6B7B; text-transform:uppercase; letter-spacing:.04em;}
.tp-hero {border-left:4px solid #0F766E; padding:2px 0 2px 14px; margin-bottom:.8rem;}
.tp-hero h1 {margin:0; font-size:2rem;}
.tp-hero p {margin:.15rem 0 0; color:#5B6B7B;}
.tp-note {background:#FFF8E6; border:1px solid #F1DFA6; border-radius:10px; padding:10px 14px; font-size:.88rem; color:#6B5413;}
button[data-baseweb="tab"] {font-weight:600;}
</style>
"""

PROPERTY_LABELS = {
    "band_gap_ev": ("Band gap", "eV"),
    "absorption_edge_nm": ("Absorption edge", "nm"),
    "conductivity_s_cm": ("Conductivity", "S/cm"),
    "photoluminescence_intensity_au": ("PL intensity", "a.u."),
    "specific_surface_area_m2_g": ("Surface area", "m²/g"),
    "active_site_density_mm2_g": ("Active-site density", "a.u."),
    "capacitance_f_g": ("Capacitance", "F/g"),
    "ion_diffusivity_cm2_s": ("Ion diffusivity", "cm²/s"),
    "curie_temperature_k": ("Curie temperature", "K"),
    "saturation_magnetization_emu_g": ("Saturation magnetisation", "emu/g"),
}

DEFAULTS = {
    "temperature_c": 650.0, "heating_rate_c_min": 5.0, "annealing_time_h": 2.0,
    "atmosphere": "air", "precursor_ratio": 1.0, "pH": 7.0, "solvent_type": "water",
    "concentration_m": 0.5, "pressure_bar": 1.0, "milling_time_h": 2.0,
    "calcination_time_h": 2.0, "method": "sol-gel", "material_system": "TiO2",
    "structure": None, "pattern": None, "heatmap": None, "inverse": None,
}


def _init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def _synthesis_from_state() -> SynthesisInput:
    s = st.session_state
    return SynthesisInput(
        temperature_c=float(s.temperature_c), heating_rate_c_min=float(s.heating_rate_c_min),
        annealing_time_h=float(s.annealing_time_h), atmosphere=str(s.atmosphere),
        precursor_ratio=float(s.precursor_ratio), pH=float(s.pH), solvent_type=str(s.solvent_type),
        concentration_m=float(s.concentration_m), pressure_bar=float(s.pressure_bar),
        milling_time_h=float(s.milling_time_h), calcination_time_h=float(s.calcination_time_h),
        method=s.method, material_system=str(s.material_system),
    )


def _layout(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family="sans-serif", color=INK), title_font_size=16,
    )
    return fig


def _csv_button(frame: pd.DataFrame, label: str, name: str) -> None:
    st.download_button(label, frame.to_csv(index=False).encode(), file_name=name, mime="text/csv")


def _fmt(value: float) -> str:
    return f"{value:.3g}" if abs(value) < 1e-2 or abs(value) >= 1e4 else f"{value:,.2f}"


# ----------------------------------------------------------------------------- sidebar
def _sidebar() -> None:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=130)
        st.markdown("### Synthesis conditions")
        st.caption("Changes apply instantly to every tab.")
        st.selectbox("Method", SYNTHESIS_METHODS, key="method")
        st.text_input("Material system", key="material_system")
        with st.expander("Thermal", expanded=True):
            st.slider("Temperature (°C)", 100.0, 1500.0, step=10.0, key="temperature_c")
            st.number_input("Heating rate (°C/min)", 0.1, 100.0, key="heating_rate_c_min")
            st.number_input("Annealing time (h)", 0.1, 48.0, key="annealing_time_h")
            st.number_input("Calcination time (h)", 0.1, 48.0, key="calcination_time_h")
        with st.expander("Chemistry", expanded=True):
            st.slider("pH", 0.0, 14.0, step=0.1, key="pH")
            st.number_input("Concentration (M)", 0.001, 10.0, format="%.3f", key="concentration_m")
            st.number_input("Precursor ratio", 0.01, 10.0, key="precursor_ratio")
            st.text_input("Solvent", key="solvent_type")
            st.text_input("Atmosphere", key="atmosphere")
        with st.expander("Processing"):
            st.number_input("Pressure (bar)", 0.1, 500.0, key="pressure_bar")
            st.number_input("Milling time (h)", 0.0, 72.0, key="milling_time_h")
        if st.button("Reset conditions"):
            for k, v in DEFAULTS.items():
                if k not in ("structure", "pattern"):
                    st.session_state[k] = v
            st.rerun()


# ----------------------------------------------------------------------------- tabs
def _tab_predict(synthesis: SynthesisInput) -> None:
    pred = predict_properties(synthesis, st.session_state["structure"]).to_dict()
    st.markdown(
        '<div class="tp-note">Baseline surrogate with illustrative coefficients, <b>not fitted to '
        "experimental data</b>. Use it for trends and workflow, not for quantitative claims.</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    headline = ["band_gap_ev", "absorption_edge_nm", "specific_surface_area_m2_g", "conductivity_s_cm"]
    cols = st.columns(len(headline))
    for col, key in zip(cols, headline):
        label, unit = PROPERTY_LABELS[key]
        col.metric(f"{label} ({unit})", _fmt(pred[key]))

    frame = pd.DataFrame(
        [{"Property": PROPERTY_LABELS[k][0], "Unit": PROPERTY_LABELS[k][1], "Value": v} for k, v in pred.items()]
    )
    left, right = st.columns([2, 3])
    with left:
        shown = frame.assign(Value=frame["Value"].map(_fmt))
        st.dataframe(shown, hide_index=True)
        _csv_button(frame, "Download CSV", "thanimampro_predictions.csv")
    with right:
        fig = px.bar(frame, x="Property", y="Value", color_discrete_sequence=[TEAL], hover_data=["Unit"],
                     title="Predicted property profile (log scale)")
        fig.update_yaxes(type="log", exponentformat="e", title="Value (mixed units)")
        fig.update_layout(xaxis_tickangle=-40, xaxis_title=None)
        st.plotly_chart(_layout(fig, 400))


def _tab_structure() -> None:
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown("#### Load a pattern")
        uploaded = st.file_uploader("CIF / XRD / XY / TXT", type=["cif", "xrd", "xy", "txt"])
        samples = sorted(SAMPLES_DIR.glob("*")) if SAMPLES_DIR.exists() else []
        sample = st.selectbox("…or use a sample", ["—"] + [p.name for p in samples])
        name, data = None, None
        if uploaded is not None:
            name, data = uploaded.name, uploaded.getvalue()
        elif sample != "—":
            name, data = sample, (SAMPLES_DIR / sample).read_bytes()
        if st.button("Analyse structure", type="primary", disabled=data is None):
            try:
                st.session_state["structure"] = analyze_structure_file(name, data)
                rows = read_pattern(data.decode("utf-8", errors="ignore"))
                st.session_state["pattern"] = rows if len(rows) >= 3 else None
            except ValueError as exc:
                st.error(f"Could not analyse file: {exc}")
        if st.session_state["structure"] is not None and st.button("Clear structure"):
            st.session_state["structure"] = st.session_state["pattern"] = None
            st.rerun()
    with right:
        feats: StructureFeatures | None = st.session_state["structure"]
        if feats is None:
            st.info("No structure loaded. Predictions use default structural priors until you analyse a file.")
            return
        c = st.columns(4)
        c[0].metric("Phase", feats.phase)
        c[1].metric("Crystallite (nm)", f"{feats.crystallite_size_nm:.1f}")
        c[2].metric("Microstrain (%)", f"{feats.microstrain_pct:.3f}")
        c[3].metric("Defect index", f"{feats.defect_index:.2f}")
        c = st.columns(3)
        c[0].metric("a (Å)", f"{feats.lattice_a:.4f}")
        c[1].metric("b (Å)", f"{feats.lattice_b:.4f}")
        c[2].metric("c (Å)", f"{feats.lattice_c:.4f}")
        st.caption(
            f"Source: {feats.source} · size/strain method: **{feats.size_method}** · peaks: {feats.n_peaks}. "
            + ("Widths are not corrected for instrumental broadening (sizes are lower bounds)."
               if feats.size_method != "heuristic"
               else "Size and strain are peak-count heuristics; upload a continuous scan for Scherrer / Williamson–Hall analysis.")
        )
    pattern = st.session_state["pattern"]
    if pattern:
        rows = sorted(pattern)
        fig = go.Figure(go.Scatter(x=[r[0] for r in rows], y=[r[1] for r in rows],
                                   mode="lines" if len(rows) >= 50 else "markers",
                                   line=dict(color=TEAL), name="Pattern"))
        if len(rows) >= 50:
            peaks = detect_peaks(rows)
            fig.add_trace(go.Scatter(x=[p.two_theta for p in peaks], y=[p.intensity for p in peaks],
                                     mode="markers", marker=dict(color="#C2410C", size=9, symbol="triangle-down"),
                                     name="Detected peaks"))
        else:
            fig.update_traces(marker=dict(size=9))
        fig.update_layout(title="Diffraction pattern", xaxis_title="2θ (°)", yaxis_title="Intensity (a.u.)")
        st.plotly_chart(_layout(fig, 360))


def _tab_mapper(synthesis: SynthesisInput) -> None:
    c = st.columns([2, 2, 1, 1])
    temp_range = c[0].slider("Temperature range (°C)", 100, 1500, (450, 900), step=10)
    ph_range = c[1].slider("pH range", 0.0, 14.0, (2.0, 12.0), step=0.2)
    points = c[2].slider("Grid points", 5, 50, 25)
    c[3].write("")
    if c[3].button("Generate map", type="primary"):
        st.session_state["heatmap"] = build_bandgap_map(
            synthesis, st.session_state["structure"], float(temp_range[0]), float(temp_range[1]),
            float(ph_range[0]), float(ph_range[1]), points,
        )
    map_df = st.session_state["heatmap"]
    if map_df is None:
        st.info("Choose ranges and press **Generate map**.")
        return
    pivot = map_df.pivot(index="pH", columns="temperature_c", values="band_gap_ev")
    pivot.index, pivot.columns = pivot.index.round(2), pivot.columns.round(1)
    fig = px.imshow(pivot, origin="lower", aspect="auto", color_continuous_scale="Tealrose",
                    labels={"x": "Temperature (°C)", "y": "pH", "color": "Band gap (eV)"},
                    title="Predicted band gap: temperature × pH")
    st.plotly_chart(_layout(fig, 460))
    _csv_button(map_df, "Download grid CSV", "thanimampro_bandgap_map.csv")


def _tab_inverse(synthesis: SynthesisInput) -> None:
    c = st.columns(4)
    target = c[0].number_input("Target band gap (eV)", 0.5, 6.0, 2.5, step=0.05)
    min_sa = c[1].number_input("Min surface area (m²/g)", 1.0, 500.0, 50.0, step=1.0)
    max_ps = c[2].number_input("Max particle size (nm)", 2.0, 500.0, 20.0, step=1.0)
    top_k = c[3].number_input("Suggestions", 1, 20, 5)
    if st.button("Suggest conditions", type="primary"):
        st.session_state["inverse"] = pd.DataFrame(suggest_synthesis_conditions(
            synthesis, DesiredPropertyTargets(float(target), float(min_sa), float(max_ps)),
            st.session_state["structure"], top_k=int(top_k)))
    result = st.session_state["inverse"]
    if result is None:
        st.info("Set targets and press **Suggest conditions**.")
        return
    st.caption("Grid search over temperature, pH and calcination time. Lower score = closer to the targets.")
    st.dataframe(result, hide_index=True)
    _csv_button(result, "Download CSV", "thanimampro_inverse_design.csv")


def _tab_literature() -> None:
    frame = load_literature_data(SEED_DATA_PATH)
    if not SEED_DATA_PATH.exists():
        st.info(f"No dataset found at `{SEED_DATA_PATH.relative_to(ROOT)}`. Add a CSV with columns "
                "material_system, method, temperature_c, pH, band_gap_ev, surface_area_m2_g, doi.")
    c = st.columns(4)
    mat = c[0].text_input("Material system")
    meth = c[1].text_input("Method")
    min_bg = c[2].number_input("Min band gap (eV)", 0.0, 6.0, 0.0, step=0.1)
    max_bg = c[3].number_input("Max band gap (eV)", 0.0, 6.0, 6.0, step=0.1)
    if min_bg > max_bg:
        st.warning("Min band gap exceeds max band gap; no records can match.")
    filtered = search_literature(frame, mat, meth, min_bg if min_bg > 0 else None, max_bg if max_bg < 6 else None)
    st.caption(f"{len(filtered)} of {len(frame)} records")
    st.dataframe(filtered, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="ThanimamPro", page_icon="🧪", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    _init_state()
    _sidebar()
    st.markdown(
        '<div class="tp-hero"><h1>ThanimamPro</h1><p>Synthesis → structure → property integration for materials research</p></div>',
        unsafe_allow_html=True,
    )
    try:
        synthesis = _synthesis_from_state()
    except ValueError as exc:
        st.error(f"Invalid synthesis conditions: {exc}")
        return
    tabs = st.tabs(["Properties", "Structure", "Relationship map", "Inverse design", "Literature"])
    with tabs[0]:
        _tab_predict(synthesis)
    with tabs[1]:
        _tab_structure()
    with tabs[2]:
        _tab_mapper(synthesis)
    with tabs[3]:
        _tab_inverse(synthesis)
    with tabs[4]:
        _tab_literature()


if __name__ == "__main__":
    main()
