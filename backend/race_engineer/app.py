"""
Race Engineer — Endurance Moto
==============================
Application Streamlit de suivi live, d'analyse stratégique et de prédiction
pour les courses d'endurance moto.

Equipe par défaut : LEGACY COMPETITION — Moto 96 — Catégorie PRD
"""

from __future__ import annotations

import streamlit as st

from race_engineer.config import load_config, save_config, DEFAULT_CONFIG
from race_engineer.database import init_db
from race_engineer.live_timing import fetch_live_data, parse_live_payload
from race_engineer.session_state import ensure_session_state
from race_engineer.ui import (
    page_dashboard,
    page_live_timing,
    page_our_bike,
    page_pilots,
    page_competitors,
    page_comparison,
    page_strategy,
    page_history,
    page_settings,
    page_simulator,
)

# Streamlit-autorefresh est optionnel : on dégrade proprement s'il est absent
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception:
    HAS_AUTOREFRESH = False


# ---------------------------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Race Engineer — Endurance Moto",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS perso pour mettre en évidence la moto 96 et soigner le rendu
st.markdown(
    """
    <style>
    .our-bike-row { background-color: rgba(255, 215, 0, 0.18) !important; }
    .pit-in { color: #d94545; font-weight: 600; }
    .pit-out { color: #2bb673; font-weight: 600; }
    .gain { color: #2bb673; font-weight: 600; }
    .loss { color: #d94545; font-weight: 600; }
    .neutral { color: #888; }
    .metric-card {
        background: rgba(255,255,255,0.04);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffd700;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------
init_db()
ensure_session_state()


# ---------------------------------------------------------------------------
# Sidebar : navigation + config rapide
# ---------------------------------------------------------------------------
config = load_config()

with st.sidebar:
    st.title("🏍️ Race Engineer")
    st.caption(
        f"**{config.get('team_name', 'LEGACY COMPETITION')}**  \n"
        f"Moto n°{config.get('our_bike_number', '96')} — "
        f"Catégorie {config.get('our_category', 'PRD')}"
    )
    st.divider()

    PAGES = {
        "📊 Dashboard": page_dashboard,
        "📡 Live Timing": page_live_timing,
        "🏍️ Notre moto": page_our_bike,
        "👤 Pilotes": page_pilots,
        "🏁 Concurrents": page_competitors,
        "⚖️ Comparatif": page_comparison,
        "🧠 Stratégie": page_strategy,
        "🕒 Historique / Replay": page_history,
        "⚙️ Paramètres": page_settings,
        "🎮 Simulateur": page_simulator,
    }

    page_label = st.radio(
        "Navigation",
        list(PAGES.keys()),
        index=st.session_state.get("nav_index", 0),
        key="nav_radio",
    )
    st.session_state["nav_index"] = list(PAGES.keys()).index(page_label)

    st.divider()

    # Auto-refresh global
    auto_refresh = st.toggle(
        "🔄 Auto-refresh",
        value=config.get("auto_refresh", True),
        help="Active le rafraîchissement automatique des données live.",
    )
    refresh_interval = st.slider(
        "Intervalle (s)",
        min_value=1,
        max_value=30,
        value=int(config.get("refresh_interval", 3)),
        step=1,
    )

    if (
        auto_refresh != config.get("auto_refresh")
        or refresh_interval != config.get("refresh_interval")
    ):
        config["auto_refresh"] = auto_refresh
        config["refresh_interval"] = refresh_interval
        save_config(config)


# ---------------------------------------------------------------------------
# Auto-refresh (uniquement sur pages live)
# ---------------------------------------------------------------------------
LIVE_PAGES = {
    "📊 Dashboard",
    "📡 Live Timing",
    "🏍️ Notre moto",
    "👤 Pilotes",
    "🏁 Concurrents",
    "⚖️ Comparatif",
    "🧠 Stratégie",
    "🎮 Simulateur",
}

if auto_refresh and page_label in LIVE_PAGES and HAS_AUTOREFRESH:
    st_autorefresh(interval=refresh_interval * 1000, key="global_refresh")
elif auto_refresh and page_label in LIVE_PAGES and not HAS_AUTOREFRESH:
    st.sidebar.warning(
        "⚠️ `streamlit-autorefresh` non installé — refresh manuel uniquement."
    )


# ---------------------------------------------------------------------------
# Fetch des données live (centralisé, mis en cache courte durée)
# ---------------------------------------------------------------------------
def get_live_snapshot():
    """Récupère un snapshot live, parse, persiste et stocke en session_state."""
    # Si le simulateur a injecté des données, on les utilise directement
    # et on ne tente pas le fetch live (qui écraserait les données simulées).
    if st.session_state.get("simulator_elapsed", 0.0) > 0:
        last = st.session_state.get("last_parsed")
        if last:
            st.session_state["last_fetch_error"] = None
            return last, None

    url = config.get("live_url", DEFAULT_CONFIG["live_url"])
    raw, error = fetch_live_data(url)

    if error:
        st.session_state["last_fetch_error"] = error
        # On garde la dernière donnée connue plutôt que vider l'écran
        return st.session_state.get("last_parsed"), error

    st.session_state["last_fetch_error"] = None
    parsed = parse_live_payload(raw)
    st.session_state["last_parsed"] = parsed
    st.session_state["last_raw"] = raw
    return parsed, None


parsed, fetch_error = get_live_snapshot()

if fetch_error and not parsed:
    st.warning(f"⚠️ Live timing indisponible : {fetch_error}")
    st.info(
        "L'application reste utilisable : historique, paramètres et replay "
        "fonctionnent sans le flux live."
    )


# ---------------------------------------------------------------------------
# Rendu de la page sélectionnée
# ---------------------------------------------------------------------------
page_func = PAGES[page_label]
page_func(parsed=parsed, config=config)
