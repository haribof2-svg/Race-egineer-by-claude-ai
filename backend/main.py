"""Race Engineer — Backend FastAPI.

Lance avec :
    cd race_engineer_svelte/backend
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import logging
import sys
import os
import time

# ---------------------------------------------------------------------------
# Ajouter le répertoire race_engineer au path Python
# Structure : race_engineer_svelte/backend/ → ../../race_engineer/
# ---------------------------------------------------------------------------
_RE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "race_engineer")
)
if _RE_PATH not in sys.path:
    sys.path.insert(0, _RE_PATH)

# Patch streamlit avant tout import de race_engineer (save_config l'importe conditionnellement)
from unittest.mock import MagicMock
_st_mock = MagicMock()
sys.modules.setdefault("streamlit", _st_mock)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from race_engineer.database import init_db
from race_engineer.mock_data import generate_mock_payload
from race_engineer.live_timing import parse_live_payload
from race_engineer.relay_tracker import process_snapshot_for_relays
from race_engineer.database import save_snapshot

import state as _state

from routers import snapshot_router, config_router, analytics_router, history_router, simulator_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("race_engineer")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Race Engineer API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(snapshot_router, prefix="/api")
app.include_router(config_router,   prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(history_router,  prefix="/api")
app.include_router(simulator_router, prefix="/api")


# ---------------------------------------------------------------------------
# Tâche de fond : simulateur
# ---------------------------------------------------------------------------
async def _simulator_loop() -> None:
    """Avance le simulateur toutes les secondes et broadcast."""
    from datetime import datetime, timezone
    while True:
        await asyncio.sleep(1)
        sim = _state.simulator
        if not sim["running"]:
            continue

        now = time.time()
        last = sim.get("last_tick") or now
        delta_real = now - last
        delta_sim = delta_real * sim["speed"] / 60.0
        sim["elapsed"] = min(sim["elapsed"] + delta_sim, float(sim["duration"]))
        sim["last_tick"] = now

        # Fin de course
        if sim["elapsed"] >= sim["duration"]:
            sim["running"] = False

        # Générer + broadcaster
        try:
            mock = generate_mock_payload(elapsed_minutes=sim["elapsed"])
            parsed = parse_live_payload(mock)
            fetched_at = datetime.now(timezone.utc).isoformat()
            parsed["fetched_at"] = fetched_at
            _state.current_snapshot = parsed

            save_snapshot(fetched_at=fetched_at, payload=mock)
            # Relay tracker a besoin du session_state de Streamlit — on skip
            # process_snapshot_for_relays(parsed)

            await _state.broadcast(parsed)
        except Exception as exc:
            logger.warning("Erreur simulateur tick : %s", exc)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    logger.info("Base de données initialisée")
    asyncio.create_task(_simulator_loop())
    logger.info("Simulateur démarré en arrière-plan")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
