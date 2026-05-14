"""Page Concurrents."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from race_engineer.database import get_pilot_laps, get_relay_events
from race_engineer.relay_tracker import get_relay_summary
from race_engineer.ui._helpers import (
    category_filter_widget,
    collect_categories,
    empty_state,
    filter_rows_by_category,
    format_lap_value,
)
from race_engineer.utils import parse_lap_time, safe_mean, safe_min


def page_competitors(parsed: Optional[Dict[str, Any]], config: Dict[str, Any]) -> None:
    st.title("🏁 Concurrents")

    our_numero = str(config.get("our_bike_number", "96"))
    default_cat = config.get("competitors", {}).get("default_category", "PRD")

    if not parsed or not parsed.get("rows"):
        empty_state("Aucun flux live actif.")
        return

    # ---- Filtre catégorie ------------------------------------------------
    cats = collect_categories(parsed)
    category = category_filter_widget(
        default_category=default_cat,
        all_categories=cats,
        key="comp_cat_filter",
    )

    rows = filter_rows_by_category(parsed["rows"], category)
    if not rows:
        empty_state(f"Aucune moto dans la catégorie {category}.")
        return

    # Tri par position
    rows_sorted = sorted(rows, key=lambda r: r.get("position") or 9999)

    # ---- Classement filtré -----------------------------------------------
    st.subheader(f"Classement live — Catégorie {category}")
    display = []
    for r in rows_sorted:
        display.append({
            "Pos.": r.get("position"),
            "Cat.P": r.get("position_cat"),
            "No.": r.get("numero"),
            "Team": r.get("team"),
            "Cat": r.get("categorie"),
            "Laps": r.get("laps"),
            "L. Lap": r.get("l_lap"),
            "Best": r.get("best_lap"),
            "Last Pit": r.get("last_pit"),
            "Total Pit": r.get("total_pit"),
            "Favori": "⭐" if r.get("numero") in config.get("competitors", {}).get("favorites", []) else "",
        })
    df = pd.DataFrame(display)

    def _style(row):
        if str(row["No."]) == our_numero:
            return ["background-color: rgba(255, 215, 0, 0.25); font-weight: 600;"] * len(row)
        if row["Favori"] == "⭐":
            return ["background-color: rgba(70, 150, 255, 0.10);"] * len(row)
        return [""] * len(row)

    st.dataframe(df.style.apply(_style, axis=1), use_container_width=True, hide_index=True)

    # ---- Tableau relais par moto -----------------------------------------
    st.subheader("📊 Relais par concurrent")

    relay_table = _build_relay_grid(rows_sorted, our_numero)
    if relay_table.empty:
        empty_state("Aucun relais enregistré.")
    else:
        st.dataframe(relay_table, use_container_width=True, hide_index=True)

    # ---- Tableau temps d'arrêt -------------------------------------------
    st.subheader("🔧 Temps d'arrêt par concurrent")
    pit_table = _build_pit_grid(rows_sorted, our_numero)
    if pit_table.empty:
        empty_state("Aucun temps d'arrêt enregistré.")
    else:
        st.dataframe(pit_table, use_container_width=True, hide_index=True)

    # ---- Vue détaillée d'un concurrent -----------------------------------
    st.subheader("🔍 Détail concurrent")
    numeros = [r.get("numero") for r in rows_sorted if r.get("numero")]
    selected_num = st.selectbox("Concurrent", numeros, key="comp_detail_select")
    if selected_num:
        _render_competitor_detail(selected_num, parsed["rows"], config)


def _build_relay_grid(rows: List[Dict[str, Any]], our_numero: str) -> pd.DataFrame:
    """Construit une grille : 1 ligne par moto, 1 colonne par relais (nb tours)."""
    data = []
    for r in rows:
        num = r.get("numero")
        if not num:
            continue
        relays = [dict(rel) for rel in get_relay_events(num)]
        rec = {
            "No.": num,
            "Team": r.get("team"),
            "Cat": r.get("categorie"),
            "Cat.P": r.get("position_cat"),
        }
        for rel in relays:
            rec[f"R{rel['relais']}"] = rel.get("tours_relais")
        data.append(rec)
    return pd.DataFrame(data) if data else pd.DataFrame()


def _build_pit_grid(rows: List[Dict[str, Any]], our_numero: str) -> pd.DataFrame:
    """Construit une grille des temps d'arrêt par relais."""
    data = []
    for r in rows:
        num = r.get("numero")
        if not num:
            continue
        relays = [dict(rel) for rel in get_relay_events(num)]
        rec = {
            "No.": num,
            "Team": r.get("team"),
            "Cat": r.get("categorie"),
        }
        for rel in relays:
            rec[f"Arrêt {rel['relais']}"] = rel.get("last_pit_time") or "—"
        data.append(rec)
    return pd.DataFrame(data) if data else pd.DataFrame()


def _render_competitor_detail(numero: str, rows: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
    row = next((r for r in rows if str(r.get("numero")) == str(numero)), None)
    if not row:
        empty_state(f"Concurrent n°{numero} introuvable.")
        return

    laps = [dict(l) for l in get_pilot_laps(numero=numero)]
    lap_secs = [l["lap_seconds"] for l in laps if l.get("lap_seconds") is not None]
    summary = get_relay_summary(numero)

    cols = st.columns(4)
    cols[0].metric("Position", row.get("position") or "—")
    cols[1].metric("Tours", row.get("laps") or "—")
    cols[2].metric("Meilleur tour", format_lap_value(parse_lap_time(row.get("best_lap"))))
    cols[3].metric("Moyenne globale", format_lap_value(safe_mean(lap_secs)))

    cols = st.columns(4)
    cols[0].metric("Relais effectués", summary["count"])
    cols[1].metric("Tours/relais moy.", f"{summary['avg_laps_per_relay']:.1f}" if summary['avg_laps_per_relay'] else "—")
    cols[2].metric("Arrêt moyen", format_lap_value(summary['avg_pit_seconds']))
    cols[3].metric("Total arrêts", row.get("total_pit") or 0)

    # Marquage favori
    favs = list(config.get("competitors", {}).get("favorites", []))
    is_fav = numero in favs
    if st.button("⭐ Retirer des favoris" if is_fav else "⭐ Ajouter aux favoris"):
        if is_fav:
            favs.remove(numero)
        else:
            favs.append(numero)
        config.setdefault("competitors", {})["favorites"] = favs
        from race_engineer.config import save_config
        save_config(config)
        st.rerun()
