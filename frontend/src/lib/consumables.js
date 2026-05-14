import { writable } from 'svelte/store';

const KEY = 'race_eng_consumables_v1';

const DEFAULTS = {
  front_tire:  { installed_at_lap: 0, max_laps: 60  },
  rear_tire:   { installed_at_lap: 0, max_laps: 45  },
  front_brake: { installed_at_lap: 0, max_laps: 120 },
};

function load() {
  if (typeof window === 'undefined') return { ...DEFAULTS };
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        front_tire:  { ...DEFAULTS.front_tire,  ...(parsed.front_tire  ?? {}) },
        rear_tire:   { ...DEFAULTS.rear_tire,   ...(parsed.rear_tire   ?? {}) },
        front_brake: { ...DEFAULTS.front_brake, ...(parsed.front_brake ?? {}) },
      };
    }
  } catch {}
  return { ...DEFAULTS };
}

export const consumables = writable(load());

if (typeof window !== 'undefined') {
  consumables.subscribe(c => {
    try { localStorage.setItem(KEY, JSON.stringify(c)); } catch {}
  });
}

export function resetPart(part, currentLap) {
  consumables.update(c => ({
    ...c,
    [part]: { ...c[part], installed_at_lap: currentLap },
  }));
}

export function setMaxLaps(part, value) {
  consumables.update(c => ({
    ...c,
    [part]: { ...c[part], max_laps: Math.max(1, Number(value) || 1) },
  }));
}
