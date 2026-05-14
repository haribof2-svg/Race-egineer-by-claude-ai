"""Contrôle du simulateur."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body

router = APIRouter(prefix="/simulator", tags=["simulator"])

import state as _state

_DURATIONS = {
    "2h": 120, "4h": 240, "6h": 360, "8h": 480,
    "12h": 720, "24h": 1440, "48h": 2880,
}


@router.get("/state")
async def get_state():
    return dict(_state.simulator)


@router.post("/start")
async def start(speed: float = Body(1.0), duration: int = Body(1440)):
    sim = _state.simulator
    sim["speed"] = max(0.5, min(speed, 120.0))
    sim["duration"] = duration
    sim["last_tick"] = time.time()
    sim["running"] = True
    return dict(sim)


@router.post("/pause")
async def pause():
    _state.simulator["running"] = False
    return dict(_state.simulator)


@router.post("/reset")
async def reset():
    sim = _state.simulator
    sim["running"] = False
    sim["elapsed"] = 0.0
    sim["last_tick"] = None
    _state.current_snapshot = None
    return dict(sim)


@router.post("/jump")
async def jump(minutes: float = Body(5.0)):
    sim = _state.simulator
    sim["elapsed"] = min(sim["elapsed"] + minutes, float(sim["duration"]))
    # Générer un snapshot immédiat
    from race_engineer.mock_data import generate_mock_payload
    from race_engineer.live_timing import parse_live_payload
    from race_engineer.database import save_snapshot
    from datetime import datetime, timezone

    mock = generate_mock_payload(elapsed_minutes=sim["elapsed"])
    parsed = parse_live_payload(mock)
    fetched_at = datetime.now(timezone.utc).isoformat()
    parsed["fetched_at"] = fetched_at
    _state.current_snapshot = parsed
    save_snapshot(fetched_at=fetched_at, payload=mock)
    await _state.broadcast(parsed)
    return {"elapsed": sim["elapsed"], "snapshot_rows": len(parsed.get("rows", []))}


@router.patch("/speed")
async def set_speed(speed: float = Body(..., embed=True)):
    _state.simulator["speed"] = max(0.5, min(speed, 120.0))
    return {"speed": _state.simulator["speed"]}
