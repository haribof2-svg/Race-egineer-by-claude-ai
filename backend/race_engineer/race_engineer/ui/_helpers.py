"""Helpers UI partagés."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import streamlit as st

from race_engineer.utils import format_seconds, format_signed


def find_our_bike(parsed: Optional[Dict[str, Any]], our_numero: str) -> Optional[Dict[str, Any]]:
    """Retourne la ligne de notre moto, ou None."""
    if not parsed or not parsed.get("rows"):
        return None
    for row in parsed["rows"]:
        if str(row.get("numero")) == str(our_numero):
            return row
    return None


def category_filter_widget(default_category: str, all_categories: Iterable[str], key: str = "cat_filter") -> str:
    """Affiche un select-box catégorie standard."""
    options = ["ALL"] + sorted({c for c in all_categories if c})
    if default_category not in options:
        options.append(default_category)
    idx = options.index(default_category) if default_category in options else 0
    return st.selectbox("Catégorie", options, index=idx, key=key)


def collect_categories(parsed: Optional[Dict[str, Any]]) -> List[str]:
    if not parsed or not parsed.get("rows"):
        return []
    return sorted({str(r.get("categorie", "")).strip() for r in parsed["rows"] if r.get("categorie")})


def filter_rows_by_category(rows: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    if not rows or category == "ALL":
        return rows
    return [r for r in rows if str(r.get("categorie", "")).strip() == category]


def highlight_our_bike(df: pd.DataFrame, our_numero: str) -> pd.io.formats.style.Styler:
    """Styler qui surligne la moto 96."""
    def _row_style(row):
        if str(row.get("numero", "")) == str(our_numero) or str(row.get("No.", "")) == str(our_numero):
            return ["background-color: rgba(255, 215, 0, 0.25); font-weight: 600;"] * len(row)
        return [""] * len(row)
    return df.style.apply(_row_style, axis=1)


def render_metric_card(label: str, value: str, delta: Optional[str] = None) -> None:
    st.metric(label=label, value=value, delta=delta)


def render_gain_loss(value: Optional[float], unit: str = "s") -> str:
    if value is None:
        return "—"
    txt = format_signed(value, unit)
    color = "#2bb673" if value > 0 else ("#d94545" if value < 0 else "#888")
    return f"<span style='color:{color};font-weight:600'>{txt}</span>"


def format_lap_value(val: Any) -> str:
    if val is None:
        return "—"
    if isinstance(val, (int, float)):
        return format_seconds(val)
    return str(val)


def empty_state(msg: str = "Aucune donnée disponible pour le moment.") -> None:
    st.info(msg)
