"""Récupération et parsing du flux de live timing JSON."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

# ---------------------------------------------------------------------------
# Mapping nom-de-colonne → nom canonique
# Le flux peut donner des noms FR ("Position") ou EN ("Pos."). On normalise.
# ---------------------------------------------------------------------------
COLUMN_ALIASES: Dict[str, str] = {
    # Position
    "position": "position",
    "pos.": "position",
    "pos": "position",
    # Position catégorie
    "positioncategorie": "position_cat",
    "cat.p": "position_cat",
    "catp": "position_cat",
    # Numéro
    "numero": "numero",
    "no.": "numero",
    "no": "numero",
    # Catégorie
    "categorie": "categorie",
    "cat": "categorie",
    # Équipe
    "equipe": "team",
    "team": "team",
    # Pilote
    "nom": "rider",
    "rider": "rider",
    # Nombre de tours
    "nbtour": "laps",
    "laps": "laps",
    # Temps tour
    "tpstour": "l_lap",
    "l. lap": "l_lap",
    "l.lap": "l_lap",
    # Meilleur tour
    "meilleurtour": "best_lap",
    "best lap": "best_lap",
    # Tours depuis stand
    "tourdepuisstand": "last_pit",
    "last pit": "last_pit",
    # Temps dernier stand
    "tpsstand": "last_pit_time",
    "last pit time": "last_pit_time",
    # Total stands
    "nbstand": "total_pit",
    "total pit": "total_pit",
    # Temps total stands
    "tpstotalstand": "total_pit_time",
    "total pit time": "total_pit_time",
    # Gap (souvent dans le flux)
    "ecart": "gap",
    "gap": "gap",
    "interval": "interval",
    "int.": "interval",
    "tour": "tour",
}

# Balises de marquage du flux à nettoyer
TAG_PATTERNS = {
    "pit_in": re.compile(r"\{entree-stand\}", re.IGNORECASE),
    "pit_out": re.compile(r"\{sortie-stand\}", re.IGNORECASE),
    "best_time": re.compile(r"\{meilleur-temps\}", re.IGNORECASE),
    "any_tag": re.compile(r"\{[^}]+\}"),
}


# ---------------------------------------------------------------------------
# Fetch HTTP
# ---------------------------------------------------------------------------
def fetch_live_data(url: str, timeout: float = 8.0) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Télécharge et parse le JSON du flux live.

    Retourne (payload, error_msg). Le BOM UTF-8 est géré.
    """
    if not url:
        return None, "Aucune URL configurée"

    full_url = _append_anti_cache(url)
    headers = {
        "User-Agent": "RaceEngineer/1.0 (Python; Streamlit)",
        "Accept": "application/json, text/plain, */*",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    try:
        resp = requests.get(full_url, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout:
        return None, f"Timeout après {timeout}s"
    except requests.exceptions.ConnectionError as exc:
        return None, f"Erreur de connexion : {exc.__class__.__name__}"
    except requests.exceptions.RequestException as exc:
        return None, f"Erreur réseau : {exc}"

    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}"

    # Décodage utf-8-sig pour supporter le BOM
    try:
        text = resp.content.decode("utf-8-sig", errors="replace")
    except Exception:
        text = resp.text

    if not text.strip():
        return None, "Réponse vide"

    try:
        # json.loads — JAMAIS eval(). Le flux peut contenir des single quotes/keys non quotées :
        # on tente d'abord en strict, puis on tente une réparation légère.
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = _try_repair_json(text)
        if payload is None:
            return None, "JSON invalide / non parsable"

    return payload, None


def _append_anti_cache(url: str) -> str:
    """Ajoute ?t=<ms> ou &t=<ms> à l'URL."""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}t={int(time.time() * 1000)}"


def _try_repair_json(text: str) -> Optional[Dict[str, Any]]:
    """Réparation minimale : single quotes → double quotes (jamais eval !)."""
    # Cette réparation reste prudente et ne traite que les cas les plus simples.
    candidate = text.strip()
    # On enlève d'éventuels appels du type "varname = {...};"
    m = re.search(r"\{.*\}", candidate, re.DOTALL)
    if not m:
        return None
    snippet = m.group(0)
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        pass
    # Substituer simple-quotes → double-quotes hors guillemets imbriqués (heuristique)
    try:
        repaired = snippet.replace("'", '"')
        return json.loads(repaired)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def parse_live_payload(payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Parse un payload live timing en une structure exploitable.

    Retourne dict :
      - fetched_at: str ISO
      - columns_raw: list[str]
      - columns: list[str]   # noms canoniques
      - rows: list[dict]     # une ligne par moto, clés canoniques
      - meta: dict           # autres clés du payload (race name, etc.)
    """
    if not payload or not isinstance(payload, dict):
        return None

    now = datetime.now(timezone.utc).isoformat()

    columns_raw = _extract_columns(payload)
    rows_raw = _extract_rows(payload)

    if not columns_raw or rows_raw is None:
        return {
            "fetched_at": now,
            "columns_raw": columns_raw or [],
            "columns": [],
            "rows": [],
            "meta": {k: v for k, v in payload.items() if k not in ("Colonnes", "Donnees")},
        }

    canon = [_canonical(c) for c in columns_raw]

    rows_parsed: List[Dict[str, Any]] = []
    for row in rows_raw:
        if not isinstance(row, list):
            # Certains flux fournissent un dict — on le traduit.
            if isinstance(row, dict):
                rec = {_canonical(k): v for k, v in row.items()}
            else:
                continue
        else:
            rec = {}
            for i, val in enumerate(row):
                if i < len(canon):
                    rec[canon[i]] = val
        cleaned = _clean_row(rec)
        if cleaned.get("numero"):
            rows_parsed.append(cleaned)

    meta = {k: v for k, v in payload.items() if k not in ("Colonnes", "Donnees", "columns", "data", "rows")}

    return {
        "fetched_at": now,
        "columns_raw": columns_raw,
        "columns": canon,
        "rows": rows_parsed,
        "meta": meta,
    }


def _extract_columns(payload: Dict[str, Any]) -> List[str]:
    for key in ("Colonnes", "colonnes", "Columns", "columns"):
        cols = payload.get(key)
        if isinstance(cols, list):
            return [str(c) for c in cols]
    return []


def _extract_rows(payload: Dict[str, Any]) -> Optional[List[Any]]:
    for key in ("Donnees", "donnees", "Data", "data", "Rows", "rows"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return rows
    return None


def _canonical(name: str) -> str:
    key = re.sub(r"\s+", " ", str(name).strip()).lower()
    if key in COLUMN_ALIASES:
        return COLUMN_ALIASES[key]
    # tentatives sans ponctuation
    key2 = key.replace(" ", "").replace(".", "")
    return COLUMN_ALIASES.get(key2, key.replace(" ", "_").replace(".", ""))


def _clean_row(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Nettoie les balises et homogénéise les types d'une ligne."""
    out: Dict[str, Any] = {}
    pit_state: Optional[str] = None

    for key, val in rec.items():
        if isinstance(val, str):
            cleaned = val
            # Détection Pit In / Pit Out
            if TAG_PATTERNS["pit_in"].search(cleaned) or "pit in" in cleaned.lower():
                pit_state = "PIT_IN"
            if TAG_PATTERNS["pit_out"].search(cleaned) or "pit out" in cleaned.lower():
                pit_state = "PIT_OUT"
            cleaned = TAG_PATTERNS["any_tag"].sub("", cleaned).strip()
            out[key] = cleaned
        else:
            out[key] = val

    if pit_state:
        out["pit_state"] = pit_state

    # Coercions numériques tolérantes
    for k in ("position", "position_cat", "laps", "last_pit", "total_pit"):
        if k in out:
            out[k] = _to_int(out[k])

    out["numero"] = str(out.get("numero", "")).strip()
    return out


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, (int,)):
        return val
    if isinstance(val, float):
        return int(val)
    try:
        s = str(val).strip()
        if s in ("", "-", "—"):
            return None
        return int(float(s))
    except (TypeError, ValueError):
        return None
