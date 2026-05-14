"""Page Live Timing."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from race_engineer.ui._helpers import (
    category_filter_widget,
    collect_categories,
    empty_state,
    filter_rows_by_category,
)

# Colonnes affichées dans l'ordre voulu
DISPLAY_COLS = [
    ("position", "Pos."),
    ("position_cat", "Cat.P"),
    ("numero", "No."),
    ("categorie", "Cat"),
    ("team", "Team"),
    ("rider", "Rider"),
    ("laps", "Laps"),
    ("l_lap", "L. Lap"),
    ("best_lap", "Best Lap"),
    ("last_pit", "Last Pit"),
    ("last_pit_time", "Last Pit Time"),
    ("total_pit", "Total Pit"),
    ("total_pit_time", "Total pit time"),
]


def page_live_timing(parsed: Optional[Dict[str, Any]], config: Dict[str, Any]) -> None:
    st.title("📡 Live Timing")

    if not parsed or not parsed.get("rows"):
        empty_state("Aucune donnée live timing disponible.")
        return

    rows = parsed["rows"]
    cats = collect_categories(parsed)

    col_filter, col_info = st.columns([1, 3])
    with col_filter:
        category = category_filter_widget(
            default_category=config.get("our_category", "PRD"),
            all_categories=cats,
            key="live_cat_filter",
        )
    with col_info:
        st.caption(
            f"Snapshot : {parsed.get('fetched_at', '—')} — "
            f"{len(rows)} motos — Catégorie affichée : **{category}**"
        )

    filtered = filter_rows_by_category(rows, category)
    if not filtered:
        empty_state(f"Aucune moto dans la catégorie {category}.")
        return

    # Construction DataFrame avec colonnes ordonnées
    display_data = []
    our_numero = str(config.get("our_bike_number", "96"))
    for row in filtered:
        rec = {}
        for canon, label in DISPLAY_COLS:
            rec[label] = row.get(canon, "—")
        rec["_pit_state"] = row.get("pit_state", "")
        rec["_is_ours"] = (str(row.get("numero")) == our_numero)
        display_data.append(rec)

    df = pd.DataFrame(display_data)

    # Tri par position si dispo
    if "Pos." in df.columns:
        df["_pos_sort"] = pd.to_numeric(df["Pos."], errors="coerce").fillna(9999)
        df = df.sort_values("_pos_sort").drop(columns=["_pos_sort"])

    df_display = df.drop(columns=["_pit_state", "_is_ours"], errors="ignore")

    # Coloration : moto 96 + pit states
    def _style_rows(row):
        styles = [""] * len(row)
        if df.loc[row.name, "_is_ours"]:
            styles = ["background-color: rgba(255, 215, 0, 0.25); font-weight: 600;"] * len(row)
        return styles

    def _style_l_lap(val, pit_state):
        if not isinstance(val, str):
            return ""
        if pit_state == "PIT_IN":
            return "color: #d94545; font-weight: 600;"
        if pit_state == "PIT_OUT":
            return "color: #2bb673; font-weight: 600;"
        return ""

    styler = df_display.style.apply(_style_rows, axis=1)

    # Coloration L. Lap selon pit_state
    pit_states = df["_pit_state"].tolist()
    if "L. Lap" in df_display.columns:
        styler = styler.apply(
            lambda col: [_style_l_lap(v, pit_states[i]) for i, v in enumerate(col)],
            subset=["L. Lap"],
        )

    st.dataframe(styler, use_container_width=True, hide_index=True, height=600)

    st.caption(
        "🟡 Moto 96 surlignée — "
        "🔴 L. Lap rouge = Pit In — "
        "🟢 L. Lap vert = Pit Out"
    )
