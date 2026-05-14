"""Historique des snapshots."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["history"])

from race_engineer.database import get_snapshots, get_snapshot_payload, count_snapshots, reset_db


@router.get("/history")
async def list_history(limit: int = Query(200, ge=1, le=2000)):
    rows = get_snapshots(limit=limit)
    return [dict(r) for r in rows]


@router.get("/history/count")
async def history_count():
    return {"count": count_snapshots()}


@router.get("/history/{snapshot_id}")
async def get_snapshot(snapshot_id: int):
    payload = get_snapshot_payload(snapshot_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Snapshot non trouvé")
    return payload


@router.delete("/history")
async def clear_history():
    reset_db()
    return {"ok": True, "message": "Historique effacé"}
