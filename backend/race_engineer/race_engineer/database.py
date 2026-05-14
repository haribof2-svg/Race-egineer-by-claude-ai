"""Stockage local SQLite pour snapshots, relais, tours, événements."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Tuple

DB_PATH = os.environ.get(
    "RACE_ENGINEER_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "race_engineer_history.sqlite"),
)

# SQLite peut se verrouiller en multithread Streamlit — on sérialise les écritures.
_DB_LOCK = threading.Lock()


@contextmanager
def get_conn():
    """Context manager pour obtenir une connexion SQLite robuste."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # WAL pour limiter les verrouillages
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
    except sqlite3.Error:
        pass
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Crée les tables si elles n'existent pas."""
    with _DB_LOCK, get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at      TEXT NOT NULL,
                event_time_utc  TEXT,
                payload         TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_snapshots_fetched_at
                ON snapshots(fetched_at);

            CREATE TABLE IF NOT EXISTS relay_events (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT NOT NULL,
                numero          TEXT NOT NULL,
                categorie       TEXT,
                team            TEXT,
                pilote          TEXT,
                relais          INTEGER,
                tours_relais    INTEGER,
                last_pit_time   TEXT,
                last_pit_seconds REAL,
                tour_total      INTEGER,
                total_pit       INTEGER,
                UNIQUE(numero, relais)
            );

            CREATE INDEX IF NOT EXISTS idx_relay_numero
                ON relay_events(numero);

            CREATE TABLE IF NOT EXISTS pilot_laps (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT NOT NULL,
                numero          TEXT NOT NULL,
                pilote          TEXT,
                tour_total      INTEGER NOT NULL,
                lap_time        TEXT,
                lap_seconds     REAL,
                relay_laps      INTEGER,
                relay_number    INTEGER,
                UNIQUE(numero, tour_total)
            );

            CREATE INDEX IF NOT EXISTS idx_laps_numero_tour
                ON pilot_laps(numero, tour_total);

            CREATE TABLE IF NOT EXISTS planned_events (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                lap             INTEGER,
                type            TEXT NOT NULL,
                description     TEXT,
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_config (
                key             TEXT PRIMARY KEY,
                value           TEXT
            );
            """
        )


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------
def save_snapshot(fetched_at: str, payload: Dict[str, Any], event_time_utc: Optional[str] = None) -> int:
    """Insère un snapshot brut et retourne l'id."""
    with _DB_LOCK, get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO snapshots (fetched_at, event_time_utc, payload) VALUES (?, ?, ?)",
            (fetched_at, event_time_utc, json.dumps(payload, ensure_ascii=False)),
        )
        return cur.lastrowid


def get_snapshots(limit: int = 1000) -> List[sqlite3.Row]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, fetched_at, event_time_utc FROM snapshots ORDER BY fetched_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows


def get_snapshot_payload(snapshot_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT payload FROM snapshots WHERE id = ?",
            (snapshot_id,),
        ).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["payload"])
    except json.JSONDecodeError:
        return None


def count_snapshots() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM snapshots").fetchone()
    return row["n"] if row else 0


# ---------------------------------------------------------------------------
# Relay events
# ---------------------------------------------------------------------------
def upsert_relay_event(
    timestamp: str,
    numero: str,
    relais: int,
    tours_relais: int,
    last_pit_time: Optional[str] = None,
    last_pit_seconds: Optional[float] = None,
    categorie: Optional[str] = None,
    team: Optional[str] = None,
    pilote: Optional[str] = None,
    tour_total: Optional[int] = None,
    total_pit: Optional[int] = None,
) -> None:
    """Insère ou met à jour un événement de relais (idempotent sur numero/relais)."""
    with _DB_LOCK, get_conn() as conn:
        conn.execute(
            """
            INSERT INTO relay_events
                (timestamp, numero, categorie, team, pilote, relais, tours_relais,
                 last_pit_time, last_pit_seconds, tour_total, total_pit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(numero, relais) DO UPDATE SET
                tours_relais = excluded.tours_relais,
                last_pit_time = COALESCE(excluded.last_pit_time, relay_events.last_pit_time),
                last_pit_seconds = COALESCE(excluded.last_pit_seconds, relay_events.last_pit_seconds),
                pilote = COALESCE(excluded.pilote, relay_events.pilote),
                tour_total = COALESCE(excluded.tour_total, relay_events.tour_total),
                total_pit = COALESCE(excluded.total_pit, relay_events.total_pit)
            """,
            (timestamp, numero, categorie, team, pilote, relais, tours_relais,
             last_pit_time, last_pit_seconds, tour_total, total_pit),
        )


def get_relay_events(numero: Optional[str] = None) -> List[sqlite3.Row]:
    with get_conn() as conn:
        if numero is None:
            rows = conn.execute(
                "SELECT * FROM relay_events ORDER BY numero, relais"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM relay_events WHERE numero = ? ORDER BY relais",
                (numero,),
            ).fetchall()
    return rows


# ---------------------------------------------------------------------------
# Pilot laps
# ---------------------------------------------------------------------------
def upsert_pilot_lap(
    timestamp: str,
    numero: str,
    tour_total: int,
    lap_time: Optional[str] = None,
    lap_seconds: Optional[float] = None,
    pilote: Optional[str] = None,
    relay_laps: Optional[int] = None,
    relay_number: Optional[int] = None,
) -> None:
    with _DB_LOCK, get_conn() as conn:
        conn.execute(
            """
            INSERT INTO pilot_laps
                (timestamp, numero, pilote, tour_total, lap_time, lap_seconds, relay_laps, relay_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(numero, tour_total) DO UPDATE SET
                lap_time = COALESCE(excluded.lap_time, pilot_laps.lap_time),
                lap_seconds = COALESCE(excluded.lap_seconds, pilot_laps.lap_seconds),
                pilote = COALESCE(excluded.pilote, pilot_laps.pilote),
                relay_laps = COALESCE(excluded.relay_laps, pilot_laps.relay_laps),
                relay_number = COALESCE(excluded.relay_number, pilot_laps.relay_number)
            """,
            (timestamp, numero, pilote, tour_total, lap_time, lap_seconds, relay_laps, relay_number),
        )


def get_pilot_laps(numero: Optional[str] = None, pilote: Optional[str] = None) -> List[sqlite3.Row]:
    query = "SELECT * FROM pilot_laps WHERE 1=1"
    params: List[Any] = []
    if numero is not None:
        query += " AND numero = ?"
        params.append(numero)
    if pilote is not None:
        query += " AND pilote = ?"
        params.append(pilote)
    query += " ORDER BY tour_total"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return rows


# ---------------------------------------------------------------------------
# Planned events
# ---------------------------------------------------------------------------
def add_planned_event(lap: Optional[int], event_type: str, description: str, created_at: str) -> int:
    with _DB_LOCK, get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO planned_events (lap, type, description, created_at) VALUES (?, ?, ?, ?)",
            (lap, event_type, description, created_at),
        )
        return cur.lastrowid


def get_planned_events() -> List[sqlite3.Row]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM planned_events ORDER BY lap NULLS LAST, id"
        ).fetchall()
    return rows


def delete_planned_event(event_id: int) -> None:
    with _DB_LOCK, get_conn() as conn:
        conn.execute("DELETE FROM planned_events WHERE id = ?", (event_id,))


def update_planned_event(event_id: int, lap: Optional[int], event_type: str, description: str) -> None:
    with _DB_LOCK, get_conn() as conn:
        conn.execute(
            "UPDATE planned_events SET lap = ?, type = ?, description = ? WHERE id = ?",
            (lap, event_type, description, event_id),
        )


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------
def reset_db() -> None:
    """Vide complètement les tables (sauf app_config)."""
    with _DB_LOCK, get_conn() as conn:
        conn.executescript(
            """
            DELETE FROM snapshots;
            DELETE FROM relay_events;
            DELETE FROM pilot_laps;
            DELETE FROM planned_events;
            """
        )


def db_size_bytes() -> int:
    try:
        return os.path.getsize(DB_PATH)
    except OSError:
        return 0
