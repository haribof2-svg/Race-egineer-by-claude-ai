"""Configuration équipe/live."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["config"])

# Import depuis le package race_engineer
from race_engineer.config import load_config, DEFAULT_CONFIG


def _save_config_safe(config: Dict[str, Any]) -> None:
    """save_config sans dépendance Streamlit."""
    from race_engineer.config import CONFIG_PATH
    try:
        tmp = CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        os.replace(tmp, CONFIG_PATH)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Impossible de sauvegarder : {exc}")


@router.get("/config")
async def get_config():
    return load_config()


@router.put("/config")
async def put_config(body: Dict[str, Any]):
    _save_config_safe(body)
    return {"ok": True}


@router.patch("/config")
async def patch_config(body: Dict[str, Any]):
    cfg = load_config()
    cfg.update(body)
    _save_config_safe(cfg)
    return cfg
