"""Utilitaires : parsing temps, formatage, helpers numériques."""

from __future__ import annotations

import re
from typing import Any, Optional


# Regex de temps : couvre "1:35.123", "01:35.123", "35.123", "1:35:25.123"
_TIME_RE = re.compile(
    r"^\s*(?:(\d+):)?(?:(\d+):)?(\d+)(?:[.,](\d+))?\s*$"
)


def parse_lap_time(value: Any) -> Optional[float]:
    """Convertit une chaîne de temps en secondes (float).

    Accepte :
      - "1:35.123"
      - "1:02:35.123"
      - "35.123"
      - "1.35.123" (parfois sur certains flux)
    Retourne None si non parsable, ou si valeur invalide ("-", "Pit In", ...).
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value >= 0 else None

    s = str(value).strip()
    if not s or s in ("-", "—", "--"):
        return None

    # Rejet explicite des marqueurs Pit
    low = s.lower()
    if "pit" in low or "stand" in low or "in" == low or "out" == low:
        return None

    # On nettoie séparateurs européens "1.35.123" → "1:35.123"
    # mais on garde le séparateur décimal (point ou virgule) pour les millisecondes
    s_norm = s.replace(",", ".")
    # Cas "1.35.123" : 2 points dont le dernier est ms → on remplace le premier par ":"
    if s_norm.count(".") == 2:
        first = s_norm.find(".")
        s_norm = s_norm[:first] + ":" + s_norm[first + 1:]

    m = _TIME_RE.match(s_norm)
    if not m:
        return None
    h_or_m, m_or_none, sec_part, ms_part = m.groups()

    if m_or_none is not None:
        # h:m:s
        h = int(h_or_m or 0)
        mm = int(m_or_none)
        ss = int(sec_part)
    elif h_or_m is not None:
        # m:s
        h = 0
        mm = int(h_or_m)
        ss = int(sec_part)
    else:
        # s seul
        h, mm = 0, 0
        ss = int(sec_part)

    ms = 0.0
    if ms_part is not None:
        # Normaliser sur 3 chiffres
        ms_str = ms_part[:3].ljust(3, "0")
        try:
            ms = int(ms_str) / 1000.0
        except ValueError:
            ms = 0.0

    return h * 3600 + mm * 60 + ss + ms


def format_seconds(sec: Optional[float], with_ms: bool = True) -> str:
    """Format inverse : secondes → 'mm:ss.mmm' ou 'h:mm:ss.mmm'."""
    if sec is None:
        return "—"
    try:
        sec = float(sec)
    except (TypeError, ValueError):
        return "—"

    sign = "-" if sec < 0 else ""
    sec = abs(sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    if h:
        return f"{sign}{h}:{m:02d}:{s:0{6 if with_ms else 2}.3f}" if with_ms else f"{sign}{h}:{m:02d}:{int(s):02d}"
    if m:
        return f"{sign}{m}:{s:0{6 if with_ms else 2}.3f}" if with_ms else f"{sign}{m}:{int(s):02d}"
    return f"{sign}{s:.3f}" if with_ms else f"{sign}{int(s)}"


def format_signed(value: Optional[float], unit: str = "s") -> str:
    """+1.234s / -0.567s / —"""
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    sign = "+" if v >= 0 else "−"
    return f"{sign}{abs(v):.3f}{unit}"


def safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    try:
        if b == 0:
            return None
        return a / b
    except Exception:
        return None


def safe_mean(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def safe_min(values):
    vals = [v for v in values if v is not None]
    return min(vals) if vals else None


def safe_max(values):
    vals = [v for v in values if v is not None]
    return max(vals) if vals else None


def safe_median(values):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    n = len(vals)
    mid = n // 2
    if n % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0


def safe_stdev(values):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return None
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return var ** 0.5
