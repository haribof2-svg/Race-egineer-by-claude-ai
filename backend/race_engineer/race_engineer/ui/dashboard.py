"""Page Dashboard."""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from race_engineer.analytics import estimate_fuel_status
from race_engineer.database import save_snapshot
from race_engineer.relay_tracker import process_snapshot_for_relays
from race_engineer.ui._helpers import find_our_bike, format_lap_value, empty_state
from race_engineer.utils import format_seconds, format_signed, parse_lap_time


def page_dashboard(parsed: Optional[Dict[str, Any]], config: Dict[str, Any]) -> None:
    st.title("📊 Dashboard")

    # Persister snapshot + détecter relais à chaque rafraîchissement
    if parsed:
        try:
            save_snapshot(parsed["fetched_at"], parsed)
            st.session_state["saved_snapshot_count"] = st.session_state.get("saved_snapshot_count", 0) + 1
        except Exception as exc:
            st.warning(f"Snapshot non sauvegardé : {exc}")
        process_snapshot_for_relays(parsed)

    our_numero = str(config.get("our_bike_number", "96"))
    our = find_our_bike(parsed, our_numero)

    if not our:
        empty_state(
            f"La moto n°{our_numero} n'est pas trouvée dans le flux live. "
            "Vérifiez l'URL et le numéro dans Paramètres."
        )
        return

    # --- Bandeau principal -------------------------------------------------
    cols = st.columns(4)
    cols[0].metric("Position", our.get("position") or "—",
                   delta=f"Cat. {our.get('position_cat') or '—'}")
    cols[1].metric("Catégorie", our.get("categorie") or "—")
    cols[2].metric("Tours", our.get("laps") or "—")
    cols[3].metric("Pilote", our.get("rider") or "—")

    # --- Chronos -----------------------------------------------------------
    st.subheader("⏱️ Chronos")
    cols = st.columns(3)
    cols[0].metric("Dernier tour", format_lap_value(parse_lap_time(our.get("l_lap"))))
    cols[1].metric("Meilleur tour", format_lap_value(parse_lap_time(our.get("best_lap"))))
    last_pit = our.get("last_pit")
    cols[2].metric("Tours depuis stand", last_pit if last_pit is not None else "—")

    # --- Pit info ----------------------------------------------------------
    st.subheader("🔧 Stands")
    cols = st.columns(4)
    cols[0].metric("Total arrêts", our.get("total_pit") or 0)
    cols[1].metric("Dernier arrêt", str(our.get("last_pit_time") or "—"))
    cols[2].metric("Temps total stands", str(our.get("total_pit_time") or "—"))
    pit_state = our.get("pit_state")
    cols[3].metric(
        "État",
        "🛑 Pit In" if pit_state == "PIT_IN" else "🟢 Pit Out" if pit_state == "PIT_OUT" else "🏁 En piste"
    )

    # --- Carburant & pit window -------------------------------------------
    st.subheader("⛽ Carburant & Pit Window")
    fuel = estimate_fuel_status(
        laps_done=our.get("laps") or 0,
        last_pit_laps=our.get("last_pit") or 0,
        fuel_config=config.get("fuel", {}),
    )
    cols = st.columns(4)
    cols[0].metric("Carburant restant (est.)", f"{fuel['fuel_remaining_l']} L" if fuel.get("fuel_remaining_l") else "—")
    cols[1].metric("Tours restants (est.)", fuel.get("laps_remaining") if fuel.get("laps_remaining") is not None else "—")
    cols[2].metric("Tours max / relais", fuel.get("max_laps_per_stint") if fuel.get("max_laps_per_stint") else "—")
    cols[3].metric("Pit window", "🚨 OUVERTE" if fuel.get("pit_window_open") else "Fermée")

    if fuel.get("pit_window_open"):
        st.warning("⚠️ La moto approche de la fenêtre de pit — préparer l'arrêt.")

    # --- Concurrent direct -------------------------------------------------
    st.subheader("🎯 Concurrent direct")
    competitor_num = config.get("competitors", {}).get("main_comparison", "")
    if not competitor_num:
        st.caption("Aucun concurrent principal défini (Paramètres → Concurrents).")
    else:
        comp_row = next(
            (r for r in (parsed.get("rows") or []) if str(r.get("numero")) == str(competitor_num)),
            None
        )
        if not comp_row:
            st.caption(f"Concurrent n°{competitor_num} introuvable dans le flux live.")
        else:
            cols = st.columns(4)
            cols[0].metric(f"N°{competitor_num} — {comp_row.get('team', '?')}",
                           f"Pos. {comp_row.get('position') or '—'}")
            cols[1].metric("Tours", comp_row.get("laps") or "—")
            cols[2].metric("Dernier tour", format_lap_value(parse_lap_time(comp_row.get("l_lap"))))
            cols[3].metric("Best", format_lap_value(parse_lap_time(comp_row.get("best_lap"))))

    # --- Message stratégique synthétique -----------------------------------
    st.subheader("🧠 Synthèse stratégique")
    msgs = []
    if fuel.get("pit_window_open"):
        msgs.append("• Préparer l'arrêt au stand dans les prochains tours.")
    if pit_state == "PIT_IN":
        msgs.append("• Moto en entrée de stand.")
    if pit_state == "PIT_OUT":
        msgs.append("• Moto en sortie de stand — surveiller la cohérence du chrono.")
    if not msgs:
        msgs.append("• Course en rythme — pas d'alerte particulière.")
    for m in msgs:
        st.markdown(m)

    # --- Erreurs de fetch --------------------------------------------------
    if st.session_state.get("last_fetch_error"):
        st.caption(f"⚠️ Dernière erreur de fetch : {st.session_state['last_fetch_error']}")
