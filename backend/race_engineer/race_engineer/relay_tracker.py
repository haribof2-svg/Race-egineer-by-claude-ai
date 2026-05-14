"""Détection et persistance des relais.

Logique métier centrale :
- ``last_pit`` augmente pendant un relais
- Quand ``last_pit`` retombe à 0 OU que ``total_pit`` augmente → un relais s'est terminé
- Le nombre de tours du relais = dernière valeur de ``last_pit`` connue avant l'événement
- Le temps d'arrêt = ``last_pit_time``

Pour éviter les doublons (le rafraîchissement est fréquent), on stocke un état
en mémoire par moto et on ne déclenche qu'aux transitions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st

from race_engineer.database import (
    upsert_pilot_lap,
    upsert_relay_event,
)
from race_engineer.utils import parse_lap_time


# ---------------------------------------------------------------------------
# État mémoire par moto
# ---------------------------------------------------------------------------
def _state() -> Dict[str, Any]:
    """État partagé en session_state."""
    if "relay_state" not in st.session_state:
        st.session_state["relay_state"] = {}
    return st.session_state["relay_state"]


def _get_bike_state(numero: str) -> Dict[str, Any]:
    state = _state()
    if numero not in state:
        state[numero] = {
            "prev_last_pit": None,    # dernière valeur de last_pit observée
            "prev_total_pit": None,   # dernière valeur de total_pit observée
            "prev_laps": None,        # dernier total de tours
            "prev_l_lap": None,       # dernier temps tour observé
            "current_relay": 1,       # numéro du relais en cours (1-indexé)
            "max_last_pit_in_relay": 0,
            "last_pilot": None,
        }
    return state[numero]


# ---------------------------------------------------------------------------
# Mise à jour à partir d'un snapshot
# ---------------------------------------------------------------------------
def process_snapshot_for_relays(parsed: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Traite un snapshot live et persiste les événements détectés.

    Retourne un résumé : {detected_relays: [...], new_laps: [...], errors: [...]}.
    """
    summary: Dict[str, Any] = {
        "detected_relays": [],
        "new_laps": [],
        "errors": [],
    }
    if not parsed or not parsed.get("rows"):
        return summary

    timestamp = parsed.get("fetched_at") or datetime.now(timezone.utc).isoformat()

    for row in parsed["rows"]:
        try:
            _process_row(row, timestamp, summary)
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append(f"Moto {row.get('numero', '?')}: {exc}")

    return summary


def _process_row(row: Dict[str, Any], timestamp: str, summary: Dict[str, Any]) -> None:
    numero = str(row.get("numero", "")).strip()
    if not numero:
        return

    state = _get_bike_state(numero)

    last_pit = row.get("last_pit")
    total_pit = row.get("total_pit")
    laps = row.get("laps")
    pilote = (row.get("rider") or "").strip() or None
    team = (row.get("team") or "").strip() or None
    categorie = (row.get("categorie") or "").strip() or None
    l_lap = row.get("l_lap")
    last_pit_time = row.get("last_pit_time")
    pit_state = row.get("pit_state")

    if pilote:
        state["last_pilot"] = pilote

    # --- Détection d'un nouveau relais terminé ------------------------------
    relay_completed = False
    tours_relais = 0
    last_pit_seconds_persisted = parse_lap_time(last_pit_time)

    prev_last_pit = state.get("prev_last_pit")
    prev_total_pit = state.get("prev_total_pit")

    # Cas 1 : total_pit a augmenté
    if (
        prev_total_pit is not None
        and isinstance(total_pit, int)
        and total_pit > prev_total_pit
    ):
        tours_relais = state.get("max_last_pit_in_relay", 0)
        if tours_relais <= 0 and isinstance(prev_last_pit, int):
            tours_relais = prev_last_pit
        relay_completed = True

    # Cas 2 : last_pit est retombé à 0 alors qu'il était > 0 (signal de pit out)
    elif (
        isinstance(prev_last_pit, int)
        and prev_last_pit > 0
        and isinstance(last_pit, int)
        and last_pit == 0
        and not relay_completed
    ):
        tours_relais = state.get("max_last_pit_in_relay", prev_last_pit)
        relay_completed = True

    if relay_completed and tours_relais > 0:
        relay_num = state["current_relay"]
        upsert_relay_event(
            timestamp=timestamp,
            numero=numero,
            relais=relay_num,
            tours_relais=tours_relais,
            last_pit_time=str(last_pit_time) if last_pit_time else None,
            last_pit_seconds=last_pit_seconds_persisted,
            categorie=categorie,
            team=team,
            pilote=state.get("last_pilot") or pilote,
            tour_total=laps if isinstance(laps, int) else None,
            total_pit=total_pit if isinstance(total_pit, int) else None,
        )
        summary["detected_relays"].append({
            "numero": numero,
            "relais": relay_num,
            "tours": tours_relais,
            "pit_time": last_pit_time,
        })
        state["current_relay"] = relay_num + 1
        state["max_last_pit_in_relay"] = 0

    # --- Suivi du tour courant ---------------------------------------------
    # On insère un tour pilote si "laps" a augmenté
    prev_laps = state.get("prev_laps")
    if (
        isinstance(laps, int)
        and laps > 0
        and (prev_laps is None or laps > prev_laps)
    ):
        lap_sec = parse_lap_time(l_lap)
        upsert_pilot_lap(
            timestamp=timestamp,
            numero=numero,
            tour_total=laps,
            lap_time=str(l_lap) if l_lap else None,
            lap_seconds=lap_sec,
            pilote=state.get("last_pilot") or pilote,
            relay_laps=last_pit if isinstance(last_pit, int) else None,
            relay_number=state["current_relay"],
        )
        if lap_sec is not None:
            summary["new_laps"].append({
                "numero": numero,
                "tour": laps,
                "time_s": lap_sec,
            })

    # --- Mise à jour de l'état mémoire -------------------------------------
    if isinstance(last_pit, int):
        if last_pit > state.get("max_last_pit_in_relay", 0):
            state["max_last_pit_in_relay"] = last_pit
        state["prev_last_pit"] = last_pit
    if isinstance(total_pit, int):
        state["prev_total_pit"] = total_pit
    if isinstance(laps, int):
        state["prev_laps"] = laps
    state["prev_l_lap"] = l_lap


# ---------------------------------------------------------------------------
# Lecture / agrégation
# ---------------------------------------------------------------------------
def get_relay_summary(numero: str) -> Dict[str, Any]:
    """Renvoie un résumé des relais persistés pour une moto."""
    from race_engineer.database import get_relay_events

    rows = [dict(r) for r in get_relay_events(numero)]
    if not rows:
        return {
            "count": 0,
            "relays": [],
            "total_laps": 0,
            "avg_laps_per_relay": None,
            "longest_relay": None,
            "shortest_relay": None,
            "avg_pit_seconds": None,
        }

    laps_list = [r["tours_relais"] for r in rows if r["tours_relais"]]
    pits = [r["last_pit_seconds"] for r in rows if r["last_pit_seconds"]]

    return {
        "count": len(rows),
        "relays": rows,
        "total_laps": sum(laps_list),
        "avg_laps_per_relay": sum(laps_list) / len(laps_list) if laps_list else None,
        "longest_relay": max(laps_list) if laps_list else None,
        "shortest_relay": min(laps_list) if laps_list else None,
        "avg_pit_seconds": sum(pits) / len(pits) if pits else None,
    }
