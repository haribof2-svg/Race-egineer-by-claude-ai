import { writable, derived } from 'svelte/store';
import { api, openStream } from './api.js';

/* ─── Stores de base ──────────────────────────────────────────────────────── */

export const snapshot  = writable(null);
export const config    = writable(null);
export const simState  = writable({ running: false, elapsed: 0, speed: 1, duration: 1440 });
export const connected = writable(false);

/* ─── Auto-loading global ────────────────────────────────────────────────────
   Démarre au premier import (dans le browser uniquement) et continue jusqu'à
   la fin de la session. Pas besoin que le layout fasse quoi que ce soit. */

let _started = false;
function startBackgroundLoader() {
  if (_started || typeof window === 'undefined') return;
  _started = true;

  async function refreshAll() {
    try {
      const c = await api.getConfig();
      if (c) config.set(c);
    } catch {}

    try {
      const s = await api.snapshot();
      if (s) snapshot.set(s);
      connected.set(true);
    } catch {
      connected.set(false);
    }

    try {
      const ss = await api.simState();
      if (ss) simState.set(ss);
    } catch {}
  }

  refreshAll();
  setInterval(refreshAll, 2000);

  // SSE best-effort
  try {
    openStream((data) => {
      snapshot.set(data);
      connected.set(true);
    });
  } catch {}
}

startBackgroundLoader();

/* ─── Stores dérivés ──────────────────────────────────────────────────────── */

export const ourNumber = derived(config, $c => $c?.our_bike_number ?? '96');

export const ourBike = derived([snapshot, ourNumber], ([$s, $n]) =>
  $s?.rows?.find(r => String(r.numero) === String($n)) ?? null
);

export const competitors = derived([snapshot, config], ([$s, $c]) => {
  if (!$s?.rows || !$c) return [];
  const cat = $c.our_category;
  const num = $c.our_bike_number;
  return $s.rows.filter(r => r.categorie === cat && String(r.numero) !== String(num));
});
