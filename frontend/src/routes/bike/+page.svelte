<script>
  import { ourBike, config } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import MetricCard from '$lib/components/MetricCard.svelte';

  let summary = null;
  let pilotLaps = [];
  let lastLoadedNum = null;

  // Chargement automatique dès que la config arrive, puis refresh toutes les 5s
  let loadIv;
  $: if ($config?.our_bike_number && $config.our_bike_number !== lastLoadedNum) {
    lastLoadedNum = $config.our_bike_number;
    loadData();
    clearInterval(loadIv);
    loadIv = setInterval(loadData, 5000);
  }

  async function loadData() {
    const num = $config?.our_bike_number ?? '96';
    try { summary   = await api.bikeSummary(num); } catch {}
    try { pilotLaps = await api.pilotLaps(num);  } catch {}
  }

  // Calculs réactifs — pas de chaînage, tout depuis les stores directement
  let avgGlobal = null, bestDB = null, totalLaps = 0;
  let relayCount = 0, avgLapsPerRelay = null, longestRelay = null, shortestRelay = null, avgPitSeconds = null;
  let fuelRemainingL = null, lapsRemaining = null, maxLapsPerStint = null, pitWindowOpen = false;
  let currentPilotName = '—';
  let teamName = '—', catName = '—';
  let lapsTotal = 0, lastLap = '—', bestLap = '—', lastPit = 0, totalPit = 0, lastPitTime = '—', position = '—';

  $: {
    const b = $ourBike;
    const c = $config;
    const sm = summary;
    const laps = pilotLaps;

    // ── Live info ─────────────────────────────────────────────────
    teamName    = b?.team       ?? c?.team_name ?? '—';
    catName     = b?.categorie  ?? c?.our_category ?? '—';
    position    = b?.position   ?? '—';
    lapsTotal   = b?.laps       ?? 0;
    lastLap     = b?.l_lap      ?? '—';
    bestLap     = b?.best_lap   ?? '—';
    lastPit     = b?.last_pit   ?? 0;
    totalPit    = b?.total_pit  ?? 0;
    lastPitTime = b?.last_pit_time ?? '—';

    // ── Pilote actif (rotation selon total_pit) ───────────────────
    const active = (c?.pilots ?? []).filter(p => p.active);
    if (active.length > 0) {
      currentPilotName = active[totalPit % active.length]?.name ?? '—';
    } else {
      currentPilotName = b?.rider ?? '—';
    }

    // ── Stats DB ─────────────────────────────────────────────────
    const lapSecs = (laps ?? []).map(l => l.lap_seconds).filter(v => v != null);
    avgGlobal = lapSecs.length ? lapSecs.reduce((a, x) => a + x, 0) / lapSecs.length : null;
    bestDB    = lapSecs.length ? Math.min(...lapSecs) : null;
    totalLaps = lapSecs.length;

    relayCount       = sm?.count ?? 0;
    avgLapsPerRelay  = sm?.avg_laps_per_relay ?? null;
    longestRelay     = sm?.longest_relay ?? null;
    shortestRelay    = sm?.shortest_relay ?? null;
    avgPitSeconds    = sm?.avg_pit_seconds ?? null;

    // ── Carburant ────────────────────────────────────────────────
    const tankCap = Number(c?.fuel?.tank_capacity_l)      || 0;
    const consLap = Number(c?.fuel?.consumption_l_per_lap) || 0;
    const safety  = Number(c?.fuel?.safety_margin_laps)   || 1;
    if (tankCap > 0 && consLap > 0) {
      maxLapsPerStint = Math.floor(tankCap / consLap);
      const used = lastPit * consLap;
      fuelRemainingL = Math.max(tankCap - used, 0);
      lapsRemaining = maxLapsPerStint - lastPit;
      pitWindowOpen = lapsRemaining <= safety + 2;
    } else {
      maxLapsPerStint = null;
      fuelRemainingL = null;
      lapsRemaining = null;
      pitWindowOpen = false;
    }
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
</script>

<svelte:head><title>Notre moto — Race Engineer</title></svelte:head>

<div class="p-6 space-y-6">
  <h1 class="text-2xl font-bold tracking-tight">🏍️ Notre moto · n°{$config?.our_bike_number ?? '96'}</h1>

  <!-- ─── Informations live ────────────────────────────────────────── -->
  {#if $ourBike}
    <section>
      <p class="section-title">État en piste</p>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard label="Équipe"       value={teamName} accent="gold" />
        <MetricCard label="Catégorie"    value={catName} />
        <MetricCard label="Position"     value={position} accent="gold" />
        <MetricCard label="Pilote actif" value={currentPilotName} accent="gold" />
      </div>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
        <MetricCard label="Tours" value={lapsTotal} />
        <MetricCard label="Dernier tour" value={lastLap} accent="green" />
        <MetricCard label="Meilleur tour" value={bestLap} accent="green" />
        <MetricCard label="Tours dep. stand" value={lastPit} />
      </div>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
        <MetricCard label="Total arrêts" value={totalPit} />
        <MetricCard label="Tps dernier arrêt" value={lastPitTime} />
      </div>
    </section>
  {:else}
    <div class="card p-6 text-center text-f1-muted text-sm">Aucun flux live actif. Lancez le simulateur.</div>
  {/if}

  <!-- ─── Statistiques globales (DB) ───────────────────────────────── -->
  <section>
    <p class="section-title">📈 Statistiques globales</p>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <MetricCard label="Moyenne tour" value={fmtSec(avgGlobal)} />
      <MetricCard label="Meilleur tour (DB)" value={fmtSec(bestDB)} accent="green" />
      <MetricCard label="Total tours (DB)" value={totalLaps} />
      <MetricCard label="Relais terminés" value={relayCount} accent="gold" />
    </div>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
      <MetricCard label="Moy. tours/relais" value={avgLapsPerRelay ? avgLapsPerRelay.toFixed(1) : '—'} />
      <MetricCard label="Plus long relais"  value={longestRelay ?? '—'} />
      <MetricCard label="Plus court relais" value={shortestRelay ?? '—'} />
      <MetricCard label="Tps arrêt moyen"   value={avgPitSeconds ? avgPitSeconds.toFixed(1) + 's' : '—'} />
    </div>
  </section>

  <!-- ─── Carburant & prédictions ──────────────────────────────────── -->
  <section>
    <p class="section-title">⛽ Carburant & prédictions</p>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <MetricCard label="Carburant restant"
                  value={fuelRemainingL != null ? fuelRemainingL.toFixed(1) + ' L' : '—'}
                  accent={pitWindowOpen ? 'red' : 'gold'} />
      <MetricCard label="Tours restants"
                  value={lapsRemaining ?? '—'}
                  accent={pitWindowOpen ? 'red' : undefined} />
      <MetricCard label="Max tours/relais" value={maxLapsPerStint ?? '—'} />
      <MetricCard label="Pit window"
                  value={pitWindowOpen ? '🚨 OUVERTE' : 'Fermée'}
                  accent={pitWindowOpen ? 'red' : 'gold'} />
    </div>
    <p class="text-xs text-f1-muted mt-2">⚠️ Estimations basées sur la consommation configurée — à ajuster en <a href="/settings" class="text-f1-gold hover:underline">Paramètres</a>.</p>
  </section>

  <!-- ─── Historique des relais ────────────────────────────────────── -->
  <section>
    <p class="section-title">📋 Historique des relais</p>
    {#if summary?.relays?.length > 0}
      <div class="card overflow-hidden">
        <table class="timing-table">
          <thead><tr>
            <th>Relais</th>
            <th>Pilote</th>
            <th class="text-right">Tours</th>
            <th class="text-right">Tps stand</th>
            <th class="text-right">Tps stand (s)</th>
            <th class="text-right">Tours tot.</th>
          </tr></thead>
          <tbody>
            {#each summary.relays as r}
              <tr>
                <td class="font-bold text-f1-gold">R{r.relais}</td>
                <td>{r.pilote ?? '—'}</td>
                <td class="text-right font-mono">{r.tours_relais ?? '—'}</td>
                <td class="text-right font-mono">{r.last_pit_time ?? '—'}</td>
                <td class="text-right font-mono text-f1-muted">{r.last_pit_seconds ? r.last_pit_seconds.toFixed(1) : '—'}</td>
                <td class="text-right font-mono text-f1-muted">{r.tour_total ?? '—'}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else}
      <div class="card p-6 text-center text-f1-muted text-sm">Aucun relais terminé pour le moment.</div>
    {/if}
  </section>
</div>
