<script>
  import { ourBike, config, simState } from '$lib/stores.js';
  import { fmtTime } from '$lib/utils.js';

  let pitLaps = 0, lapsLeft = 0, fuelPct = 0, fuelWarn = false;
  $: {
    const fuel = $config?.fuel ?? {};
    pitLaps  = fuel.tank_capacity_l && fuel.consumption_l_per_lap
      ? Math.floor(fuel.tank_capacity_l / fuel.consumption_l_per_lap) : 0;
    lapsLeft = pitLaps - ($ourBike?.last_pit ?? 0);
    fuelPct  = pitLaps > 0 ? ($ourBike?.last_pit ?? 0) / pitLaps : 0;
    fuelWarn = lapsLeft <= (fuel.safety_margin_laps ?? 1) + 2;
  }
</script>

<svelte:head><title>Stratégie — Race Engineer</title></svelte:head>

<div class="p-6 space-y-6">
  <h1 class="text-2xl font-bold tracking-tight">Stratégie</h1>

  <section>
    <p class="section-title">Gestion carburant</p>
    <div class="card p-5 space-y-4">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 text-center">
        <div>
          <div class="metric-label">Capacité</div>
          <div class="text-2xl font-bold">{$config?.fuel?.tank_capacity_l ?? '—'}<span class="text-sm font-normal text-f1-muted ml-1">L</span></div>
        </div>
        <div>
          <div class="metric-label">Conso/tour</div>
          <div class="text-2xl font-bold">{$config?.fuel?.consumption_l_per_lap ?? '—'}<span class="text-sm font-normal text-f1-muted ml-1">L</span></div>
        </div>
        <div>
          <div class="metric-label">Tours max/relais</div>
          <div class="text-2xl font-bold text-f1-gold">{pitLaps || '—'}</div>
        </div>
        <div>
          <div class="metric-label">Tours restants</div>
          <div class="text-2xl font-bold {fuelWarn ? 'text-f1-red' : 'text-f1-green'}">{lapsLeft}</div>
        </div>
      </div>

      <div>
        <div class="flex justify-between text-xs text-f1-muted mb-1">
          <span>Carburant consommé</span>
          <span class="{fuelWarn ? 'text-f1-red font-bold' : ''}">{(fuelPct*100).toFixed(0)}%{fuelWarn ? ' ⚠ PIT WINDOW' : ''}</span>
        </div>
        <div class="progress-bar">
          <div class="h-full rounded-full transition-all duration-500 {fuelWarn ? 'bg-f1-red' : 'bg-f1-gold'}"
            style="width:{Math.min(fuelPct*100,100)}%"></div>
        </div>
      </div>
    </div>
  </section>

  {#if $simState?.elapsed > 0}
    <section>
      <p class="section-title">Course simulée</p>
      <div class="card p-5">
        <div class="flex items-center justify-between">
          <div>
            <div class="metric-label">Temps écoulé</div>
            <div class="text-3xl font-bold font-mono text-f1-gold">{fmtTime($simState.elapsed)}</div>
          </div>
          <div>
            <div class="metric-label">Restant</div>
            <div class="text-3xl font-bold font-mono">{fmtTime(Math.max(($simState.duration||1440)-$simState.elapsed,0))}</div>
          </div>
          <div>
            <div class="metric-label">Vitesse sim.</div>
            <div class="text-3xl font-bold">{$simState.speed}×</div>
          </div>
        </div>
        <div class="mt-4 progress-bar">
          <div class="progress-bar-fill" style="width:{Math.min($simState.elapsed/($simState.duration||1440)*100,100)}%"></div>
        </div>
      </div>
    </section>
  {/if}

  <section>
    <p class="section-title">Pneus</p>
    <div class="card p-5 text-f1-muted text-sm">
      Le suivi des pneus est en saisie manuelle. Configurez dans <a href="/settings" class="text-f1-gold hover:underline">Paramètres</a>.
    </div>
  </section>
</div>
