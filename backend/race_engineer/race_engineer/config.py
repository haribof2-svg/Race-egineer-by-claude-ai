"""Configuration de l'application — persistée en JSON."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Dict

CONFIG_PATH = os.environ.get(
    "RACE_ENGINEER_CONFIG",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "race_engineer_config.json"),
)


DEFAULT_CONFIG: Dict[str, Any] = {
    # Équipe
    "team_name": "LEGACY COMPETITION",
    "our_bike_number": "96",
    "our_category": "PRD",
    # Live timing
    "live_url": "https://fimewc.live-frclassification.fr/r1.json",
    "auto_refresh": True,
    "refresh_interval": 3,  # secondes
    # Pilotes (3 ou 4)
    "pilots": [
        {"name": "Pilote 1", "alias": [], "color": "#e63946", "order": 1, "active": True},
        {"name": "Pilote 2", "alias": [], "color": "#457b9d", "order": 2, "active": True},
        {"name": "Pilote 3", "alias": [], "color": "#2a9d8f", "order": 3, "active": True},
        {"name": "Pilote 4", "alias": [], "color": "#f4a261", "order": 4, "active": False},
    ],
    # Carburant
    "fuel": {
        "tank_capacity_l": 24.0,
        "consumption_l_per_lap": 3.2,
        "safety_margin_laps": 1,
        "refuel_amount_l": 24.0,
    },
    # Pneus
    "tires": {
        "tracking_enabled": False,
        "wear_per_lap_pct": 1.5,
        "performance_impact_pct_per_pct_wear": 0.05,
    },
    # Concurrents
    "competitors": {
        "default_category": "PRD",
        "favorites": [],          # liste de numéros
        "main_comparison": "",    # numéro
    },
    # Exports
    "export": {
        "auto_export": False,
        "export_path": "exports/",
    },
}


def load_config() -> Dict[str, Any]:
    """Charge la config depuis le fichier JSON, ou retourne le défaut."""
    if not os.path.exists(CONFIG_PATH):
        return deepcopy(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge avec défauts pour gérer les nouvelles clés ajoutées par upgrade
        return _merge_defaults(data, deepcopy(DEFAULT_CONFIG))
    except (OSError, json.JSONDecodeError):
        return deepcopy(DEFAULT_CONFIG)


def save_config(config: Dict[str, Any]) -> None:
    """Persiste la config en JSON (création atomique)."""
    try:
        tmp = CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        os.replace(tmp, CONFIG_PATH)
    except OSError as exc:
        # On ne fait pas planter l'app pour un souci d'écriture disque
        import streamlit as st
        st.warning(f"Impossible de sauvegarder la config : {exc}")


def _merge_defaults(data: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Fusionne récursivement defaults dans data (data prend la priorité)."""
    for key, default_val in defaults.items():
        if key not in data:
            data[key] = default_val
        elif isinstance(default_val, dict) and isinstance(data[key], dict):
            data[key] = _merge_defaults(data[key], default_val)
    return data
