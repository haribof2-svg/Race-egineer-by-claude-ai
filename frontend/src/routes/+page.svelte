<script>
  import { snapshot, ourBike, config, simState } from '$lib/stores.js';
  import MetricCard from '$lib/components/MetricCard.svelte';
  import BikeR1 from '$lib/components/BikeR1.svelte';
  import { fmtTime } from '$lib/utils.js';

  let pitLaps = 0, lapsLeft = 0, fuelWarn = false;
  $: {
    const fuel = $config?.fuel ?? {};
    pitLaps  = fuel.tank_capacity_l && fuel.consumption_l_per_lap
      ? Math.floor(fuel.tank_capacity_l / fuel.consumption_l_per_lap) : 0;
    lapsLeft = pitLaps - ($ourBike?.last_pit ?? 0);
    fuelWarn = lapsLeft <= (fuel.safety_margin_laps ?? 1) + 2;
  }
</script>

<svelte:head><title>Dashboard — Race Engineer</title></svelte:head>

<div class="p-6 space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Dashboard</h1>
      {#if $simState?.running}
        <p class="text-xs text-f1-sub mt-0.5">Simulation · {fmtTime($simState.elapsed)} / {fmtTime($simState.duration)}</p>
      {/if}
    </div>
    {#if $snapshot}
      <span class="text-xs text-f1-muted font-mono">{$snapshot.fetched_at?.slice(11,19)} UTC</span>
    {/if}
  </div>

  {#if !$ourBike && ($snapshot?.rows ?? []).length === 0}
    <div class="card p-8 text-center text-f1-muted">
      <div class="text-4xl mb-3">🏁</div>
      <p class="font-semibold">Aucune donnée disponible</p>
      <p class="text-xs mt-1">Lancez le <a href="/simulator" class="text-f1-gold hover:underline">simulateur</a> ou configurez l'URL live dans les <a href="/settings" class="text-f1-gold hover:underline">paramètres</a>.</p>
    </div>
  {:else}
    {#if $ourBike}
      <BikeR1 />

      <section>
        <p class="section-title">Moto n°{$config?.our_bike_number} · {$config?.team_name}</p>
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard label="Position" value={$ourBike.position ?? '—'} accent="gold" />
          <MetricCard label="Tours" value={$ourBike.laps ?? '—'} />
          <MetricCard label="Dernier tour" value={$ourBike.l_lap ?? '—'} accent="green" />
          <MetricCard label="Meilleur tour" value={$ourBike.best_lap ?? '—'} accent="green" />
          <MetricCard label="Dep. stand (tours)" value={$ourBike.last_pit ?? '—'}
            accent={fuelWarn ? 'red' : 'gold'}
            delta={fuelWarn ? '⚠ PIT WINDOW' : null}
            deltaClass="text-f1-red" />
          <MetricCard label="Arrêts stand" value={$ourBike.total_pit ?? '—'} />
          <MetricCard label="Tps dernier arrêt" value={$ourBike.last_pit_time ?? '—'} />
          <MetricCard label="État" value={$ourBike.pit_state ?? 'EN PISTE'}
            accent={$ourBike.pit_state === 'PIT_IN' ? 'red' : $ourBike.pit_state === 'PIT_OUT' ? 'green' : 'gold'} />
        </div>
      </section>
    {/if}

    {#if ($snapshot?.rows ?? []).length > 0}
      <section>
        <p class="section-title">Classement — {$config?.our_category ?? 'Toutes catégories'}</p>
        <div class="card overflow-hidden">
          <table class="timing-table">
            <thead>
              <tr>
                <th class="w-10">Pos</th><th class="w-12">N°</th><th>Équipe</th>
                <th class="w-16 text-right">Tours</th><th class="w-24 text-right">Der. tour</th>
                <th class="w-14 text-right">↺ pit</th><th class="w-14 text-right">Arrêts</th>
              </tr>
            </thead>
            <tbody>
              {#each ($snapshot?.rows ?? []).filter(r => !$config || r.categorie === $config.our_category) as r (r.numero)}
                {@const isOurs = String(r.numero) === String($config?.our_bike_number)}
                <tr class="{isOurs ? 'our-bike' : ''} {r.pit_state === 'PIT_IN' ? 'pit-in' : ''} {r.pit_state === 'PIT_OUT' ? 'pit-out' : ''}">
                  <td class="text-center font-bold">{r.position ?? '—'}</td>
                  <td class="{isOurs ? 'text-f1-gold' : ''} font-bold">{r.numero}</td>
                  <td class="truncate max-w-[200px]">{r.team ?? '—'}</td>
                  <td class="text-right font-mono">{r.laps ?? '—'}</td>
                  <td class="text-right font-mono">{r.l_lap ?? '—'}</td>
                  <td class="text-right font-mono text-f1-muted">{r.last_pit ?? '—'}</td>
                  <td class="text-right font-mono">{r.total_pit ?? '—'}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </section>
    {/if}
  {/if}
</div>
