/** Utilitaires partagés. */

export function fmtTime(minutes) {
  const total = Math.floor(minutes * 60);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

export function fmtDelta(seconds) {
  if (seconds == null) return '—';
  const sign = seconds >= 0 ? '+' : '';
  return `${sign}${seconds.toFixed(3)}s`;
}

export function gainClass(val) {
  if (val == null) return 'neutral';
  return val > 0 ? 'gain' : val < 0 ? 'loss' : 'neutral';
}

export function gainSign(val) {
  if (val == null) return '—';
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(1)}s`;
}

export function lapColor(lap, best, avg) {
  if (lap == null) return '';
  if (lap <= best * 1.001) return 'sector-purple';
  if (lap <= avg * 0.999) return 'sector-green';
  return '';
}
