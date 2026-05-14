"""Relais, tours pilotes, analytique."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query

router = APIRouter(tags=["analytics"])

from race_engineer.database import get_relay_events, get_pilot_laps
from race_engineer.analytics import compute_pilot_stats


@router.get("/relays")
async def get_relays(numero: Optional[str] = Query(None)):
    if numero:
        return [dict(r) for r in get_relay_events(numero)]
    # Tous les numéros présents dans la DB
    from race_engineer.database import get_conn
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT numero FROM relay_events ORDER BY numero"
        ).fetchall()
    result = {}
    for row in rows:
        num = row["numero"]
        result[num] = [dict(r) for r in get_relay_events(num)]
    return result


@router.get("/pilot-laps")
async def get_pilot_laps_route(numero: str = Query(...)):
    return [dict(r) for r in get_pilot_laps(numero)]


@router.get("/analytics/{numero}")
async def get_analytics(numero: str, pilot: str = Query(...)):
    from race_engineer.config import load_config
    cfg = load_config()
    pilot_cfg = next(
        (p for p in cfg.get("pilots", []) if p["name"] == pilot),
        None,
    )
    aliases = pilot_cfg["alias"] if pilot_cfg else []
    return compute_pilot_stats(numero=numero, pilot_name=pilot, aliases=aliases)


@router.get("/bike-summary/{numero}")
async def get_bike_summary(numero: str):
    from race_engineer.relay_tracker import get_relay_summary
    return get_relay_summary(numero)
