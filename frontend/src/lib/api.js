/** Helpers d'appel à l'API FastAPI backend. */

const BASE = '/api';

async function get(path) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`GET ${path} → ${r.status}`);
  return r.json();
}

async function post(path, body = {}) {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`POST ${path} → ${r.status}`);
  return r.json();
}

async function patch(path, body = {}) {
  const r = await fetch(`${BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`PATCH ${path} → ${r.status}`);
  return r.json();
}

async function put(path, body = {}) {
  const r = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`PUT ${path} → ${r.status}`);
  return r.json();
}

async function del(path) {
  const r = await fetch(`${BASE}${path}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(`DELETE ${path} → ${r.status}`);
  return r.json();
}

// ── API methods ──────────────────────────────────────────────────────────────

export const api = {
  // Snapshot courant
  snapshot:     () => get('/snapshot'),

  // Config
  getConfig:    () => get('/config'),
  saveConfig:   (c) => put('/config', c),
  patchConfig:  (c) => patch('/config', c),

  // Relais / analytique
  relays:       (numero) => get(`/relays?numero=${numero}`),
  allRelays:    () => get('/relays'),
  pilotLaps:    (numero) => get(`/pilot-laps?numero=${numero}`),
  analytics:    (numero, pilot) => get(`/analytics/${numero}?pilot=${encodeURIComponent(pilot)}`),
  bikeSummary:  (numero) => get(`/bike-summary/${numero}`),

  // Historique
  history:      (limit = 200) => get(`/history?limit=${limit}`),
  historyCount: () => get('/history/count'),
  historyItem:  (id) => get(`/history/${id}`),
  clearHistory: () => del('/history'),

  // Simulateur
  simState:     () => get('/simulator/state'),
  simStart:     (speed, duration) => post('/simulator/start', { speed, duration }),
  simPause:     () => post('/simulator/pause'),
  simReset:     () => post('/simulator/reset'),
  simJump:      (minutes) => post('/simulator/jump', { minutes }),
  simSpeed:     (speed) => patch('/simulator/speed', { speed }),
};

// ── SSE live stream ──────────────────────────────────────────────────────────

/**
 * Ouvre un EventSource vers /api/stream.
 * @param {(data: object) => void} onMessage
 * @returns {() => void} close function
 */
export function openStream(onMessage) {
  const es = new EventSource('/api/stream');
  es.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)); } catch {}
  };
  es.onerror = () => {};
  return () => es.close();
}
