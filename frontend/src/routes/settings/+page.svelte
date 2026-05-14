<script>
  import { config } from '$lib/stores.js';
  import { api } from '$lib/api.js';

  let cfg = null;
  let saved = false;

  // Initialise cfg dès que $config est dispo (une seule fois)
  $: if ($config && cfg === null) cfg = JSON.parse(JSON.stringify($config));

  async function save() {
    try {
      await api.saveConfig(cfg);
      config.set(JSON.parse(JSON.stringify(cfg)));
      saved = true;
      setTimeout(() => saved = false, 2000);
    } catch (e) {
      console.error('Erreur sauvegarde:', e);
    }
  }
</script>

<svelte:head><title>Paramètres — Race Engineer</title></svelte:head>

<div class="p-6 space-y-6 max-w-2xl">
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-bold tracking-tight">Paramètres</h1>
    {#if cfg}
      <button class="btn-primary" onclick={save}>
        {saved ? '✓ Sauvegardé' : 'Sauvegarder'}
      </button>
    {/if}
  </div>

  {#if !cfg}
    <div class="card p-8 text-center text-f1-muted">Connexion au serveur…</div>
  {:else}
    <!-- Équipe -->
    <section class="card p-5 space-y-4">
      <p class="section-title">Équipe</p>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-f1-muted uppercase tracking-widest block mb-1">Nom équipe</label>
          <input class="w-full bg-f1-bg border border-f1-border rounded-sm px-3 py-2 text-sm focus:border-f1-gold outline-none"
            bind:value={cfg.team_name} />
        </div>
        <div>
          <label class="text-xs text-f1-muted uppercase tracking-widest block mb-1">N° moto</label>
          <input class="w-full bg-f1-bg border border-f1-border rounded-sm px-3 py-2 text-sm focus:border-f1-gold outline-none"
            bind:value={cfg.our_bike_number} />
        </div>
        <div>
          <label class="text-xs text-f1-muted uppercase tracking-widest block mb-1">Catégorie</label>
          <input class="w-full bg-f1-bg border border-f1-border rounded-sm px-3 py-2 text-sm focus:border-f1-gold outline-none"
            bind:value={cfg.our_category} />
        </div>
        <div>
          <label class="text-xs text-f1-muted uppercase tracking-widest block mb-1">URL live timing</label>
          <input class="w-full bg-f1-bg border border-f1-border rounded-sm px-3 py-2 text-sm font-mono focus:border-f1-gold outline-none"
            bind:value={cfg.live_url} />
        </div>
      </div>
    </section>

    <!-- Carburant -->
    <section class="card p-5 space-y-4">
      <p class="section-title">Carburant</p>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-f1-muted uppercase tracking-widest block mb-1">Capacité (L)</label>
          <input type="number" step="0.1" class="w-full bg-f1-bg border border-f1-border rounded-sm px-3 py-2 text-sm focus:border-f1-gold outline-none"
            bind:value={cfg.fuel.tank_capacity_l} />
        </div>
        <div>
          <label class="text-xs text-f1-muted uppercase tracking-widest block mb-1">Conso / tour (L)</label>
          <input type="number" step="0.1" class="w-full bg-f1-bg border border-f1-border rounded-sm px-3 py-2 text-sm focus:border-f1-gold outline-none"
            bind:value={cfg.fuel.consumption_l_per_lap} />
        </div>
      </div>
    </section>

    <!-- Pilotes -->
    <section class="card p-5 space-y-3">
      <p class="section-title">Pilotes</p>
      {#each cfg.pilots as pilot}
        <div class="flex items-center gap-3 py-2 border-b border-f1-border last:border-0">
          <input type="color" bind:value={pilot.color} class="w-8 h-8 rounded cursor-pointer border-0 bg-transparent" />
          <input class="flex-1 bg-f1-bg border border-f1-border rounded-sm px-3 py-1.5 text-sm focus:border-f1-gold outline-none"
            bind:value={pilot.name} placeholder="Nom pilote" />
          <label class="flex items-center gap-1.5 text-xs text-f1-sub cursor-pointer">
            <input type="checkbox" bind:checked={pilot.active} class="accent-f1-gold" />
            Actif
          </label>
        </div>
      {/each}
    </section>
  {/if}
</div>
