# Race Engineer — Svelte + FastAPI

## Prérequis
- Python 3.10+ avec `fastapi`, `uvicorn` installés
- Node.js 22 LTS  →  https://nodejs.org

## Démarrage (2 terminaux)

### Terminal 1 — Backend FastAPI
```powershell
cd race_engineer_svelte\backend
uvicorn main:app --reload --port 8000
```
→ API disponible sur http://localhost:8000
→ Docs interactives : http://localhost:8000/docs

### Terminal 2 — Frontend SvelteKit
```powershell
cd race_engineer_svelte\frontend
npm install        # une seule fois
npm run dev
```
→ App disponible sur http://localhost:5173

## Pages disponibles
| URL                    | Page          |
|------------------------|---------------|
| /                      | Dashboard     |
| /timing                | Live Timing   |
| /bike                  | Notre moto    |
| /pilots                | Pilotes       |
| /competitors           | Concurrents   |
| /comparison            | Comparatif    |
| /strategy              | Stratégie     |
| /history               | Historique    |
| /simulator             | Simulateur    |
| /settings              | Paramètres    |

## Architecture
```
race_engineer_svelte/
├── backend/
│   ├── main.py              ← FastAPI + CORS + simulateur background
│   ├── state.py             ← état partagé + SSE queues
│   └── routers/
│       ├── snapshot.py      ← GET /api/snapshot + GET /api/stream (SSE)
│       ├── config_router.py ← GET/PUT/PATCH /api/config
│       ├── analytics_router.py ← relais, pilotes, analytique
│       ├── history_router.py   ← snapshots DB
│       └── simulator_router.py ← contrôle simulateur
└── frontend/
    └── src/
        ├── lib/
        │   ├── api.js       ← appels REST + SSE
        │   ├── stores.js    ← snapshot, config, simState réactifs
        │   └── components/  ← Sidebar, MetricCard, TimingTable
        └── routes/          ← 9 pages Svelte
```
