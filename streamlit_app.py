from __future__ import annotations

import html
import json
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thanimampro_api.database import load_literature_data, search_literature
from thanimampro_api.inverse import reachable_band_gap_range, suggest_synthesis_conditions
from thanimampro_api.mapper import build_property_map
from thanimampro_api.sensitivity import one_at_a_time
from thanimampro_api.predict import predict_properties, scope_warnings
from thanimampro_api.schemas import (
    CALIBRATED_PROPERTIES,
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
.tp-steps {display:flex; gap:10px; margin:.2rem 0 1rem; flex-wrap:wrap;}
.tp-step {flex:1; min-width:180px; border:1px solid #E2E8EE; border-radius:12px; padding:10px 14px; background:#fff;}
.tp-step b {display:block; font-size:.78rem; text-transform:uppercase; letter-spacing:.05em; color:#5B6B7B;}
.tp-step span {font-weight:600;}
.tp-step.done {border-color:#0F766E; background:#F0FAF8;}
.tp-step.done span {color:#0F766E;}
.tp-chip {display:inline-block; padding:3px 10px; border-radius:999px; font-size:.8rem; font-weight:600; background:#E6F4F1; color:#0F766E;}
.tp-chip.warn {background:#FFF1DB; color:#9A5B00;}
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

# Starting points inside the calibrated domain (TiO2 and doped TiO2). They are typical of the
# literature table, not recipes taken from a specific paper.
PRESETS = {
    "TiO2 · sol-gel, 450 °C": dict(method="sol-gel", material_system="TiO2", temperature_c=450.0, pH=7.0, calcination_time_h=2.0, pressure_bar=1.0, milling_time_h=0.0),
    "TiO2 · co-precipitation, 600 °C": dict(method="co-precipitation", material_system="TiO2", temperature_c=600.0, pH=10.0, calcination_time_h=4.0, pressure_bar=1.0, milling_time_h=0.0),
    "TiO2 · combustion, 500 °C": dict(method="combustion", material_system="TiO2", temperature_c=500.0, pH=7.0, calcination_time_h=1.0, pressure_bar=1.0, milling_time_h=0.0),
    "TiO2:Fe · sol-gel, 450 °C": dict(method="sol-gel", material_system="TiO2:Fe", temperature_c=450.0, pH=7.0, calcination_time_h=4.0, pressure_bar=1.0, milling_time_h=0.0),
}
CONDITION_KEYS = [
    "temperature_c", "heating_rate_c_min", "annealing_time_h", "atmosphere", "precursor_ratio", "pH",
    "solvent_type", "concentration_m", "pressure_bar", "milling_time_h", "calcination_time_h", "method", "material_system",
]

DEFAULTS = {
    "temperature_c": 650.0, "heating_rate_c_min": 5.0, "annealing_time_h": 2.0,
    "atmosphere": "air", "precursor_ratio": 1.0, "pH": 7.0, "solvent_type": "water",
    "concentration_m": 0.5, "pressure_bar": 1.0, "milling_time_h": 2.0,
    "calcination_time_h": 2.0, "method": "sol-gel", "material_system": "TiO2",
    "use_defect_index": False, "defect_index": 0.25, "instrumental_fwhm": 0.0, "strip_ka2": False,
    "structure": None, "pattern": None, "heatmap": None, "inverse": None, "scenarios": [], "preset": "—",
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


def _structure_for_prediction() -> StructureFeatures | None:
    """Analysed structure, with the user's defect-index estimate attached when one is supplied."""
    feats = st.session_state["structure"]
    if not st.session_state["use_defect_index"]:
        return feats
    value = float(st.session_state["defect_index"])
    if feats is None:
        return StructureFeatures(phase="not analysed", defect_index=value, source="user estimate")
    return replace(feats, defect_index=value)


def _available(pred: dict) -> list:
    """Property keys that are reported for the current material (magnetic outputs may be absent)."""
    return [k for k in PROPERTY_LABELS if pred.get(k) is not None]


def _layout(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family="sans-serif", color=INK), title_font_size=16,
    )
    return fig


def _csv_button(frame: pd.DataFrame, label: str, name: str) -> None:
    st.download_button(label, frame.to_csv(index=False).encode(), file_name=name, mime="text/csv")


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3g}" if abs(value) < 1e-2 or abs(value) >= 1e4 else f"{value:,.2f}"


# ----------------------------------------------------------------------------- helpers
def _apply(values: dict) -> None:
    """Callback: write values into session state before widgets are rebuilt."""
    for key, value in values.items():
        st.session_state[key] = value


def _conditions() -> dict:
    return {k: st.session_state[k] for k in CONDITION_KEYS}


def _scenario_frame() -> pd.DataFrame:
    rows = []
    for sc in st.session_state["scenarios"]:
        rows.append({"Scenario": sc["name"], **{k: sc["conditions"][k] for k in ("method", "temperature_c", "pH", "pressure_bar")},
                     **{PROPERTY_LABELS[k][0]: v for k, v in sc["properties"].items()}})
    return pd.DataFrame(rows)


CALIBRATION_NOTE = (
    "Band gap and surface area are fitted to the literature table (137 TiO2 rows, 30 papers). "
    "Leave-one-paper-out error: band gap MAE 0.145 eV (R² 0.35); surface area from temperature MAE 46.5 m²/g "
    "(R² −0.13, no better than a constant by R²). All other properties are illustrative and unvalidated."
)


def _cell(value: object) -> str:
    """Text safe for a Markdown table cell."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _report_markdown(synthesis: SynthesisInput, pred: dict) -> str:
    feats = st.session_state["structure"]
    lines = [
        "# ThanimamPro report", f"Generated: {datetime.now():%Y-%m-%d %H:%M}", "",
        "## Synthesis conditions", "| Parameter | Value |", "|---|---|",
        *[f"| {k} | {_cell(v)} |" for k, v in synthesis.to_dict().items()], "", "## Structure",
    ]
    if feats:
        lines += ["| Descriptor | Value |", "|---|---|",
                  *[f"| {k} | {_cell('not available' if v is None else v)} |" for k, v in feats.to_dict().items()]]
    else:
        lines.append("No structure file analysed.")
    lines += ["", "## Predicted properties", "| Property | Value | Unit | Status |", "|---|---|---|---|",
              *[f"| {PROPERTY_LABELS[k][0]} | {_fmt(v)} | {PROPERTY_LABELS[k][1]} | "
                f"{'calibrated' if k in CALIBRATED_PROPERTIES else 'illustrative'} |" for k, v in pred.items() if v is not None], "",
              "> " + CALIBRATION_NOTE, *[f"> Warning: {w}" for w in scope_warnings(synthesis)]]
    return "\n".join(lines)


# ----------------------------------------------------------------------------- sidebar
def _sidebar() -> None:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=130)
        st.markdown("### Synthesis conditions")
        preset = st.selectbox("Quick start", ["—"] + list(PRESETS), key="preset",
                              help="Illustrative starting points, not literature-verified recipes.")
        if preset != "—":
            st.button("Load preset", on_click=_apply, args=(PRESETS[preset],), type="primary")
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
        with st.expander("Defect index (optional)"):
            st.checkbox("Supply my own estimate", key="use_defect_index",
                        help="A diffraction pattern does not determine a defect index. Without an estimate, "
                             "the illustrative properties use 0.25. Calibrated properties do not use it.")
            st.slider("Defect index (0 = none, 1 = high)", 0.0, 1.0, step=0.05, key="defect_index",
                      disabled=not st.session_state["use_defect_index"])
        st.button("Reset conditions", on_click=_apply,
                  args=({k: v for k, v in DEFAULTS.items() if k in CONDITION_KEYS}
                        | {"preset": "—", "use_defect_index": False, "defect_index": 0.25},))


def _stepper(n_scenarios: int) -> None:
    feats = st.session_state["structure"]
    steps = [
        ("1 · Conditions", f"{st.session_state['material_system']} · {st.session_state['method']}", True),
        ("2 · Structure", f"{feats.phase} · size: {feats.size_method}" if feats else "optional · upload in Structure tab", feats is not None),
        ("3 · Results", "live — updates as you edit", True),
        ("4 · Scenarios", f"{n_scenarios} saved" if n_scenarios else "save one to compare", n_scenarios > 0),
    ]
    # User-typed text (material system) is escaped before it enters the markup.
    markup = "".join(f'<div class="tp-step {"done" if ok else ""}"><b>{html.escape(t)}</b><span>{html.escape(v)}</span></div>'
                     for t, v, ok in steps)
    st.markdown(f'<div class="tp-steps">{markup}</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------- results
def _absorption_figure(edge_nm: float, gap: float) -> go.Figure:
    fig = go.Figure()
    for x0, x1, name, color in [(200, 380, "UV", "#DCD7F5"), (380, 750, "Visible", "#FDE8B0"), (750, 1100, "Near-IR", "#F4C9C0")]:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=color, opacity=0.55, line_width=0,
                      annotation_text=name, annotation_position="top left")
    fig.add_trace(go.Scatter(x=[200, min(edge_nm, 1100)], y=[0, 0], mode="lines",
                             line=dict(color=TEAL, width=14), name="Absorbed", hoverinfo="skip"))
    fig.add_vline(x=min(edge_nm, 1100), line_dash="dot", line_color=INK,
                  annotation_text=f"edge {edge_nm:.0f} nm ({gap:.2f} eV)", annotation_position="bottom right")
    fig.update_yaxes(visible=False, range=[-1, 1])
    fig.update_xaxes(title="Wavelength (nm)", range=[200, 1100])
    fig.update_layout(showlegend=False, title="Light absorption window")
    return _layout(fig, 220)


def _tab_results(synthesis: SynthesisInput) -> None:
    structure = _structure_for_prediction()
    pred = predict_properties(synthesis, structure).to_dict()
    st.markdown(f'<div class="tp-note">{html.escape(CALIBRATION_NOTE)}</div>', unsafe_allow_html=True)
    st.write("")
    ref = st.session_state["scenarios"][-1]["properties"] if st.session_state["scenarios"] else None
    measured_size = structure is not None and structure.crystallite_size_nm is not None
    basis = {
        "band_gap_ev": "calibrated · held-out MAE 0.145 eV",
        "absorption_edge_nm": "1239.84 / band gap",
        "specific_surface_area_m2_g": ("geometric, from measured crystallite size · MAE 33.7 m²/g (upper bound)"
                                       if measured_size else "calibrated on temperature · held-out MAE 46.5 m²/g"),
    }
    for col, key in zip(st.columns(len(CALIBRATED_PROPERTIES)), CALIBRATED_PROPERTIES):
        label, unit = PROPERTY_LABELS[key]
        delta = None if ref is None or ref.get(key) is None else f"{pred[key] - ref[key]:+.3g} vs last saved"
        col.metric(f"{label} ({unit})", _fmt(pred[key]), delta=delta, delta_color="off")
        col.caption(basis[key])

    gap = pred["band_gap_ev"]
    edge = pred["absorption_edge_nm"]
    region = "UV-only" if edge < 380 else ("visible-light active" if edge <= 750 else "extends into near-IR")
    st.markdown(f'<span class="tp-chip">{region}</span> &nbsp; absorption edge {edge:.0f} nm', unsafe_allow_html=True)
    st.plotly_chart(_absorption_figure(edge, gap), key="absorption")

    st.markdown("#### Sensitivity")
    c1, c2 = st.columns([1, 3])
    prop = c1.selectbox("Property", _available(pred), format_func=lambda k: PROPERTY_LABELS[k][0], key="sens_prop")
    c1.caption("One variable at a time: temperature ±50 °C, pH ±1, pressure ±10 %.")
    sens = pd.DataFrame(one_at_a_time(synthesis, structure, prop))
    if sens["swing"].max() == 0:
        c2.info(f"{PROPERTY_LABELS[prop][0]} does not depend on temperature, pH or pressure in the current surrogate.")
    else:
        names = {"temperature_c": "Temperature ±50 °C", "pH": "pH ±1", "pressure_bar": "Pressure ±10 %"}
        fig = go.Figure()
        fig.add_bar(y=sens["variable"].map(names), x=sens["delta_low"], orientation="h", name="decrease", marker_color="#64748B")
        fig.add_bar(y=sens["variable"].map(names), x=sens["delta_high"], orientation="h", name="increase", marker_color=TEAL)
        fig.update_layout(barmode="relative", title=f"Change in {PROPERTY_LABELS[prop][0]} ({PROPERTY_LABELS[prop][1]})",
                          yaxis=dict(autorange="reversed"), legend=dict(orientation="h", y=-0.2))
        c2.plotly_chart(_layout(fig, 280), key="tornado")

    with st.expander("All predicted properties (including illustrative, unvalidated ones)", expanded=False):
        frame = pd.DataFrame([{"Property": PROPERTY_LABELS[k][0], "Unit": PROPERTY_LABELS[k][1], "Value": v,
                               "Status": "calibrated" if k in CALIBRATED_PROPERTIES else "illustrative"}
                              for k, v in pred.items() if v is not None])
        if pred.get("curie_temperature_k") is None:
            st.caption("Curie temperature and saturation magnetisation are reported only for systems containing Fe, Co, Ni, Mn, Cr or Gd.")
        left, right = st.columns([2, 3])
        left.dataframe(frame.assign(Value=frame["Value"].map(_fmt)), hide_index=True)
        _csv_button(frame, "Download CSV", "thanimampro_predictions.csv")
        fig = px.bar(frame, x="Property", y="Value", color="Status", hover_data=["Unit"],
                     color_discrete_map={"calibrated": TEAL, "illustrative": "#94A3B8"},
                     title="Property profile (log scale, mixed units)")
        fig.update_yaxes(type="log", exponentformat="e")
        fig.update_layout(xaxis_tickangle=-40, xaxis_title=None)
        right.plotly_chart(_layout(fig, 380), key="profile")

    st.markdown("#### Save this scenario")
    c1, c2 = st.columns([3, 1])
    name = c1.text_input("Name", value=f"Scenario {len(st.session_state['scenarios']) + 1}", label_visibility="collapsed")
    if c2.button("Save scenario", type="primary"):
        st.session_state["scenarios"].append({"name": name, "conditions": _conditions(), "properties": pred})
        st.toast(f"Saved “{name}”", icon="✅")
        st.rerun()


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
        st.number_input("Instrumental FWHM (° 2θ)", 0.0, 1.0, step=0.01, format="%.3f", key="instrumental_fwhm",
                        help="Width of a standard (e.g. LaB6) on the same instrument; removed in quadrature. "
                             "With 0, the instrument contribution stays in the widths and the size is underestimated.")
        st.checkbox("Scan contains Kα2 (strip it)", key="strip_ka2",
                    help="Rachinger correction for unmonochromated Cu radiation. Leave off for Kα1-only data.")
        if st.button("Analyse structure", type="primary", disabled=data is None):
            try:
                with st.spinner("Detecting peaks and fitting widths…"):
                    st.session_state["structure"] = analyze_structure_file(
                        name, data, instrumental_fwhm_deg=float(st.session_state["instrumental_fwhm"]),
                        strip_ka2=bool(st.session_state["strip_ka2"]))
                    rows = read_pattern(data.decode("utf-8", errors="ignore"))
                    st.session_state["pattern"] = rows if len(rows) >= 3 else None
                st.toast(f"Analysed {name}", icon="🔬")
                st.rerun()
            except ValueError as exc:
                st.error(f"Could not analyse file: {exc}")
        if st.session_state["structure"] is not None and st.button("Clear structure"):
            st.session_state["structure"] = st.session_state["pattern"] = None
            st.rerun()
    with right:
        feats: StructureFeatures | None = st.session_state["structure"]
        if feats is None:
            st.info("No structure loaded. The crystallite size is then estimated from the calcination temperature.")
            return
        c = st.columns(3)
        c[0].metric("Phase", feats.phase)
        c[1].metric("Crystallite (nm)", "n/a" if feats.crystallite_size_nm is None else f"{feats.crystallite_size_nm:.1f}")
        c[2].metric("Microstrain (%)", "n/a" if feats.microstrain_pct is None else f"{feats.microstrain_pct:.3f}")
        c = st.columns(3)
        for col, label, value in zip(c, ("a (Å)", "b (Å)", "c (Å)"), (feats.lattice_a, feats.lattice_b, feats.lattice_c)):
            col.metric(label, "n/a" if value is None else f"{value:.4f}")
        st.caption(f"Source: {feats.source} · size method: **{feats.size_method}** · peaks detected: {feats.n_peaks}"
                   f" · peaks used: {feats.n_peaks_used}")
        if feats.notes:
            st.caption(feats.notes)
    pattern = st.session_state["pattern"]
    if pattern:
        rows = sorted(pattern)
        fig = go.Figure(go.Scatter(x=[r[0] for r in rows], y=[r[1] for r in rows],
                                   mode="lines" if len(rows) >= 50 else "markers",
                                   line=dict(color=TEAL), marker=dict(size=9, color=TEAL), name="Pattern"))
        if len(rows) >= 50:
            peaks = detect_peaks(rows, strip_ka2=bool(st.session_state["strip_ka2"]))
            base = dict(rows)
            fig.add_trace(go.Scatter(x=[p.two_theta for p in peaks],
                                     y=[base.get(p.two_theta, p.intensity) for p in peaks],
                                     mode="markers+text", text=[f"{p.two_theta:.1f}°" for p in peaks], textposition="top center",
                                     marker=dict(color="#C2410C", size=9, symbol="triangle-down"), name="Detected peaks"))
        fig.update_layout(title="Diffraction pattern", xaxis_title="2θ (°)", yaxis_title="Intensity (a.u.)")
        st.plotly_chart(_layout(fig, 380), key="xrd")


def _tab_mapper(synthesis: SynthesisInput) -> None:
    structure = _structure_for_prediction()
    c = st.columns([2, 2, 2, 1])
    prop = c[0].selectbox("Property", _available(predict_properties(synthesis, structure).to_dict()), format_func=lambda k: f"{PROPERTY_LABELS[k][0]} ({PROPERTY_LABELS[k][1]})", key="map_prop")
    temp_range = c[1].slider("Temperature range (°C)", 100, 1500, (450, 900), step=10)
    ph_range = c[2].slider("pH range", 0.0, 14.0, (2.0, 12.0), step=0.2)
    points = c[3].slider("Grid", 5, 50, 25)
    view = st.radio("View", ["Heatmap", "3D surface"], horizontal=True)
    # Live: recomputed on every change (grid of at most 2,500 cheap evaluations).
    with st.spinner("Computing map…"):
        map_df = build_property_map(synthesis, structure, float(temp_range[0]), float(temp_range[1]),
                                    float(ph_range[0]), float(ph_range[1]), points, prop)
    st.session_state["heatmap"] = map_df
    label, unit = PROPERTY_LABELS[prop]
    pivot = map_df.pivot(index="pH", columns="temperature_c", values="value")
    if view == "Heatmap":
        fig = go.Figure(go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorscale="Tealrose",
                                   colorbar=dict(title=unit), hovertemplate="T=%{x:.0f} °C<br>pH=%{y:.2f}<br>value=%{z:.4g}<extra></extra>"))
        if temp_range[0] <= synthesis.temperature_c <= temp_range[1] and ph_range[0] <= synthesis.pH <= ph_range[1]:
            fig.add_trace(go.Scatter(x=[synthesis.temperature_c], y=[synthesis.pH], mode="markers",
                                     marker=dict(symbol="star", size=16, color="white", line=dict(color=INK, width=2)),
                                     name="Current conditions"))
        fig.update_layout(title=f"{label}: temperature × pH", xaxis_title="Temperature (°C)", yaxis_title="pH")
    else:
        fig = go.Figure(go.Surface(z=pivot.values, x=pivot.columns, y=pivot.index, colorscale="Tealrose",
                                   colorbar=dict(title=unit)))
        fig.update_layout(title=f"{label}: temperature × pH",
                          scene=dict(xaxis_title="Temperature (°C)", yaxis_title="pH", zaxis_title=unit))
    st.plotly_chart(_layout(fig, 520), key="map")
    lo, hi = float(map_df["value"].min()), float(map_df["value"].max())
    st.caption(f"Range over the grid: {_fmt(lo)} – {_fmt(hi)} {unit}. Star = current conditions. "
               + ("This property is calibrated on temperature only; the literature table does not support a pH dependence."
                  if prop in CALIBRATED_PROPERTIES else "Illustrative, unvalidated property."))
    _csv_button(map_df.rename(columns={"value": prop}), "Download grid CSV", f"thanimampro_{prop}_map.csv")


def _tab_inverse(synthesis: SynthesisInput) -> None:
    structure = _structure_for_prediction()
    c = st.columns(4)
    target = c[0].number_input("Target band gap (eV)", 0.5, 6.0, 3.15, step=0.05)
    min_sa = c[1].number_input("Min surface area (m²/g)", 1.0, 500.0, 50.0, step=1.0)
    max_ps = c[2].number_input("Max crystallite size (nm)", 2.0, 500.0, 20.0, step=1.0)
    top_k = c[3].number_input("Suggestions", 1, 20, 5)
    if st.button("Suggest conditions", type="primary"):
        with st.spinner("Searching calcination temperatures…"):
            st.session_state["inverse"] = {
                "frame": pd.DataFrame(suggest_synthesis_conditions(
                    synthesis, DesiredPropertyTargets(float(target), float(min_sa), float(max_ps)),
                    structure, top_k=int(top_k))),
                "target": (float(target), float(min_sa)),
                "range": reachable_band_gap_range(synthesis, structure),
                "material": synthesis.material_system,
            }
        st.toast("Suggestions ready", icon="🎯")
    result = st.session_state["inverse"]
    if result is None:
        st.info("Set targets and press **Suggest conditions**.")
        return
    frame, (t_bg, t_sa), (lo, hi) = result["frame"], result["target"], result["range"]
    if not bool(frame["target_reachable"].any()):
        st.warning(f"A band gap of {t_bg:.2f} eV is outside what the surrogate predicts for {result['material']} "
                   f"over the calibrated temperature range ({lo:.2f}–{hi:.2f} eV). The rows below are the nearest "
                   "conditions, not solutions. A doped system (written 'TiO2:Fe') shifts the range by −0.31 eV.")
    elif not bool(frame["meets_all_targets"].any()):
        st.warning("The band gap is attainable, but no calcination temperature in the list meets the band-gap, "
                   "surface-area and crystallite-size targets together. The rows below are the closest compromises.")
    st.caption("Search over calcination temperature (200–1,100 °C, 25 °C steps), the only variable the calibrated "
               "relations respond to. Lower score = closer to the targets.")
    left, right = st.columns([3, 2])
    left.dataframe(frame, hide_index=True)
    fig = px.scatter(frame, x="pred_band_gap_ev", y="pred_surface_area_m2_g", color="score", size_max=14,
                     color_continuous_scale="Tealrose_r", hover_data=["temperature_c", "estimated_crystallite_size_nm"],
                     labels={"pred_band_gap_ev": "Band gap (eV)", "pred_surface_area_m2_g": "Surface area (m²/g)"})
    fig.add_trace(go.Scatter(x=[t_bg], y=[t_sa], mode="markers", name="Target",
                             marker=dict(symbol="star", size=16, color="#C2410C")))
    fig.update_layout(title="Candidates vs target")
    right.plotly_chart(_layout(fig, 340), key="inv_scatter")
    pick = st.selectbox("Candidate to try", frame.index, format_func=lambda i: (
        f"#{i + 1}: {frame.at[i, 'temperature_c']:.0f} °C (band gap {frame.at[i, 'pred_band_gap_ev']:.2f} eV)"))
    row = frame.loc[pick]
    st.button("Apply to sidebar", on_click=_apply, type="primary",
              args=({"temperature_c": float(row["temperature_c"]), "preset": "—"},))
    _csv_button(frame, "Download CSV", "thanimampro_inverse_design.csv")


def _tab_scenarios(synthesis: SynthesisInput) -> None:
    structure = _structure_for_prediction()
    pred = predict_properties(synthesis, structure).to_dict()
    scenarios = st.session_state["scenarios"]
    if not scenarios:
        st.info("No scenarios yet. Save the current conditions from the **Results** tab, change a parameter, and save again to compare.")
    else:
        frame = _scenario_frame()
        st.dataframe(frame, hide_index=True)
        props = [PROPERTY_LABELS[k][0] for k in ("band_gap_ev", "specific_surface_area_m2_g", "absorption_edge_nm")]
        pick = st.selectbox("Compare", props)
        fig = px.bar(frame, x="Scenario", y=pick, color_discrete_sequence=[TEAL], text_auto=".3g")
        st.plotly_chart(_layout(fig, 320), key="scen_bar")
        c = st.columns(3)
        with c[0]:
            _csv_button(frame, "Download comparison CSV", "thanimampro_scenarios.csv")
        if c[1].button("Clear scenarios"):
            st.session_state["scenarios"] = []
            st.rerun()
    st.markdown("#### Report")
    md = _report_markdown(synthesis, pred)
    c = st.columns(2)
    c[0].download_button("Download report (Markdown)", md.encode(), "thanimampro_report.md", "text/markdown")
    c[1].download_button("Download inputs + outputs (JSON)", json.dumps(
        {"conditions": synthesis.to_dict(), "structure": structure.to_dict() if structure else None,
         "predictions": pred, "warnings": scope_warnings(synthesis), "note": CALIBRATION_NOTE}, indent=2).encode(), "thanimampro_run.json", "application/json")
    with st.expander("Preview report"):
        st.markdown(md)


def _tab_literature() -> None:
    frame = load_literature_data(SEED_DATA_PATH)
    if not SEED_DATA_PATH.exists():
        st.info(f"No dataset found at `{SEED_DATA_PATH.relative_to(ROOT)}`. Add a CSV with columns "
                "material_system, method, temperature_c, pH, band_gap_ev, surface_area_m2_g, doi. "
                "See `docs/LITERATURE_DATA_HANDOVER.md`.")
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
    plot = filtered.dropna(subset=["temperature_c", "band_gap_ev"])
    if len(plot) >= 2:
        st.plotly_chart(_layout(px.scatter(plot, x="temperature_c", y="band_gap_ev", color="method",
                                           hover_data=["material_system", "doi"], title="Band gap vs temperature"), 360), key="lit")


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
    _stepper(len(st.session_state["scenarios"]))
    for message in scope_warnings(synthesis):
        st.warning(message)
    tabs = st.tabs(["Results", "Structure", "Relationship map", "Inverse design", "Scenarios & report", "Literature"])
    with tabs[0]:
        _tab_results(synthesis)
    with tabs[1]:
        _tab_structure()
    with tabs[2]:
        _tab_mapper(synthesis)
    with tabs[3]:
        _tab_inverse(synthesis)
    with tabs[4]:
        _tab_scenarios(synthesis)
    with tabs[5]:
        _tab_literature()


if __name__ == "__main__":
    main()
