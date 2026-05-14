"""Snapshot courant + flux SSE."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

import state as _state

router = APIRouter(tags=["snapshot"])


@router.get("/snapshot")
async def get_snapshot():
    if _state.current_snapshot is None:
        return {"rows": [], "fetched_at": None, "meta": {}}
    return _state.current_snapshot


@router.get("/stream")
async def stream(request: Request):
    """Server-Sent Events : push un snapshot dès qu'il est disponible."""
    async def _generator() -> AsyncGenerator[str, None]:
        q: asyncio.Queue = asyncio.Queue(maxsize=10)
        _state.sse_clients.append(q)
        try:
            # Envoyer immédiatement le snapshot courant s'il existe
            if _state.current_snapshot:
                yield f"data: {json.dumps(_state.current_snapshot)}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=20)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            try:
                _state.sse_clients.remove(q)
            except ValueError:
                pass

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
