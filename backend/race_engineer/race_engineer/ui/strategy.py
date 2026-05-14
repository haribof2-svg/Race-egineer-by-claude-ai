"""Page Stratégie : timeline, carburant, pneus, simulation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from race_engineer.analytics import estimate_fuel_status
from race_engineer.database import (
    add_planned_event,
    delete_planned_event,
    get_planned_events,
    update_planned_event,
)
from race_engineer.ui._helpers import find_our_bike, empty_state


EVENT_TYPES = ["PIT", "Changement pilote", "Changement pneus", "Safety Car", "Freins", "Autre"]

EVENT_COLORS = {
    "PIT": "#f4a261",
    "Changement pilote": "#457b9d",
    "Changement pneus": "#2a9d8f",
    "Safety Car": "#e63946",
    "Freins": "#9b59b6",
    "Autre": "#888888",
}


def page_strategy(parsed: Optional[Dict[str, Any]], config: Dict[str, Any]) -> None:
    st.title("🧠 Stratégie")

    our_numero = str(config.get("our_bike_number", "96"))
    our = find_our_bike(parsed, our_numero)
    current_lap = (our.get("laps") if our else None) or 0

    tabs = st.tabs(["📅 Timeline", "⛽ Carburant", "🛞 Pneus", "🔮 Simulation"])

    # ====================================================================
    # Tab 1 - Timeline
    # ====================================================================
    with tabs[0]:
        st.subheader("Timeline stratégique")
        st.caption(f"Tour actuel : **{current_lap}**")

        # Form ajout
        with st.expander("➕ Ajouter un événement", expanded=False):
            with st.form("add_event_form", clear_on_submit=True):
                ev_lap = st.number_input("Tour", min_value=0, value=max(current_lap, 0), step=1)
                ev_type = st.selectbox("Type", EVENT_TYPES)
                ev_desc = st.text_input("Description (optionnel)", value="")
                submitted = st.form_submit_button("Ajouter")
                if submitted:
                    add_planned_event(
                        lap=int(ev_lap),
                        event_type=ev_type,
                        description=ev_desc,
                        created_at=datetime.now(timezone.utc).isoformat(),
                    )
                    st.success("Événement ajouté.")
                    st.rerun()

        events = [dict(e) for e in get_planned_events()]

        if events:
            # Graphique timeline
            if HAS_PLOTLY:
                fig = go.Figure()
                max_lap = max(current_lap + 10, max((e["lap"] or 0) for e in events) + 5)
                fig.add_vrect(x0=0, x1=current_lap, fillcolor="rgba(150,150,150,0.15)",
                              line_width=0, annotation_text="Passé", annotation_position="top left")
                for e in events:
                    if e["lap"] is None:
                        continue
                    color = EVENT_COLORS.get(e["type"], "#888")
                    fig.add_trace(go.Scatter(
                        x=[e["lap"]],
                        y=[e["type"]],
                        mode="markers+text",
                        marker=dict(size=18, color=color, symbol="diamond"),
                        text=[e["description"] or ""],
                        textposition="top center",
                        name=e["type"],
                        showlegend=False,
                    ))
                fig.add_vline(x=current_lap, line_color="#ffd700", line_width=2,
                              annotation_text="Now", annotation_position="top")
                fig.update_layout(
                    xaxis_title="Tour", height=350, margin=dict(l=20, r=20, t=30, b=20),
                    xaxis_range=[0, max_lap],
                )
                st.plotly_chart(fig, use_container_width=True)

            # Tableau éditable
            st.markdown("##### Événements planifiés")
            for e in events:
                cols = st.columns([1, 2, 4, 1])
                with cols[0]:
                    st.text(f"T{e['lap']}" if e['lap'] is not None else "—")
                with cols[1]:
                    st.text(e["type"])
                with cols[2]:
                    st.text(e["description"] or "")
                with cols[3]:
                    if st.button("🗑️", key=f"del_evt_{e['id']}"):
                        delete_planned_event(e["id"])
                        st.rerun()
        else:
            empty_state("Aucun événement planifié. Ajoutez-en un avec le formulaire ci-dessus.")

    # ====================================================================
    # Tab 2 - Carburant
    # ====================================================================
    with tabs[1]:
        st.subheader("Carburant")
        fuel_cfg = config.get("fuel", {})

        cols = st.columns(4)
        cols[0].metric("Capacité réservoir", f"{fuel_cfg.get('tank_capacity_l', 24.0)} L")
        cols[1].metric("Conso L/tour (est.)", f"{fuel_cfg.get('consumption_l_per_lap', 3.2)}")
        cols[2].metric("Marge sécurité", f"{fuel_cfg.get('safety_margin_laps', 1)} tours")
        cols[3].metric("Plein remis", f"{fuel_cfg.get('refuel_amount_l', 24.0)} L")

        if our:
            fuel = estimate_fuel_status(
                laps_done=our.get("laps") or 0,
                last_pit_laps=our.get("last_pit") or 0,
                fuel_config=fuel_cfg,
            )
            cols = st.columns(4)
            cols[0].metric("Carburant restant", f"{fuel['fuel_remaining_l']} L" if fuel['fuel_remaining_l'] else "—")
            cols[1].metric("Tours restants estimés", fuel['laps_remaining'] if fuel['laps_remaining'] is not None else "—")
            cols[2].metric("Tours max/relais", fuel['max_laps_per_stint'] if fuel['max_laps_per_stint'] else "—")
            cols[3].metric("Pit window", "🚨 OUVERTE" if fuel['pit_window_open'] else "Fermée")

            if fuel.get("max_laps_per_stint"):
                next_pit_lap = (our.get("laps") or 0) + fuel.get("laps_remaining", 0)
                st.info(f"📍 **Prochain arrêt estimé** : autour du tour **{next_pit_lap}**")
        else:
            st.caption("Données live nécessaires.")

        st.caption("⚠️ Toutes les valeurs sont des estimations basées sur la configuration.")

    # ====================================================================
    # Tab 3 - Pneus
    # ====================================================================
    with tabs[2]:
        st.subheader("Pneus")
        tire_cfg = config.get("tires", {})
        if not tire_cfg.get("tracking_enabled"):
            st.info("ℹ️ Le suivi des pneus n'est pas activé. Activez-le dans Paramètres → Pneus.")

        # Inputs manuels d'usure
        st.markdown("#### Usure manuelle")
        cols = st.columns(4)
        labels = ["Avant gauche", "Avant droit", "Arrière gauche", "Arrière droit"]
        keys = ["tire_fl", "tire_fr", "tire_rl", "tire_rr"]
        wear_per_lap = float(tire_cfg.get("wear_per_lap_pct", 1.5))
        for i, (lbl, key) in enumerate(zip(labels, keys)):
            with cols[i]:
                if key not in st.session_state:
                    st.session_state[key] = 0.0
                wear = st.slider(lbl + " (% usure)", 0.0, 100.0,
                                 value=float(st.session_state[key]),
                                 step=1.0, key=key)
                impact = wear * float(tire_cfg.get("performance_impact_pct_per_pct_wear", 0.05))
                remaining_laps = int(max(0, (100 - wear) / wear_per_lap)) if wear_per_lap > 0 else 0
                st.caption(f"Impact perf: ~{impact:.2f}%  \nTours restants: ~{remaining_laps}")

    # ====================================================================
    # Tab 4 - Simulation
    # ====================================================================
    with tabs[3]:
        st.subheader("Simulation")
        if not our:
            empty_state("Données live requises pour simuler.")
            return

        st.markdown("Comparez 3 scénarios stratégiques :")

        scenarios = []
        cols = st.columns(3)
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"**Scénario {chr(65+i)}**")
                pit_in = st.number_input(f"Pit dans X tours", min_value=0, max_value=50,
                                          value=[0, 5, 10][i], step=1, key=f"sim_pit_{i}")
                change_pilot = st.checkbox("Changer pilote", key=f"sim_pilot_{i}", value=(i > 0))
                change_tires = st.checkbox("Changer pneus", key=f"sim_tires_{i}", value=(i == 2))
                scenarios.append({
                    "name": f"Scénario {chr(65+i)}",
                    "pit_in_laps": pit_in,
                    "change_pilot": change_pilot,
                    "change_tires": change_tires,
                })

        # Calcul simple : pit standard = 60s, +30s si changement pilote, +20s si pneus
        results = []
        for s in scenarios:
            pit_cost = 60.0
            if s["change_pilot"]:
                pit_cost += 30.0
            if s["change_tires"]:
                pit_cost += 20.0
            results.append({
                "Scénario": s["name"],
                "Pit dans": f"+{s['pit_in_laps']} tours",
                "Pilote": "Oui" if s["change_pilot"] else "Non",
                "Pneus": "Oui" if s["change_tires"] else "Non",
                "Coût estimé arrêt": f"{pit_cost:.0f}s",
                "Tour estimé du pit": (our.get("laps") or 0) + s["pit_in_laps"],
            })

        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        st.caption("Estimation simple — les coûts par défaut sont configurables.")
