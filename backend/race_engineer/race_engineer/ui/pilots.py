"""Page Pilotes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from race_engineer.analytics import compute_pilot_stats
from race_engineer.database import get_pilot_laps
from race_engineer.ui._helpers import empty_state, format_lap_value
from race_engineer.utils import format_seconds


def page_pilots(parsed: Optional[Dict[str, Any]], config: Dict[str, Any]) -> None:
    st.title("👤 Pilotes")

    our_numero = str(config.get("our_bike_number", "96"))
    pilots: List[Dict[str, Any]] = [
        p for p in config.get("pilots", []) if p.get("active", True)
    ]

    if not pilots:
        empty_state("Aucun pilote configuré (Paramètres → Pilotes).")
        return

    # Pilote actuel d'après le flux
    current_rider_name = None
    if parsed and parsed.get("rows"):
        ours = next(
            (r for r in parsed["rows"] if str(r.get("numero")) == our_numero),
            None
        )
        if ours:
            current_rider_name = (ours.get("rider") or "").strip()

    # --- Tableau récapitulatif --------------------------------------------
    st.subheader("📋 Vue d'ensemble")

    summary_rows = []
    pilot_stats_cache: Dict[str, Dict[str, Any]] = {}
    for p in pilots:
        stats = compute_pilot_stats(our_numero, p["name"], p.get("alias", []))
        pilot_stats_cache[p["name"]] = stats

        # Détection statut
        if current_rider_name and (
            current_rider_name.lower() == p["name"].strip().lower()
            or current_rider_name.lower() in [a.strip().lower() for a in p.get("alias", [])]
        ):
            status = "🟢 EN RELAIS"
        elif stats["total_laps"] == 0:
            status = "⚪ Disponible"
        else:
            status = "🟡 Relais terminé"

        summary_rows.append({
            "Pilote": p["name"],
            "Statut": status,
            "Tours": stats["total_laps"],
            "Relais": stats["total_relays"],
            "Moyenne": format_lap_value(stats["mean_lap"]),
            "Best": format_lap_value(stats["best_lap"]),
            "Dernier relais (tours)": stats["last_relay_laps_count"],
            "Moy. dernier relais": format_lap_value(stats["last_relay_mean"]),
            "Régularité": f"{stats['regularity_idx']:.0f}/100" if stats['regularity_idx'] is not None else "—",
            "Tendance": stats["trend"],
            "Reco": stats["recommendation"],
        })

    df = pd.DataFrame(summary_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Détail par pilote ------------------------------------------------
    st.subheader("🔍 Détail par pilote")

    selected_name = st.selectbox(
        "Pilote",
        [p["name"] for p in pilots],
        key="pilot_select",
    )
    pilot = next(p for p in pilots if p["name"] == selected_name)
    stats = pilot_stats_cache[selected_name]

    # Bloc activité
    st.markdown("#### Activité course")
    cols = st.columns(4)
    cols[0].metric("Tours totaux", stats["total_laps"])
    cols[1].metric("Relais effectués", stats["total_relays"])
    cols[2].metric("Tours relais en cours", stats["current_relay_laps_count"])
    cols[3].metric("Tours dernier relais", stats["last_relay_laps_count"])

    cols = st.columns(4)
    cols[0].metric("Moy. tours/relais", f"{stats['avg_laps_per_relay']:.1f}" if stats['avg_laps_per_relay'] else "—")
    cols[1].metric("Plus long relais", stats["longest_relay_laps"] or "—")
    cols[2].metric("Plus court relais", stats["shortest_relay_laps"] or "—")
    cols[3].metric("Relais actuel n°", stats["current_relay"] or "—")

    # Bloc performance
    st.markdown("#### Performance chrono")
    cols = st.columns(4)
    cols[0].metric("Meilleur tour", format_lap_value(stats["best_lap"]))
    cols[1].metric("Moyenne globale", format_lap_value(stats["mean_lap"]))
    cols[2].metric("Médiane", format_lap_value(stats["median_lap"]))
    cols[3].metric("Écart-type", format_lap_value(stats["stdev_lap"]) if stats["stdev_lap"] else "—")

    cols = st.columns(4)
    cols[0].metric("Moy. 5 meilleurs", format_lap_value(stats["best5_mean"]))
    cols[1].metric("Moy. 10 derniers", format_lap_value(stats["last10_mean"]))
    cols[2].metric("Moy. relais en cours", format_lap_value(stats["current_relay_mean"]))
    cols[3].metric("Best relais en cours", format_lap_value(stats["current_relay_best"]))

    cols = st.columns(4)
    cols[0].metric("Moy. dernier relais", format_lap_value(stats["last_relay_mean"]))
    cols[1].metric("Best dernier relais", format_lap_value(stats["last_relay_best"]))
    cols[2].metric("Régularité (idx)", f"{stats['regularity_idx']:.0f}/100" if stats['regularity_idx'] is not None else "—")
    cols[3].metric("Tendance", stats["trend"])

    # Dégradation
    st.markdown("#### Dégradation dans le relais")
    cols = st.columns(3)
    cols[0].metric("Moy. 3 premiers tours", format_lap_value(stats["deg_first3_mean"]))
    cols[1].metric("Moy. 3 derniers tours", format_lap_value(stats["deg_last3_mean"]))
    cols[2].metric("Delta dégradation", format_lap_value(stats["degradation"]) if stats["degradation"] else "—")

    # Reco
    st.info(f"💡 Recommandation : **{stats['recommendation']}**")

    # ---- Graphiques ------------------------------------------------------
    if HAS_PLOTLY:
        st.markdown("#### 📈 Évolution des temps au tour")
        lap_secs = stats["raw_lap_secs"]
        if lap_secs:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=lap_secs,
                mode="lines+markers",
                name=selected_name,
                line=dict(color=pilot.get("color", "#e63946")),
            ))
            if stats["mean_lap"]:
                fig.add_hline(y=stats["mean_lap"], line_dash="dash", line_color="gray",
                              annotation_text=f"Moy. {format_seconds(stats['mean_lap'])}")
            fig.update_layout(
                yaxis_title="Temps (s)",
                xaxis_title="Tour",
                height=400,
                margin=dict(l=20, r=20, t=30, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Aucun tour enregistré pour ce pilote.")

        # Histogramme tous pilotes
        st.markdown("#### 📊 Comparaison entre pilotes")
        fig2 = go.Figure()
        for p in pilots:
            ps = pilot_stats_cache[p["name"]]
            if ps["raw_lap_secs"]:
                fig2.add_trace(go.Box(
                    y=ps["raw_lap_secs"],
                    name=p["name"],
                    marker_color=p.get("color", "#888"),
                ))
        if fig2.data:
            fig2.update_layout(yaxis_title="Temps (s)", height=400, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.caption("ℹ️ Installez `plotly` pour les graphiques.")
