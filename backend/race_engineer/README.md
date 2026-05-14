# 🏍️ Race Engineer — Endurance Moto

Application web Python/Streamlit de suivi live, d'analyse stratégique et de
prédiction pour les courses d'endurance moto.

**Configuration par défaut :** LEGACY COMPETITION — Moto n°96 — Catégorie PRD.

---

## ✨ Fonctionnalités

- 📊 **Dashboard** : vue synthétique, alertes pit window, comparaison concurrent
- 📡 **Live Timing** : tableau temps réel avec mise en évidence de la 96
- 🏍️ **Notre moto** : stats détaillées (relais, moyennes, prédictions carburant)
- 👤 **Pilotes** : statistiques par pilote (régularité, dégradation, tendance, reco)
- 🏁 **Concurrents** : grille de relais et temps d'arrêt par concurrent
- ⚖️ **Comparatif** : analyse relais-par-relais Notre moto vs concurrent (piste + stand)
- 🧠 **Stratégie** : timeline d'événements, carburant, pneus, simulation 3 scénarios
- 🕒 **Historique / Replay** : navigation dans les snapshots passés, exports CSV/Excel/JSON
- ⚙️ **Paramètres** : configuration équipe, pilotes, carburant, pneus, concurrents

---

## 🚀 Installation locale

```bash
git clone <repo-url>
cd race_engineer

# Optionnel mais recommandé
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre dans le navigateur sur `http://localhost:8501`.

---

## ☁️ Déploiement Streamlit Cloud

1. Pousser ce dépôt sur GitHub
2. Aller sur [streamlit.io/cloud](https://streamlit.io/cloud)
3. New app → connecter le repo → fichier principal : `app.py`
4. Python version : 3.10+
5. Deploy

L'URL publique est partageable avec toute l'équipe au stand.

---

## 🧠 Logique métier : la colonne `Last Pit`

C'est la colonne centrale du flux. Elle représente **le nombre de tours
effectués depuis le dernier arrêt au stand**.

- Pendant un relais, `Last Pit` augmente à chaque tour.
- Quand la moto repasse au stand, `Last Pit` retombe à `0` et `Total Pit`
  s'incrémente.
- Le **temps du dernier arrêt** est donné par `Last Pit Time`.

### Détection d'un relais terminé

Implémentée dans `race_engineer/relay_tracker.py`. L'application déclenche
l'enregistrement d'un relais quand :

1. **`Total Pit` augmente** par rapport à la valeur précédente — un arrêt vient
   d'être validé.  
2. **OU** `Last Pit` retombe à `0` alors qu'il était `>0` — la moto vient de
   ressortir des stands.

Dans les deux cas, le nombre de tours du relais terminé est la **dernière
valeur connue de `Last Pit` avant l'événement** (on garde un max courant pour
robustesse face aux rafraîchissements rapides).

L'idempotence est assurée par une contrainte `UNIQUE(numero, relais)` dans
SQLite : un même relais ne peut pas être enregistré deux fois.

### Nettoyage des balises

Le flux peut contenir des marqueurs `{entree-stand}Pit In`, `{sortie-stand}Pit Out`,
`{meilleur-temps}...`. Le parser :
- détecte l'état pit (`PIT_IN` / `PIT_OUT`) et le pose dans `pit_state`
- nettoie les balises pour ne garder que la valeur textuelle utile

---

## ⚖️ Logique du comparatif

Pour chaque relais aligné (n°1, n°2, etc.) entre notre moto et un concurrent :

- **Temps piste** = moyenne au tour × nombre de tours du relais
- **Gain/perte piste** = `temps_piste_conc - temps_piste_96`  
  → positif = la 96 a gagné en piste
- **Gain/perte stand** = `temps_arret_conc - temps_arret_96`  
  → positif = la 96 a gagné au stand
- **Bilan relais** = gain piste + gain stand
- **Cumul** = somme des bilans depuis le départ

Convention de signe partout dans l'app : **positif = gain pour la 96**.

---

## 💾 Stockage local SQLite

Base : `race_engineer_history.sqlite` (créée automatiquement à côté de `app.py`).

Tables :
| Table | Contenu |
|---|---|
| `snapshots` | Payload JSON complet de chaque fetch live |
| `relay_events` | 1 ligne par relais terminé (unique `numero, relais`) |
| `pilot_laps` | 1 ligne par tour par moto (unique `numero, tour_total`) |
| `planned_events` | Événements stratégiques planifiés (pit, changement pilote…) |
| `app_config` | (Réservé) — la config principale est dans `race_engineer_config.json` |

Mode WAL activé pour limiter les verrouillages en accès concurrent (Streamlit
peut spawner plusieurs threads).

---

## 🧪 Tests / mode démo

Pas de connexion live ? Allez dans **Paramètres → Maintenance → Charger un
snapshot mock**. Cela charge un jeu de 9 motos simulant 30 min (ou plus) de
course pour explorer l'app.

Tests manuels recommandés :
- Lancer l'app avec et sans `live_url` valide → vérifier le message d'erreur propre
- Charger un mock à 30 min puis 90 min → vérifier l'apparition de relais
- Configurer un concurrent principal → vérifier le module Comparatif
- Export Excel → vérifier les 9 feuilles
- Redémarrer l'app → vérifier que les snapshots persistent

---

## 📁 Structure du projet

```
race_engineer/
├── app.py                              # Entry point Streamlit + navigation
├── requirements.txt
├── README.md
├── race_engineer_config.json           # créé au 1er lancement
├── race_engineer_history.sqlite        # créé au 1er lancement
└── race_engineer/
    ├── __init__.py
    ├── config.py            # Load/save JSON config
    ├── database.py          # SQLite : tables, upsert, queries
    ├── live_timing.py       # Fetch HTTP + parsing JSON (BOM-safe, no eval)
    ├── relay_tracker.py     # Logique Last Pit / Total Pit
    ├── analytics.py         # Stats pilote, fuel, comparaison
    ├── utils.py             # parse_lap_time, format_seconds, helpers
    ├── exports.py           # CSV / Excel / JSON
    ├── mock_data.py         # Générateur de payload pour démo
    ├── session_state.py     # Init centralisée du st.session_state
    └── ui/
        ├── __init__.py
        ├── _helpers.py
        ├── dashboard.py
        ├── live_timing.py
        ├── our_bike.py
        ├── pilots.py
        ├── competitors.py
        ├── comparison.py
        ├── strategy.py
        ├── history.py
        └── settings.py
```

---

## ⚠️ Limitations connues

- Les prédictions carburant et pit window dépendent d'une **estimation de
  consommation** configurable. À ajuster à chaque essai libre.
- La consommation pilote-par-pilote n'est pas calculée automatiquement à partir
  du flux (le flux ne donne pas le carburant) — c'est une projection basée sur
  la moyenne globale.
- Les pneus sont en saisie manuelle (le flux ne contient pas cette donnée).
- Le matching pilote ↔ flux se fait par nom + alias (configurable en Paramètres).
  Si le nom du flux change, ajouter l'alias.

---

## 📜 Licence

Usage interne — LEGACY COMPETITION.
