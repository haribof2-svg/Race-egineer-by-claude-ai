"""Génération de données de test pour développement / démo sans live timing."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, List


COLUMNS_MOCK = [
    "Position", "PositionCategorie", "Numero", "Categorie", "Equipe", "Nom",
    "NbTour", "TpsTour", "MeilleurTour", "TourDepuisStand", "TpsStand",
    "NbStand", "TpsTotalStand",
]

TEAMS_MOCK = [
    ("96", "PRD", "LEGACY COMPETITION", "Pilote 1"),
    ("7",  "EWC", "YART YAMAHA",         "BROC PARKES"),
    ("1",  "EWC", "F.C.C. TSR HONDA",    "GINO REA"),
    ("5",  "EWC", "F1 RACING SUZUKI",    "K. HANIKA"),
    ("33", "SST", "TEAM TATI MOTO",      "L. AMIET"),
    ("44", "SST", "MACO RACING",         "P. CASTILLON"),
    ("65", "PRD", "BMW MOTORRAD WORLD",  "K. POVAH"),
    ("70", "PRD", "TEAM 18 SAPEURS",     "J. BENOIT"),
    ("12", "EXP", "GMT94",                "Y. SOUCASSE"),
]


def generate_mock_payload(elapsed_minutes: float = 30.0) -> Dict[str, Any]:
    """Construit un payload mock simulant un état de course."""
    rng = random.Random(42)
    rows: List[List[Any]] = []

    for pos, (num, cat, team, rider) in enumerate(TEAMS_MOCK, 1):
        base_lap = rng.uniform(95.0, 110.0)
        laps_done = int(elapsed_minutes * 60 / base_lap)
        # Stand toutes les ~20 tours
        total_pit = laps_done // 22
        last_pit = laps_done - total_pit * 22
        last_lap_s = base_lap + rng.uniform(-0.5, 0.7)
        best_lap_s = base_lap - rng.uniform(0.5, 1.5)
        last_pit_t = f"0:{rng.randint(45, 75)}.{rng.randint(0, 999):03d}" if total_pit else "-"
        total_pit_t = f"0:{total_pit * 60 + rng.randint(0, 30)}.000" if total_pit else "-"

        rows.append([
            pos,
            sum(1 for t in TEAMS_MOCK[:pos] if t[1] == cat),
            num,
            cat,
            team,
            rider,
            laps_done,
            _format_time(last_lap_s),
            _format_time(best_lap_s),
            last_pit,
            last_pit_t,
            total_pit,
            total_pit_t,
        ])

    return {
        "Colonnes": COLUMNS_MOCK,
        "Donnees": rows,
        "_mock": True,
        "_elapsed_minutes": elapsed_minutes,
    }


def _format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"{m}:{s:06.3f}"
