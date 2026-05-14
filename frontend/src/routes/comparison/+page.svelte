<script>
  import { onMount } from 'svelte';
  import { snapshot, config } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { gainClass, gainSign } from '$lib/utils.js';

  let relays96 = [];
  let relaysOther = [];
  let selected = '';

  $: num    = $config?.our_bike_number ?? '96';
  $: cat    = $config?.our_category ?? 'PRD';
  $: others = ($snapshot?.rows ?? []).filter(r => r.categorie === cat && String(r.numero) !== String(num));

  $: comparison = relays96.map((r96, i) => {
    const ro = relaysOther[i];
    if (!ro) return null;
    return {
      relais: r96.relais,
      tours96: r96.tours_relais,
      toursOther: ro.tours_relais,
      stand96: r96.last_pit_seconds,
      standOther: ro.last_pit_seconds,
      deltaStand: ro.last_pit_seconds != null && r96.last_pit_seconds != null
        ? ro.last_pit_seconds - r96.last_pit_seconds : null,
    };
  }).filter(Boolean);

  onMount(async () => { try { relays96 = await api.relays(num); } catch {} });

  async function loadOther(n) {
    selected = n;
    try { relaysOther = await api.relays(n); } catch { relaysOther = []; }
  }
</script>

<svelte:head><title>Comparatif — Race Engineer</title></svelte:head>

<div class="p-6 space-y-4">
  <h1 class="text-2xl font-bold tracking-tight">Comparatif relais</h1>

  <div class="flex flex-wrap gap-2 items-center">
    <span class="text-f1-muted text-sm">Concurrent :</span>
    {#each others as r}
      <button class="btn-ghost text-xs px-3 py-1.5
        {selected === String(r.numero) ? '!border-f1-gold !text-f1-gold' : ''}"
        onclick={() => loadOther(String(r.numero))}>
        n°{r.numero} · {r.team}
      </button>
    {/each}
  </div>

  {#if !selected}
    <div class="card p-8 text-center text-f1-muted">Sélectionnez un concurrent ci-dessus.</div>
  {:else if comparison.length === 0}
    <div class="card p-8 text-center text-f1-muted">Pas encore assez de relais pour comparer.</div>
  {:else}
    <div class="card overflow-hidden">
      <table class="timing-table">
        <thead><tr>
          <th>Relais</th>
          <th class="text-right">Tours n°{num}</th>
          <th class="text-right">Tours n°{selected}</th>
          <th class="text-right">Stand n°{num}</th>
          <th class="text-right">Stand n°{selected}</th>
          <th class="text-right">Δ stand</th>
        </tr></thead>
        <tbody>
          {#each comparison as c}
            <tr>
              <td class="font-bold text-f1-gold">R{c.relais}</td>
              <td class="text-right font-mono">{c.tours96}</td>
              <td class="text-right font-mono">{c.toursOther}</td>
              <td class="text-right font-mono">{c.stand96?.toFixed(1) ?? '—'}s</td>
              <td class="text-right font-mono">{c.standOther?.toFixed(1) ?? '—'}s</td>
              <td class="text-right font-mono {gainClass(c.deltaStand)}">{gainSign(c.deltaStand)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
