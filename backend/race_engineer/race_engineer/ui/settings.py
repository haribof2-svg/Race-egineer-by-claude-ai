"""Page Paramètres."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import streamlit as st

from race_engineer.config import DEFAULT_CONFIG, load_config, save_config
from race_engineer.database import reset_db
from race_engineer.live_timing import fetch_live_data, parse_live_payload
from race_engineer.mock_data import generate_mock_payload


def page_settings(parsed: Optional[Dict[str, Any]], config: Dict[str, Any]) -> None:
    st.title("⚙️ Paramètres")

    tabs = st.tabs([
        "🏍️ Équipe", "👤 Pilotes", "⛽ Carburant", "🛞 Pneus",
        "🏁 Concurrents", "📥 Exports", "🛠️ Maintenance",
    ])

    # ========== Tab 1 - Équipe ==========
    with tabs[0]:
        st.subheader("Équipe & flux live")

        team_name = st.text_input("Nom équipe", value=config.get("team_name", ""))
        bike_num = st.text_input("Numéro moto", value=str(config.get("our_bike_number", "")))
        cat = st.text_input("Catégorie", value=config.get("our_category", "PRD"))

        live_url = st.text_input("URL live timing", value=config.get("live_url", ""))

        col1, col2 = st.columns(2)
        with col1:
            auto = st.toggle("Auto-refresh activé", value=bool(config.get("auto_refresh", True)))
        with col2:
            interval = st.slider("Intervalle (s)", 1, 30, int(config.get("refresh_interval", 3)))

        if st.button("💾 Sauvegarder équipe", type="primary"):
            config["team_name"] = team_name
            config["our_bike_number"] = bike_num.strip()
            config["our_category"] = cat.strip().upper()
            config["live_url"] = live_url.strip()
            config["auto_refresh"] = auto
            config["refresh_interval"] = interval
            save_config(config)
            st.success("Sauvegardé.")
            st.rerun()

        # Test de connexion
        if st.button("🔌 Tester le flux live"):
            with st.spinner("Test en cours..."):
                raw, err = fetch_live_data(live_url)
                if err:
                    st.error(f"Erreur : {err}")
                else:
                    p = parse_live_payload(raw)
                    if p and p.get("rows"):
                        st.success(f"✅ Connexion OK — {len(p['rows'])} motos détectées.")
                        st.json({
                            "fetched_at": p["fetched_at"],
                            "columns": p["columns"],
                            "first_row": p["rows"][0] if p["rows"] else None,
                        })
                    else:
                        st.warning("Réponse reçue mais aucune donnée exploitable.")

    # ========== Tab 2 - Pilotes ==========
    with tabs[1]:
        st.subheader("Pilotes")
        pilots = config.get("pilots", [])

        n_pilots = st.radio("Nombre de pilotes", [3, 4],
                            index=0 if len([p for p in pilots if p.get("active", True)]) <= 3 else 1,
                            horizontal=True)

        new_pilots = []
        for i in range(4):
            with st.expander(f"Pilote {i+1}", expanded=(i < n_pilots)):
                p = pilots[i] if i < len(pilots) else {
                    "name": f"Pilote {i+1}", "alias": [], "color": "#888888",
                    "order": i+1, "active": (i < n_pilots),
                }
                cols = st.columns([2, 1, 1, 1])
                with cols[0]:
                    name = st.text_input("Nom", value=p.get("name", ""), key=f"p_name_{i}")
                with cols[1]:
                    color = st.color_picker("Couleur", value=p.get("color", "#888"), key=f"p_color_{i}")
                with cols[2]:
                    order = st.number_input("Ordre", min_value=1, max_value=10, value=int(p.get("order", i+1)), key=f"p_order_{i}")
                with cols[3]:
                    active = st.checkbox("Actif", value=bool(p.get("active", i < n_pilots)) and (i < n_pilots), key=f"p_active_{i}")
                aliases_str = st.text_input(
                    "Alias (séparés par virgule)",
                    value=", ".join(p.get("alias", [])),
                    key=f"p_alias_{i}",
                    help="Noms alternatifs utilisés dans le live timing",
                )
                aliases = [a.strip() for a in aliases_str.split(",") if a.strip()]

                new_pilots.append({
                    "name": name,
                    "alias": aliases,
                    "color": color,
                    "order": int(order),
                    "active": active and (i < n_pilots),
                })

        if st.button("💾 Sauvegarder pilotes", type="primary"):
            new_pilots.sort(key=lambda p: p["order"])
            config["pilots"] = new_pilots
            save_config(config)
            st.success("Sauvegardé.")
            st.rerun()

    # ========== Tab 3 - Carburant ==========
    with tabs[2]:
        st.subheader("Carburant")
        fc = config.get("fuel", {})
        tank = st.number_input("Capacité réservoir (L)", min_value=1.0, max_value=50.0,
                               value=float(fc.get("tank_capacity_l", 24.0)), step=0.5)
        conso = st.number_input("Consommation (L/tour)", min_value=0.1, max_value=10.0,
                                value=float(fc.get("consumption_l_per_lap", 3.2)), step=0.1)
        margin = st.number_input("Marge sécurité (tours)", min_value=0, max_value=10,
                                  value=int(fc.get("safety_margin_laps", 1)), step=1)
        refuel = st.number_input("Quantité de plein (L)", min_value=1.0, max_value=50.0,
                                  value=float(fc.get("refuel_amount_l", 24.0)), step=0.5)
        if st.button("💾 Sauvegarder carburant", type="primary"):
            config["fuel"] = {
                "tank_capacity_l": tank,
                "consumption_l_per_lap": conso,
                "safety_margin_laps": margin,
                "refuel_amount_l": refuel,
            }
            save_config(config)
            st.success("Sauvegardé.")
            st.rerun()

    # ========== Tab 4 - Pneus ==========
    with tabs[3]:
        st.subheader("Pneus")
        tc = config.get("tires", {})
        tracking = st.toggle("Activer le suivi des pneus", value=bool(tc.get("tracking_enabled", False)))
        wear = st.number_input("Usure estimée (% / tour)", min_value=0.0, max_value=10.0,
                                value=float(tc.get("wear_per_lap_pct", 1.5)), step=0.1)
        impact = st.number_input("Impact perf (% par % usure)", min_value=0.0, max_value=1.0,
                                  value=float(tc.get("performance_impact_pct_per_pct_wear", 0.05)),
                                  step=0.01, format="%.2f")
        if st.button("💾 Sauvegarder pneus", type="primary"):
            config["tires"] = {
                "tracking_enabled": tracking,
                "wear_per_lap_pct": wear,
                "performance_impact_pct_per_pct_wear": impact,
            }
            save_config(config)
            st.success("Sauvegardé.")
            st.rerun()

    # ========== Tab 5 - Concurrents ==========
    with tabs[4]:
        st.subheader("Concurrents")
        cc = config.get("competitors", {})

        default_cat = st.text_input("Catégorie par défaut", value=cc.get("default_category", "PRD"))
        favorites_str = st.text_input(
            "Favoris (numéros séparés par virgule)",
            value=", ".join(cc.get("favorites", [])),
        )
        main = st.text_input("Concurrent principal de comparaison (numéro)",
                              value=cc.get("main_comparison", ""))
        if st.button("💾 Sauvegarder concurrents", type="primary"):
            config["competitors"] = {
                "default_category": default_cat.strip().upper(),
                "favorites": [n.strip() for n in favorites_str.split(",") if n.strip()],
                "main_comparison": main.strip(),
            }
            save_config(config)
            st.success("Sauvegardé.")
            st.rerun()

    # ========== Tab 6 - Exports ==========
    with tabs[5]:
        st.subheader("Exports")
        ec = config.get("export", {})
        path = st.text_input("Chemin export local", value=ec.get("export_path", "exports/"))
        auto = st.toggle("Export automatique", value=bool(ec.get("auto_export", False)))
        if st.button("💾 Sauvegarder exports", type="primary"):
            config["export"] = {"export_path": path, "auto_export": auto}
            save_config(config)
            st.success("Sauvegardé.")

    # ========== Tab 7 - Maintenance ==========
    with tabs[6]:
        st.subheader("Maintenance")

        st.markdown("#### Données mock (démo / hors-ligne)")
        st.caption(
            "Permet de charger un jeu de données simulé pour tester l'app sans connexion au live timing."
        )
        elapsed = st.slider("Minutes simulées de course", 5, 240, 30)
        if st.button("🎲 Charger un snapshot mock"):
            mock = generate_mock_payload(elapsed_minutes=elapsed)
            st.session_state["last_parsed"] = parse_live_payload(mock)
            st.session_state["last_raw"] = mock
            st.success(f"✅ Snapshot mock chargé ({elapsed} min de course simulées).")
            st.rerun()

        st.markdown("---")
        st.markdown("#### Configuration JSON")
        st.code(json.dumps(config, indent=2, ensure_ascii=False), language="json")

        st.markdown("---")
        st.markdown("#### Reset")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("♻️ Reset config par défaut"):
                save_config({k: v for k, v in DEFAULT_CONFIG.items()})
                st.success("Config réinitialisée.")
                st.rerun()
        with col2:
            if st.button("💣 Reset base SQLite", help="Supprime tous les snapshots / relais / tours."):
                if st.session_state.get("confirm_reset_db"):
                    reset_db()
                    st.session_state["confirm_reset_db"] = False
                    st.success("Base réinitialisée.")
                    st.rerun()
                else:
                    st.session_state["confirm_reset_db"] = True
                    st.warning("Cliquez à nouveau pour confirmer.")
