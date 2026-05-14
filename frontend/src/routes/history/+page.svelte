<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';

  let snapshots = [];
  let selected = null;
  let detail = null;
  let loading = false;

  onMount(async () => {
    try { snapshots = await api.history(200); } catch {}
  });

  async function loadDetail(id) {
    loading = true;
    selected = id;
    try { detail = await api.historyItem(id); } catch { detail = null; }
    loading = false;
  }

  async function clearAll() {
    if (!confirm('Effacer tout l\'historique ?')) return;
    await api.clearHistory();
    snapshots = []; detail = null; selected = null;
  }
</script>

<svelte:head><title>Historique — Race Engineer</title></svelte:head>

<div class="p-6 flex gap-4 h-full">
  <!-- Liste -->
  <div class="w-64 shrink-0 space-y-2">
    <div class="flex items-center justify-between mb-3">
      <h1 class="text-lg font-bold">Historique</h1>
      {#if snapshots.length > 0}
        <button class="btn-danger text-xs px-2 py-1" on:click={clearAll}>Effacer</button>
      {/if}
    </div>
    {#if snapshots.length === 0}
      <p class="text-f1-muted text-xs">Aucun snapshot enregistré.</p>
    {:else}
      <div class="space-y-1 overflow-y-auto max-h-[70vh]">
        {#each snapshots as s}
          <button class="w-full text-left card px-3 py-2 text-xs hover:border-f1-gold transition-colors
            {selected === s.id ? 'border-f1-gold bg-f1-gold/5' : ''}"
            on:click={() => loadDetail(s.id)}>
            <div class="font-mono text-f1-sub">{s.fetched_at?.replace('T',' ').slice(0,19)}</div>
            <div class="text-f1-muted">ID #{s.id}</div>
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Détail -->
  <div class="flex-1 overflow-y-auto">
    {#if loading}
      <div class="card p-8 text-center text-f1-muted">Chargement…</div>
    {:else if detail}
      <div class="space-y-3">
        <p class="section-title">Snapshot #{selected} · {detail.fetched_at?.replace('T',' ').slice(0,19)} UTC</p>
        <div class="card overflow-hidden">
          <table class="timing-table">
            <thead><tr>
              <th>Pos</th><th>N°</th><th>Équipe</th>
              <th class="text-right">Tours</th>
              <th class="text-right">Der. tour</th>
              <th class="text-right">Arrêts</th>
            </tr></thead>
            <tbody>
              {#each detail.rows ?? [] as r}
                <tr><td>{r.position??'—'}</td><td class="font-bold">{r.numero}</td>
                  <td class="truncate max-w-[200px]">{r.team??'—'}</td>
                  <td class="text-right font-mono">{r.laps??'—'}</td>
                  <td class="text-right font-mono">{r.l_lap??'—'}</td>
                  <td class="text-right font-mono">{r.total_pit??'—'}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {:else}
      <div class="card p-8 text-center text-f1-muted">Sélectionnez un snapshot à gauche.</div>
    {/if}
  </div>
</div>
