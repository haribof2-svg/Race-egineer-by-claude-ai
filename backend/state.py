"""État global partagé entre les routers FastAPI."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Snapshot courant (données de course)
# ---------------------------------------------------------------------------
current_snapshot: Optional[Dict[str, Any]] = None

# ---------------------------------------------------------------------------
# Simulateur
# ---------------------------------------------------------------------------
simulator: Dict[str, Any] = {
    "running": False,
    "elapsed": 0.0,     # minutes simulées
    "speed": 1.0,       # multiplicateur
    "last_tick": None,  # time.time() du dernier tick
    "duration": 1440,   # durée totale en minutes
}

# ---------------------------------------------------------------------------
# File SSE : un asyncio.Queue par client connecté
# ---------------------------------------------------------------------------
sse_clients: List[asyncio.Queue] = []


async def broadcast(data: Dict[str, Any]) -> None:
    """Envoie un snapshot à tous les clients SSE connectés."""
    for q in list(sse_clients):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass
