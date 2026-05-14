"""Initialisation du session_state Streamlit (centralisée pour éviter KeyError)."""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st


_DEFAULTS: Dict[str, Any] = {
    "nav_index": 0,
    "last_parsed": None,
    "last_raw": None,
    "last_fetch_error": None,
    "relay_state": {},
    "saved_snapshot_count": 0,
    "selected_competitor": None,
    "category_filter": "PRD",
    "replay_snapshot_id": None,
    "history_view_mode": "live",   # 'live' ou 'replay'
    # Simulateur
    "simulator_running": False,
    "simulator_elapsed": 0.0,      # minutes de course simulées
    "simulator_speed": 1.0,        # multiplicateur de vitesse
    "simulator_last_tick": None,   # timestamp réel du dernier tick
    "simulator_duration": 1440,    # durée totale de la course en minutes (24 h)
}


def ensure_session_state() -> None:
    """Garantit que toutes les clés attendues existent dans st.session_state."""
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default
