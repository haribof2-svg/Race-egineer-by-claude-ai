"""Page Notre Moto."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from race_engineer.analytics import estimate_fuel_status
from race_engineer.database import get_pilot_laps
from race_engineer.relay_tracker import get_relay_summary
from race_engineer.ui._helpers import find_our_bike, format_lap_value, empty_state
from race_engineer.utils import format_seconds, parse_lap_time, safe_mean, safe_min


def page_our_bike(parsed: Optional[Dict[str, Any]], config: Dict[str, Any]) -> None:
    our_numero = str(config.get("our_bike_number", "96"))
    st.title(f"🏍️ Notre moto — n°{our_numero}")

    our = find_our_bike(parsed, our_numero)
    if not our and not parsed:
        empty_state("Aucun flux live actif. Utiliser le live ou l'historique.")
        return

    # ---- Informations live ----------------------------------------------
    if our:
        cols = st.columns(4)
        cols[0].metric("Équipe", our.get("team", "—"))
        cols[1].metric("Catégorie", our.get("categorie", "—"))
        cols[2].metric("Tours", our.get("laps") or 0)
        cols[3].metric("Pilote", our.get("rider", "—"))

        cols = st.columns(4)
        cols[0].metric("Dernier tour", format_lap_value(parse_lap_time(our.get("l_lap"))))
        cols[1].metric("Meilleur tour", format_lap_value(parse_lap_time(our.get("best_lap"))))
        cols[2].metric("Tours depuis stand", our.get("last_pit") or 0)
        cols[3].metric("Total arrêts", our.get("total_pit") or 0)

    # ---- Stats issues de la base ----------------------------------------
    st.subheader("📈 Statistiques globales")

    laps = [dict(l) for l in get_pilot_laps(numero=our_numero)]
    lap_secs = [l["lap_seconds"] for l in laps if l.get("lap_seconds") is not None]

    relay_summary = get_relay_summary(our_numero)

    cols = st.columns(4)
    cols[0].metric("Moyenne globale", format_lap_value(safe_mean(lap_secs)))
    cols[1].metric("Meilleur tour (DB)", format_lap_value(safe_min(lap_secs)))
    cols[2].metric("Total tours (DB)", len(laps))
    cols[3].metric("Relais terminés", relay_summary["count"])

    cols = st.columns(4)
    cols[0].metric("Moyenne tours/relais", f"{relay_summary['avg_laps_per_relay']:.1f}" if relay_summary['avg_laps_per_relay'] else "—")
    cols[1].metric("Plus long relais", relay_summary['longest_relay'] if relay_summary['longest_relay'] else "—")
    cols[2].metric("Plus court relais", relay_summary['shortest_relay'] if relay_summary['shortest_relay'] else "—")
    cols[3].metric("Tps arrêt moyen", format_lap_value(relay_summary['avg_pit_seconds']))

    # ---- Carburant / pit window -----------------------------------------
    st.subheader("⛽ Carburant & prédictions")
    if our:
        fuel = estimate_fuel_status(
            laps_done=our.get("laps") or 0,
            last_pit_laps=our.get("last_pit") or 0,
            fuel_config=config.get("fuel", {}),
        )
        cols = st.columns(4)
        cols[0].metric("Carburant restant", f"{fuel['fuel_remaining_l']} L" if fuel['fuel_remaining_l'] else "—")
        cols[1].metric("Tours restants", fuel['laps_remaining'] if fuel['laps_remaining'] is not None else "—")
        cols[2].metric("Max tours/relais", fuel['max_laps_per_stint'] if fuel['max_laps_per_stint'] else "—")
        cols[3].metric("Pit window", "🚨 OUVERTE" if fuel['pit_window_open'] else "Fermée")

        st.caption("⚠️ Estimations basées sur la consommation configurée — à ajuster en Paramètres.")

    # ---- Historique des relais ------------------------------------------
    st.subheader("📋 Historique des relais")
    if relay_summary["relays"]:
        df = pd.DataFrame(relay_summary["relays"])
        keep_cols = [c for c in ("relais", "tours_relais", "last_pit_time", "last_pit_seconds", "pilote", "tour_total") if c in df.columns]
        st.dataframe(df[keep_cols] if keep_cols else df, use_container_width=True, hide_index=True)
    else:
        empty_state("Aucun relais terminé pour le moment.")
