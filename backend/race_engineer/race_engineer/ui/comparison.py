"""Page Comparatif moto 96 vs concurrent."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from race_engineer.analytics import build_comparison
from race_engineer.exports import export_comparison_csv
from race_engineer.ui._helpers import (
    collect_categories,
    empty_state,
    filter_rows_by_category,
)
from race_engineer.utils import format_seconds, format_signed


def page_comparison(parsed: Optional[Dict[str, Any]], config: Dict[str, Any]) -> None:
    st.title("⚖️ Comparatif — Notre moto vs Concurrent")

    our_numero = str(config.get("our_bike_number", "96"))

    # ---- Sélection du concurrent ----------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        cats = collect_categories(parsed) if parsed else []
        default_cat = config.get("our_category", "PRD")
        options = ["ALL"] + sorted({c for c in cats if c})
        idx = options.index(default_cat) if default_cat in options else 0
        sel_cat = st.selectbox("Catégorie du concurrent", options, index=idx, key="comp_cat")

    rows = parsed["rows"] if (parsed and parsed.get("rows")) else []
    cand_rows = [r for r in rows if str(r.get("numero")) != our_numero]
    if sel_cat != "ALL":
        cand_rows = [r for r in cand_rows if str(r.get("categorie", "")).strip() == sel_cat]

    competitor_options = [r.get("numero") for r in cand_rows if r.get("numero")]
    default_competitor = config.get("competitors", {}).get("main_comparison", "")
    if default_competitor and default_competitor not in competitor_options:
        competitor_options.insert(0, default_competitor)

    with col2:
        if not competitor_options:
            st.warning("Aucun concurrent disponible dans cette catégorie.")
            return
        idx = competitor_options.index(default_competitor) if default_competitor in competitor_options else 0
        sel_competitor = st.selectbox("Concurrent", competitor_options, index=idx, key="cmp_select")

    if not sel_competitor:
        return

    # ---- Calcul du comparatif -------------------------------------------
    comparison = build_comparison(our_numero, str(sel_competitor))

    if not comparison["rows"]:
        empty_state("Pas encore de relais enregistré pour calculer un comparatif.")
        return

    # ---- KPIs principaux -------------------------------------------------
    totals = comparison["totals"]
    cols = st.columns(3)
    cols[0].metric("Gain/perte piste total", format_signed(totals["gain_piste_total"]))
    cols[1].metric("Gain/perte stand total", format_signed(totals["gain_pit_total"]))
    cols[2].metric("Bilan global cumulé", format_signed(totals["bilan_total"]))

    # ---- Highlights ------------------------------------------------------
    cols = st.columns(4)
    if comparison["best_gain_relay"]:
        bg = comparison["best_gain_relay"]
        cols[0].metric("Meilleur relais", f"R{bg['relais']}",
                       delta=format_signed(bg['bilan']))
    if comparison["worst_loss_relay"]:
        wl = comparison["worst_loss_relay"]
        cols[1].metric("Pire relais", f"R{wl['relais']}",
                       delta=format_signed(wl['bilan']))
    if comparison["best_pit_relay"]:
        bp = comparison["best_pit_relay"]
        cols[2].metric("Meilleur arrêt", f"R{bp['relais']}",
                       delta=format_signed(bp['gain_pit']))
    if comparison["worst_pit_relay"]:
        wp = comparison["worst_pit_relay"]
        cols[3].metric("Pire arrêt", f"R{wp['relais']}",
                       delta=format_signed(wp['gain_pit']))

    # ---- Tableau détaillé ------------------------------------------------
    st.subheader("📋 Détail relais par relais")
    display_rows = []
    for r in comparison["rows"]:
        display_rows.append({
            "Relais": f"R{r['relais']}",
            "Tours 96": r["tours_96"] or "—",
            "Tours conc.": r["tours_conc"] or "—",
            "Moy. 96": format_seconds(r["moy_96"]) if r["moy_96"] else "—",
            "Moy. conc.": format_seconds(r["moy_conc"]) if r["moy_conc"] else "—",
            "Piste 96": format_seconds(r["piste_96"]) if r["piste_96"] else "—",
            "Piste conc.": format_seconds(r["piste_conc"]) if r["piste_conc"] else "—",
            "Gain piste": format_signed(r["gain_piste"]),
            "Arrêt 96": format_seconds(r["pit_96"]) if r["pit_96"] else "—",
            "Arrêt conc.": format_seconds(r["pit_conc"]) if r["pit_conc"] else "—",
            "Gain stand": format_signed(r["gain_pit"]),
            "Bilan": format_signed(r["bilan"]),
            "Cumul": format_signed(r["cumul"]),
        })
    df = pd.DataFrame(display_rows)

    def _color_signed(val):
        if not isinstance(val, str) or val == "—":
            return ""
        if val.startswith("+"):
            return "color: #2bb673; font-weight: 600;"
        if val.startswith("−") or val.startswith("-"):
            return "color: #d94545; font-weight: 600;"
        return "color: #888;"

    styler = df.style.map(_color_signed, subset=["Gain piste", "Gain stand", "Bilan", "Cumul"])
    st.dataframe(styler, use_container_width=True, hide_index=True)

    st.caption(
        "🟢 Vert = gain pour la 96  |  🔴 Rouge = perte pour la 96"
    )

    # ---- Graphiques ------------------------------------------------------
    if HAS_PLOTLY:
        st.subheader("📈 Visualisations")
        valid = [r for r in comparison["rows"] if r["bilan"] is not None]
        if valid:
            labels = [f"R{r['relais']}" for r in valid]
            piste_vals = [r["gain_piste"] or 0 for r in valid]
            pit_vals = [r["gain_pit"] or 0 for r in valid]
            cumul_vals = [r["cumul"] or 0 for r in valid]

            # Cumul
            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                x=labels, y=cumul_vals, mode="lines+markers",
                fill="tozeroy", line=dict(color="#ffd700", width=2),
                name="Cumul",
            ))
            fig_cum.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_cum.update_layout(
                title="Cumul gain/perte (s)",
                yaxis_title="Secondes (>0 = gain pour 96)",
                height=350, margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_cum, use_container_width=True)

            # Barres piste vs stand
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(x=labels, y=piste_vals, name="Piste", marker_color="#457b9d"))
            fig_bar.add_trace(go.Bar(x=labels, y=pit_vals, name="Stand", marker_color="#f4a261"))
            fig_bar.update_layout(
                title="Gain/perte par relais : piste vs stand",
                barmode="group",
                yaxis_title="Secondes",
                height=350, margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.caption("Pas assez de données pour les graphiques.")

    # ---- Predictions / extension prédictive -----------------------------
    st.subheader("🔮 Extension prédictive")
    valid_bilans = [r["bilan"] for r in comparison["rows"] if r["bilan"] is not None]
    if len(valid_bilans) >= 2:
        avg_per_relay = sum(valid_bilans) / len(valid_bilans)
        proj_3 = avg_per_relay * 3
        st.markdown(f"- **Projection 3 prochains relais** (si tendance continue) : {format_signed(proj_3)}")
        if avg_per_relay < 0:
            comp_needed = -avg_per_relay
            st.markdown(
                f"- **Pour compenser le déficit**, il faudrait gagner ~{comp_needed:.2f}s "
                f"par relais (au stand ou en piste)."
            )
    else:
        st.caption("Au moins 2 relais terminés sont nécessaires pour une projection.")

    # ---- Export ---------------------------------------------------------
    st.download_button(
        "📥 Export CSV du comparatif",
        data=export_comparison_csv(comparison),
        file_name=f"comparaison_{our_numero}_vs_{sel_competitor}.csv",
        mime="text/csv",
    )
