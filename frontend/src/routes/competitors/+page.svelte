<script>
  import { competitors, config } from '$lib/stores.js';
</script>

<svelte:head><title>Concurrents — Race Engineer</title></svelte:head>

<div class="p-6 space-y-4">
  <h1 class="text-2xl font-bold tracking-tight">Concurrents · {$config?.our_category ?? ''}</h1>

  {#if $competitors.length === 0}
    <div class="card p-8 text-center text-f1-muted">Aucun concurrent — lancez le simulateur.</div>
  {:else}
    <div class="card overflow-hidden">
      <table class="timing-table">
        <thead><tr>
          <th>Pos</th><th>N°</th><th>Équipe</th><th>Pilote</th>
          <th class="text-right">Tours</th>
          <th class="text-right">Der. tour</th>
          <th class="text-right">Meilleur</th>
          <th class="text-right">↺ pit</th>
          <th class="text-right">Arrêts</th>
          <th class="text-right">Tps stand</th>
        </tr></thead>
        <tbody>
          {#each $competitors as r (r.numero)}
            <tr class="{r.pit_state === 'PIT_IN' ? 'pit-in' : r.pit_state === 'PIT_OUT' ? 'pit-out' : ''}">
              <td class="text-center font-bold">{r.position ?? '—'}</td>
              <td class="font-bold text-f1-sub">{r.numero}</td>
              <td class="truncate max-w-[180px]">{r.team ?? '—'}</td>
              <td class="text-f1-sub truncate max-w-[120px]">{r.rider ?? '—'}</td>
              <td class="text-right font-mono">{r.laps ?? '—'}</td>
              <td class="text-right font-mono">{r.l_lap ?? '—'}</td>
              <td class="text-right font-mono text-f1-green">{r.best_lap ?? '—'}</td>
              <td class="text-right font-mono text-f1-muted">{r.last_pit ?? '—'}</td>
              <td class="text-right font-mono">{r.total_pit ?? '—'}</td>
              <td class="text-right font-mono text-f1-muted">{r.last_pit_time ?? '—'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
