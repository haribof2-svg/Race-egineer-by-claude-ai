<script>
  import { config, ourBike } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import MetricCard from '$lib/components/MetricCard.svelte';

  let stats = {};         // map { pilotName: statsObj }
  let loading = false;
  let selectedName = '';
  let lastKey = '';
  let loadIv;

  // Charge automatiquement dès que config/ourBike est dispo, refresh toutes les 5s
  $: {
    const num = $config?.our_bike_number;
    const activePilots = ($config?.pilots ?? []).filter(p => p.active);
    const key = num + '|' + activePilots.map(p => p.name).join(',');
    if (num && activePilots.length > 0 && key !== lastKey) {
      lastKey = key;
      loadAll(num, activePilots);
      clearInterval(loadIv);
      loadIv = setInterval(() => loadAll(num, activePilots), 5000);
      if (!selectedName) selectedName = activePilots[0].name;
    }
  }

  async function loadAll(num, pilots) {
    loading = true;
    const next = {};
    for (const p of pilots) {
      try {
        next[p.name] = await api.analytics(num, p.name);
      } catch {
        next[p.name] = null;
      }
    }
    stats = next;
    loading = false;
  }

  // Pilote actuellement en piste (rotation selon total_pit)
  let currentRiderName = null;
  $: {
    const active = ($config?.pilots ?? []).filter(p => p.active);
    const tp = Number($ourBike?.total_pit) || 0;
    currentRiderName = active.length ? active[tp % active.length]?.name : null;
  }

  function pilotStatus(p, s) {
    if (!s) return { text: 'Inconnu', cls: 'text-f1-muted' };
    if (currentRiderName && p.name === currentRiderName) return { text: '🟢 EN RELAIS', cls: 'text-f1-green font-bold' };
    if ((s.total_laps ?? 0) === 0) return { text: '⚪ Disponible', cls: 'text-f1-sub' };
    return { text: '🟡 Relais terminé', cls: 'text-f1-gold' };
  }

  function fmtSec(s) {
    if (s == null) return '—';
    if (s >= 60) {
      const m = Math.floor(s / 60);
      const sec = (s - m * 60).toFixed(3);
      return `${m}:${sec.padStart(6, '0')}`;
    }
    return s.toFixed(3) + 's';
  }

  function trendLabel(t) {
    if (!t || t === 'indéterminé') return { text: '— indéterminé', cls: 'text-f1-muted' };
    if (typeof t === 'string') {
      if (t.includes('dégrad') || t.includes('hausse')) return { text: '↗ ' + t, cls: 'loss' };
      if (t.includes('améli') || t.includes('baiss'))   return { text: '↘ ' + t, cls: 'gain' };
      return { text: '→ ' + t, cls: 'neutral' };
    }
    return { text: String(t), cls: 'neutral' };
  }

  $: activePilots = ($config?.pilots ?? []).filter(p => p.active);
  $: selectedPilot = activePilots.find(p => p.name === selectedName);
  $: selectedStats = stats[selectedName] ?? null;
</script>

<svelte:head><title>Pilotes — Race Engineer</title></svelte:head>

<div class="p-6 space-y-6">
  <h1 class="text-2xl font-bold tracking-tight">👤 Pilotes</h1>

  {#if activePilots.length === 0}
    <div class="card p-8 text-center text-f1-muted">
      Aucun pilote configuré. Va dans <a href="/settings" class="text-f1-gold hover:underline">Paramètres</a>.
    </div>
  {:else if loading && Object.keys(stats).length === 0}
    <div class="card p-8 text-center text-f1-muted">Chargement des statistiques…</div>
  {:else}

    <!-- ─── Tableau récapitulatif ──────────────────────────────────── -->
    <section>
      <p class="section-title">📋 Vue d'ensemble</p>
      <div class="card overflow-x-auto">
        <table class="timing-table">
          <thead>
            <tr>
              <th>Pilote</th>
              <th>Statut</th>
              <th class="text-right">Tours</th>
              <th class="text-right">Relais</th>
              <th class="text-right">Moyenne</th>
              <th class="text-right">Best</th>
              <th class="text-right">Der. relais</th>
              <th class="text-right">Moy. der.</th>
              <th class="text-right">Régularité</th>
              <th>Tendance</th>
              <th>Reco</th>
            </tr>
          </thead>
          <tbody>
            {#each activePilots as p}
              {@const s = stats[p.name]}
              {@const st = pilotStatus(p, s)}
              {@const tr = trendLabel(s?.trend)}
              <tr class:our-bike={p.name === currentRiderName}>
                <td>
                  <span class="inline-flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full" style="background:{p.color}"></span>
                    <span class="font-semibold">{p.name}</span>
                  </span>
                </td>
                <td class={st.cls}>{st.text}</td>
                <td class="text-right font-mono">{s?.total_laps ?? '—'}</td>
                <td class="text-right font-mono">{s?.total_relays ?? '—'}</td>
                <td class="text-right font-mono">{fmtSec(s?.mean_lap)}</td>
                <td class="text-right font-mono text-f1-green">{fmtSec(s?.best_lap)}</td>
                <td class="text-right font-mono">{s?.last_relay_laps_count ?? '—'}</td>
                <td class="text-right font-mono">{fmtSec(s?.last_relay_mean)}</td>
                <td class="text-right font-mono">{s?.regularity_idx != null ? s.regularity_idx.toFixed(0) + '/100' : '—'}</td>
                <td class={tr.cls}>{tr.text}</td>
                <td class="text-xs text-f1-sub max-w-[200px] truncate">{s?.recommendation ?? '—'}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>

    <!-- ─── Détail par pilote ──────────────────────────────────────── -->
    <section class="space-y-4">
      <div class="flex items-center justify-between">
        <p class="section-title mb-0">🔍 Détail par pilote</p>
        <div class="flex gap-2 flex-wrap">
          {#each activePilots as p}
            <button class="btn-ghost text-xs px-3 py-1.5
              {selectedName === p.name ? '!border-f1-gold !text-f1-gold' : ''}"
              onclick={() => selectedName = p.name}>
              <span class="inline-block w-2 h-2 rounded-full mr-1.5 align-middle" style="background:{p.color}"></span>
              {p.name}
            </button>
          {/each}
        </div>
      </div>

      {#if selectedPilot && selectedStats}
        {@const s = selectedStats}
        <!-- Activité course -->
        <div>
          <p class="text-xs uppercase tracking-widest text-f1-muted mb-2">Activité course</p>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <MetricCard label="Tours totaux" value={s.total_laps ?? 0} accent="gold" />
            <MetricCard label="Relais effectués" value={s.total_relays ?? 0} />
            <MetricCard label="Tours relais en cours" value={s.current_relay_laps_count ?? 0} />
            <MetricCard label="Tours dernier relais" value={s.last_relay_laps_count ?? 0} />
          </div>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
            <MetricCard label="Moy. tours/relais" value={s.avg_laps_per_relay ? s.avg_laps_per_relay.toFixed(1) : '—'} />
            <MetricCard label="Plus long relais" value={s.longest_relay_laps || '—'} />
            <MetricCard label="Plus court relais" value={s.shortest_relay_laps || '—'} />
            <MetricCard label="Relais actuel n°" value={s.current_relay || '—'} />
          </div>
        </div>

        <!-- Performance chrono -->
        <div>
          <p class="text-xs uppercase tracking-widest text-f1-muted mb-2">Performance chrono</p>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <MetricCard label="Meilleur tour" value={fmtSec(s.best_lap)} accent="green" />
            <MetricCard label="Moyenne globale" value={fmtSec(s.mean_lap)} />
            <MetricCard label="Médiane" value={fmtSec(s.median_lap)} />
            <MetricCard label="Écart-type" value={s.stdev_lap ? fmtSec(s.stdev_lap) : '—'} />
          </div>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
            <MetricCard label="Moy. 5 meilleurs"      value={fmtSec(s.best5_mean)} />
            <MetricCard label="Moy. 10 derniers"      value={fmtSec(s.last10_mean)} />
            <MetricCard label="Moy. relais en cours"  value={fmtSec(s.current_relay_mean)} />
            <MetricCard label="Best relais en cours"  value={fmtSec(s.current_relay_best)} accent="green" />
          </div>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
            <MetricCard label="Moy. dernier relais"   value={fmtSec(s.last_relay_mean)} />
            <MetricCard label="Best dernier relais"   value={fmtSec(s.last_relay_best)} accent="green" />
            <MetricCard label="Régularité"            value={s.regularity_idx != null ? s.regularity_idx.toFixed(0) + '/100' : '—'} accent="gold" />
            <MetricCard label="Tendance"              value={trendLabel(s.trend).text} />
          </div>
        </div>

        <!-- Dégradation -->
        <div>
          <p class="text-xs uppercase tracking-widest text-f1-muted mb-2">Dégradation dans le relais</p>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <MetricCard label="Moy. 3 premiers tours" value={fmtSec(s.deg_first3_mean)} />
            <MetricCard label="Moy. 3 derniers tours" value={fmtSec(s.deg_last3_mean)} />
            <MetricCard label="Delta dégradation"
                        value={s.degradation != null ? (s.degradation > 0 ? '+' : '') + s.degradation.toFixed(3) + 's' : '—'}
                        accent={s.degradation > 0.5 ? 'red' : 'green'} />
          </div>
        </div>

        <!-- Recommandation -->
        {#if s.recommendation}
          <div class="card p-4 border-l-2 border-l-f1-gold">
            <p class="text-sm"><span class="font-bold text-f1-gold">💡 Recommandation :</span> {s.recommendation}</p>
          </div>
        {/if}

        <!-- Graphique évolution -->
        {#if s.raw_lap_secs?.length > 0}
          <div>
            <p class="text-xs uppercase tracking-widest text-f1-muted mb-2">📈 Évolution des temps au tour ({s.raw_lap_secs.length} tours)</p>
            <div class="card p-4">
              {@const data = s.raw_lap_secs}
              {@const minV = Math.min(...data)}
              {@const maxV = Math.max(...data)}
              {@const range = maxV - minV || 1}
              {@const W = 800}
              {@const H = 220}
              {@const stepX = data.length > 1 ? W / (data.length - 1) : 0}
              {@const meanV = s.mean_lap}
              {@const meanY = meanV != null ? H - ((meanV - minV) / range) * H : null}
              <svg viewBox="0 0 {W} {H}" class="w-full h-auto" preserveAspectRatio="none">
                <!-- Ligne moyenne -->
                {#if meanY != null}
                  <line x1="0" y1={meanY} x2={W} y2={meanY} stroke="#666" stroke-dasharray="4 3" stroke-width="1"/>
                  <text x="4" y={meanY - 4} font-size="10" fill="#999" font-family="JetBrains Mono,monospace">Moy. {fmtSec(meanV)}</text>
                {/if}
                <!-- Polyline -->
                <polyline
                  fill="none"
                  stroke={selectedPilot.color}
                  stroke-width="2"
                  points={data.map((v, i) => `${i * stepX},${H - ((v - minV) / range) * H}`).join(' ')}
                />
                <!-- Points -->
                {#each data as v, i}
                  <circle cx={i * stepX} cy={H - ((v - minV) / range) * H} r="2.5" fill={selectedPilot.color}/>
                {/each}
              </svg>
              <div class="flex justify-between text-xs text-f1-muted font-mono mt-1">
                <span>Tour 1</span>
                <span>Tour {data.length}</span>
              </div>
            </div>
          </div>
        {/if}

      {:else if selectedPilot}
        <div class="card p-6 text-center text-f1-muted text-sm">Aucune donnée pour {selectedPilot.name}.</div>
      {/if}
    </section>

    <!-- ─── Comparaison entre pilotes (box plot simple) ────────────── -->
    <section>
      <p class="section-title">📊 Comparaison entre pilotes</p>
      <div class="card p-4">
        <div class="space-y-2">
          {#each activePilots as p}
            {@const ps = stats[p.name]}
            {#if ps?.raw_lap_secs?.length > 0}
              {@const data = ps.raw_lap_secs}
              {@const sorted = [...data].sort((a, b) => a - b)}
              {@const q1 = sorted[Math.floor(sorted.length * 0.25)]}
              {@const median = sorted[Math.floor(sorted.length * 0.5)]}
              {@const q3 = sorted[Math.floor(sorted.length * 0.75)]}
              {@const allMin = Math.min(...activePilots.flatMap(pp => stats[pp.name]?.raw_lap_secs ?? []))}
              {@const allMax = Math.max(...activePilots.flatMap(pp => stats[pp.name]?.raw_lap_secs ?? []))}
              {@const range = allMax - allMin || 1}
              <div class="flex items-center gap-3">
                <div class="w-28 text-xs font-semibold flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full" style="background:{p.color}"></span>
                  <span class="truncate">{p.name}</span>
                </div>
                <div class="flex-1 relative h-6 bg-f1-bg rounded">
                  <!-- Range min-max line -->
                  <div class="absolute top-1/2 -translate-y-1/2 h-0.5 bg-f1-border"
                       style="left:{((sorted[0] - allMin) / range) * 100}%; right:{100 - ((sorted[sorted.length-1] - allMin) / range) * 100}%"></div>
                  <!-- Q1-Q3 box -->
                  <div class="absolute top-1 bottom-1 rounded opacity-60"
                       style="background:{p.color}; left:{((q1 - allMin) / range) * 100}%; right:{100 - ((q3 - allMin) / range) * 100}%"></div>
                  <!-- Median tick -->
                  <div class="absolute top-0 bottom-0 w-0.5 bg-white"
                       style="left:{((median - allMin) / range) * 100}%"></div>
                </div>
                <div class="text-xs text-f1-muted font-mono w-20 text-right">{fmtSec(median)}</div>
              </div>
            {/if}
          {/each}
        </div>
        <p class="text-xs text-f1-muted mt-3">Médiane en blanc · zone Q1–Q3 colorée · extension min/max</p>
      </div>
    </section>

  {/if}
</div>
