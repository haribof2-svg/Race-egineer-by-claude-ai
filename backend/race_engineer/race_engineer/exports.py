"""Exports : CSV, Excel, JSON."""

from __future__ import annotations

import io
import json
from typing import Any, Dict, List, Optional

import pandas as pd

from race_engineer.database import (
    get_planned_events,
    get_pilot_laps,
    get_relay_events,
    get_snapshots,
    get_snapshot_payload,
)


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------
def build_excel_export(
    parsed: Optional[Dict[str, Any]],
    our_numero: str,
    comparison: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Construit un classeur Excel multi-feuilles. Retourne les octets."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # 1. Live Timing
        if parsed and parsed.get("rows"):
            df = pd.DataFrame(parsed["rows"])
            df.to_excel(writer, sheet_name="Live Timing", index=False)
        else:
            pd.DataFrame([{"info": "Pas de données live"}]).to_excel(
                writer, sheet_name="Live Timing", index=False
            )

        # 2. Notre moto
        our_rows = [r for r in (parsed.get("rows") if parsed else []) if str(r.get("numero")) == str(our_numero)]
        pd.DataFrame(our_rows or [{"info": "Moto non trouvée"}]).to_excel(
            writer, sheet_name="Notre moto", index=False
        )

        # 3. Pilotes (depuis pilot_laps)
        laps_df = pd.DataFrame([dict(l) for l in get_pilot_laps(numero=our_numero)])
        if laps_df.empty:
            laps_df = pd.DataFrame([{"info": "Aucun tour enregistré"}])
        laps_df.to_excel(writer, sheet_name="Pilotes", index=False)

        # 4. Concurrents relais
        relays_df = pd.DataFrame([dict(r) for r in get_relay_events()])
        if relays_df.empty:
            relays_df = pd.DataFrame([{"info": "Aucun relais enregistré"}])
        relays_df.to_excel(writer, sheet_name="Concurrents relais", index=False)

        # 5. Temps d'arrêt
        if not relays_df.empty and "last_pit_seconds" in relays_df.columns:
            pit_df = relays_df[["numero", "relais", "last_pit_time", "last_pit_seconds"]]
        else:
            pit_df = pd.DataFrame([{"info": "Aucun arrêt enregistré"}])
        pit_df.to_excel(writer, sheet_name="Temps d'arrêt", index=False)

        # 6. Comparatif concurrent
        if comparison and comparison.get("rows"):
            comp_df = pd.DataFrame(comparison["rows"])
            comp_df.to_excel(writer, sheet_name="Comparatif concurrent", index=False)
        else:
            pd.DataFrame([{"info": "Aucun comparatif disponible"}]).to_excel(
                writer, sheet_name="Comparatif concurrent", index=False
            )

        # 7. Historique événements
        events_df = pd.DataFrame([dict(e) for e in get_planned_events()])
        if events_df.empty:
            events_df = pd.DataFrame([{"info": "Aucun événement planifié"}])
        events_df.to_excel(writer, sheet_name="Historique événements", index=False)

        # 8. Stratégie (idem évents)
        events_df.to_excel(writer, sheet_name="Stratégie", index=False)

        # 9. Paramètres
        if config:
            flat = _flatten_config(config)
            pd.DataFrame(list(flat.items()), columns=["clé", "valeur"]).to_excel(
                writer, sheet_name="Paramètres", index=False
            )
        else:
            pd.DataFrame([{"info": "Aucune config"}]).to_excel(
                writer, sheet_name="Paramètres", index=False
            )

    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def export_relays_csv() -> bytes:
    rows = [dict(r) for r in get_relay_events()]
    df = pd.DataFrame(rows) if rows else pd.DataFrame([{"info": "Aucun relais"}])
    return df.to_csv(index=False).encode("utf-8")


def export_laps_csv(numero: Optional[str] = None) -> bytes:
    rows = [dict(r) for r in get_pilot_laps(numero=numero)]
    df = pd.DataFrame(rows) if rows else pd.DataFrame([{"info": "Aucun tour"}])
    return df.to_csv(index=False).encode("utf-8")


def export_comparison_csv(comparison: Dict[str, Any]) -> bytes:
    if not comparison or not comparison.get("rows"):
        return pd.DataFrame([{"info": "Aucun comparatif"}]).to_csv(index=False).encode("utf-8")
    return pd.DataFrame(comparison["rows"]).to_csv(index=False).encode("utf-8")


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------
def export_snapshots_json(limit: int = 100) -> bytes:
    snaps = get_snapshots(limit=limit)
    out = []
    for s in snaps:
        payload = get_snapshot_payload(s["id"])
        out.append({
            "id": s["id"],
            "fetched_at": s["fetched_at"],
            "event_time_utc": s["event_time_utc"],
            "payload": payload,
        })
    return json.dumps(out, ensure_ascii=False, indent=2).encode("utf-8")


def export_planned_events_json() -> bytes:
    rows = [dict(e) for e in get_planned_events()]
    return json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")


def export_config_json(config: Dict[str, Any]) -> bytes:
    return json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _flatten_config(cfg: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in cfg.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten_config(v, prefix=key + "."))
        elif isinstance(v, list):
            out[key] = json.dumps(v, ensure_ascii=False)
        else:
            out[key] = v
    return out
