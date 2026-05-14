<script>
  import { snapshot, config } from '$lib/stores.js';
  import TimingTable from '$lib/components/TimingTable.svelte';

  let catFilter = 'ALL';

  $: allRows  = $snapshot?.rows ?? [];
  $: cats     = ['ALL', ...new Set(allRows.map(r => r.categorie).filter(Boolean))];
  $: filtered = catFilter === 'ALL' ? allRows : allRows.filter(r => r.categorie === catFilter);
  $: fetchedAt = $snapshot?.fetched_at?.replace('T',' ').slice(0,19) + ' UTC';
</script>

<svelte:head><title>Live Timing — Race Engineer</title></svelte:head>

<div class="p-6 space-y-4">
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-bold tracking-tight">Live Timing</h1>
    <div class="flex items-center gap-4">
      <div class="flex gap-1">
        {#each cats as cat}
          <button class="btn-ghost text-xs px-3 py-1.5 {catFilter===cat ? '!border-f1-gold !text-f1-gold' : ''}"
                  onclick={() => catFilter = cat}>{cat}</button>
        {/each}
      </div>
      {#if $snapshot}
        <span class="text-xs text-f1-muted font-mono">{fetchedAt}</span>
      {/if}
    </div>
  </div>

  {#if filtered.length === 0}
    <div class="card p-8 text-center text-f1-muted">
      Aucune donnée live. Lancez le <a href="/simulator" class="text-f1-gold hover:underline">simulateur</a>.
    </div>
  {:else}
    <div class="card overflow-hidden">
      <TimingTable rows={filtered} ourNumber={$config?.our_bike_number ?? '96'} />
    </div>
    <p class="text-xs text-f1-muted text-right">{filtered.length} motos · mise à jour en temps réel via SSE</p>
  {/if}
</div>
