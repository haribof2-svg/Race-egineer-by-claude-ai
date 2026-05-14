"""Page Historique / Replay."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from race_engineer.database import (
    count_snapshots,
    get_snapshot_payload,
    get_snapshots,
    db_size_bytes,
)
from race_engineer.exports import (
    build_excel_export,
    export_laps_csv,
    export_relays_csv,
    export_snapshots_json,
    export_planned_events_json,
    export_config_json,
)
from race_engineer.live_timing import parse_live_payload
from race_engineer.ui._helpers import empty_state, format_lap_value


def page_history(parsed: Optional[Dict[str, Any]], config: Dict[str, Any]) -> None:
    st.title("🕒 Historique / Replay")

    n_snaps = count_snapshots()
    size_kb = db_size_bytes() / 1024

    cols = st.columns(3)
    cols[0].metric("Snapshots enregistrés", n_snaps)
    cols[1].metric("Taille DB", f"{size_kb:.1f} KB")
    cols[2].metric("Snapshots / cette session", st.session_state.get("saved_snapshot_count", 0))

    if n_snaps == 0:
        empty_state("Aucun snapshot enregistré pour le moment. Lancez l'app pendant le live pour collecter.")
    else:
        st.subheader("Replay d'un snapshot")
        snaps = get_snapshots(limit=500)

        # Sélecteur via slider + dropdown
        options = {
            f"#{s['id']} — {s['fetched_at']}": s["id"]
            for s in snaps
        }
        labels = list(options.keys())
        # Slider
        slider_idx = st.slider("Position dans le temps", 0, len(labels) - 1, len(labels) - 1)
        selected_label = labels[len(labels) - 1 - slider_idx]  # plus récent à droite

        # Affiche également un select pour précision
        selected_label = st.selectbox("Snapshot précis", labels, index=labels.index(selected_label))

        snapshot_id = options[selected_label]
        payload = get_snapshot_payload(snapshot_id)

        if not payload:
            st.error("Snapshot non lisible.")
        else:
            replay_parsed = parse_live_payload(payload)
            if replay_parsed and replay_parsed.get("rows"):
                st.caption(f"Replay snapshot #{snapshot_id} — {replay_parsed['fetched_at']}")
                df = pd.DataFrame(replay_parsed["rows"])
                our_numero = str(config.get("our_bike_number", "96"))

                def _style(row):
                    if str(row.get("numero")) == our_numero:
                        return ["background-color: rgba(255, 215, 0, 0.25); font-weight: 600;"] * len(row)
                    return [""] * len(row)

                st.dataframe(df.style.apply(_style, axis=1), use_container_width=True, hide_index=True)
            else:
                empty_state("Snapshot vide ou non parsable.")

    # ---- Exports ---------------------------------------------------------
    st.subheader("📥 Exports")

    our_numero = str(config.get("our_bike_number", "96"))

    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Excel**")
        excel_data = build_excel_export(parsed, our_numero, comparison=None, config=config)
        st.download_button(
            "📊 Export Excel complet",
            data=excel_data,
            file_name="race_engineer_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with cols[1]:
        st.markdown("**CSV**")
        st.download_button(
            "📑 Relais",
            data=export_relays_csv(),
            file_name="relay_events.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "📑 Tours (notre moto)",
            data=export_laps_csv(numero=our_numero),
            file_name=f"pilot_laps_{our_numero}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with cols[2]:
        st.markdown("**JSON**")
        st.download_button(
            "🗂️ Snapshots (100 derniers)",
            data=export_snapshots_json(limit=100),
            file_name="snapshots.json",
            mime="application/json",
            use_container_width=True,
        )
        st.download_button(
            "🗂️ Événements planifiés",
            data=export_planned_events_json(),
            file_name="planned_events.json",
            mime="application/json",
            use_container_width=True,
        )
        st.download_button(
            "🗂️ Config",
            data=export_config_json(config),
            file_name="race_engineer_config.json",
            mime="application/json",
            use_container_width=True,
        )
