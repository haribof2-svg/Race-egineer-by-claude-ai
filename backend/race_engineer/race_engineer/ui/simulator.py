"""Page Simulateur — rejoue une course fictive avec vitesse d'écoulement variable."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception:
    HAS_AUTOREFRESH = False

from race_engineer.mock_data import generate_mock_payload
from race_engineer.live_timing import parse_live_payload
from race_engineer.relay_tracker import process_snapshot_for_relays
from race_engineer.database import save_snapshot


# ---------------------------------------------------------------------------
# Durées de course disponibles
# ---------------------------------------------------------------------------
_DURATIONS = {
    "2 h  (sprint)":    120,
    "4 h":              240,
    "6 h":              360,
    "8 h":              480,
    "12 h":             720,
    "24 h  (classique)": 1440,
    "48 h":             2880,
}

_SPEED_OPTIONS = [0.5, 1, 2, 5, 10, 30, 60]
_TICK_INTERVAL_MS = 1000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fmt_time(minutes: float) -> str:
    total_s = int(minutes * 60)
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _apply_tick(speed: float, duration_min: int) -> None:
    now = time.time()
    last = st.session_state.get("simulator_last_tick")
    if last is not None:
        delta_real_s = now - last
        delta_sim_min = delta_real_s * speed / 60.0
        elapsed = st.session_state.get("simulator_elapsed", 0.0) + delta_sim_min
        capped = min(elapsed, float(duration_min))
        st.session_state["simulator_elapsed"] = capped
        # Auto-stop en fin de course
        if capped >= duration_min:
            st.session_state["simulator_running"] = False
    st.session_state["simulator_last_tick"] = now


def _push_snapshot() -> Dict[str, Any]:
    elapsed = st.session_state.get("simulator_elapsed", 0.0)
    mock = generate_mock_payload(elapsed_minutes=elapsed)
    parsed = parse_live_payload(mock)

    fetched_at = datetime.now(timezone.utc).isoformat()
    parsed["fetched_at"] = fetched_at

    st.session_state["last_parsed"] = parsed
    st.session_state["last_raw"] = mock

    save_snapshot(fetched_at=fetched_at, payload=mock)
    process_snapshot_for_relays(parsed)

    return parsed


# ---------------------------------------------------------------------------
# Page principale
# ---------------------------------------------------------------------------
def page_simulator(parsed: Optional[Dict[str, Any]] = None, config: Optional[Dict[str, Any]] = None) -> None:
    st.title("🎮 Simulateur de course")
    st.caption(
        "Génère un flux fictif pour tester toutes les pages. "
        "Les données sont injectées dans le même pipeline que le live — "
        "relais, pilotes, historique et stratégie se remplissent en temps réel."
    )

    running = st.session_state.get("simulator_running", False)

    # --- Auto-refresh quand le simulateur tourne ----------------------------
    if running and HAS_AUTOREFRESH:
        st_autorefresh(interval=_TICK_INTERVAL_MS, key="sim_autorefresh")
    elif running and not HAS_AUTOREFRESH:
        st.warning("⚠️ `streamlit-autorefresh` non installé — refresh manuel uniquement.")

    # -----------------------------------------------------------------------
    # Ligne 1 : durée de course
    # -----------------------------------------------------------------------
    duration_label = st.selectbox(
        "🏁 Durée de la course",
        options=list(_DURATIONS.keys()),
        index=list(_DURATIONS.values()).index(
            st.session_state.get("simulator_duration", 1440)
        ) if st.session_state.get("simulator_duration", 1440) in _DURATIONS.values() else 5,
        disabled=running or st.session_state.get("simulator_elapsed", 0.0) > 0,
        help="Choisissez avant de démarrer. Modifiez après un Reset.",
    )
    duration_min: int = _DURATIONS[duration_label]
    st.session_state["simulator_duration"] = duration_min

    st.divider()

    # -----------------------------------------------------------------------
    # Ligne 2 : boutons de contrôle
    # -----------------------------------------------------------------------
    col_play, col_jump, col_reset = st.columns([1, 1, 1])

    with col_play:
        label = "⏸ Pause" if running else "▶ Démarrer"
        btn_type = "secondary" if running else "primary"
        if st.button(label, use_container_width=True, type=btn_type):
            if running:
                st.session_state["simulator_running"] = False
            else:
                st.session_state["simulator_running"] = True
                st.session_state["simulator_last_tick"] = time.time()
            st.rerun()

    with col_jump:
        remaining = duration_min - st.session_state.get("simulator_elapsed", 0.0)
        jump = min(5.0, remaining)
        if st.button(f"⏭ +{jump:.0f} min", use_container_width=True, disabled=running or remaining <= 0):
            st.session_state["simulator_elapsed"] = min(
                st.session_state.get("simulator_elapsed", 0.0) + jump,
                float(duration_min),
            )
            _push_snapshot()
            st.rerun()

    with col_reset:
        if st.button("↺ Réinitialiser", use_container_width=True):
            st.session_state["simulator_running"] = False
            st.session_state["simulator_elapsed"] = 0.0
            st.session_state["simulator_last_tick"] = None
            st.session_state["last_parsed"] = None
            st.session_state["last_raw"] = None
            st.session_state["relay_state"] = {}
            st.rerun()

    # -----------------------------------------------------------------------
    # Ligne 3 : curseur de vitesse
    # -----------------------------------------------------------------------
    speed = st.select_slider(
        "⏩ Vitesse d'écoulement du temps",
        options=_SPEED_OPTIONS,
        value=st.session_state.get("simulator_speed", 1.0),
        format_func=lambda x: (
            f"{x:g}×  ({x * 60:.0f} min simulées / min réelle)" if x < 1
            else f"{x:g}×  ({x:.0f} min simulées / min réelle)"
        ),
        help="1× = temps réel · 60× = 1 min réelle = 1 h de course",
    )
    st.session_state["simulator_speed"] = speed

    # -----------------------------------------------------------------------
    # Avancement du temps (si en cours)
    # -----------------------------------------------------------------------
    if running:
        _apply_tick(speed, duration_min)
        _push_snapshot()

    # -----------------------------------------------------------------------
    # Affichage chrono + progression
    # -----------------------------------------------------------------------
    elapsed = st.session_state.get("simulator_elapsed", 0.0)
    pct = elapsed / duration_min if duration_min else 0.0

    st.markdown("### Temps de course simulé")
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.metric("Chrono", _fmt_time(elapsed))
    with col_t2:
        st.metric("Restant", _fmt_time(max(duration_min - elapsed, 0)))
    with col_t3:
        if elapsed >= duration_min and elapsed > 0:
            status_label = "🏁 Terminée"
        elif running:
            status_label = "🟢 En cours"
        elif elapsed > 0:
            status_label = "⏸ En pause"
        else:
            status_label = "⬜ Arrêté"
        st.metric("État", status_label)

    st.progress(
        min(pct, 1.0),
        text=f"{_fmt_time(elapsed)} / {_fmt_time(duration_min)}  ({pct * 100:.1f} %)",
    )

    st.divider()

    # -----------------------------------------------------------------------
    # Tableau du dernier snapshot injecté
    # -----------------------------------------------------------------------
    last = st.session_state.get("last_parsed")
    if last and last.get("rows"):
        rows = last["rows"]
        st.markdown(
            f"**Dernière injection :** {len(rows)} motos · "
            f"{last.get('fetched_at', '')[:19].replace('T', ' ')} UTC"
        )
        import pandas as pd
        df = pd.DataFrame([
            {
                "Pos": r.get("pos", "—"),
                "N°": r.get("numero", "—"),
                "Cat.": r.get("categorie", "—"),
                "Équipe": r.get("team", "—"),
                "Tours": r.get("laps", "—"),
                "Dernier tour": r.get("l_lap", "—"),
                "Dep. stand": r.get("last_pit", "—"),
                "Nb arrêts": r.get("total_pit", "—"),
            }
            for r in rows
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    elif elapsed == 0.0:
        st.info("Appuyez sur **▶ Démarrer** ou **⏭ +5 min** pour injecter les premières données.")
    else:
        st.info("Aucune donnée générée.")

    # -----------------------------------------------------------------------
    # Aide
    # -----------------------------------------------------------------------
    with st.expander("ℹ️ Comment utiliser le simulateur"):
        st.markdown(
            """
            1. **Choisissez la durée** de la course (2 h à 48 h) — à faire avant de démarrer.
            2. **Réglez la vitesse** (1× à 60×). À 60×, 1 min réelle = 1 h de course simulée.
            3. **Démarrez** — le chrono avance automatiquement et injecte un snapshot à chaque seconde.
            4. **Naviguez** librement vers Dashboard, Pilotes, Stratégie… les données y apparaissent.
            5. **⏭ +5 min** fait un saut instantané sans démarrer le continu.
            6. **Réinitialiser** remet tout à zéro (chrono, données, relais détectés).

            > Astuce : démarrez à 60×, laissez tourner 5 min réelles → vous simulez 5 h de course
            > avec relais complets, stats pilotes et historique remplis.
            """
        )
