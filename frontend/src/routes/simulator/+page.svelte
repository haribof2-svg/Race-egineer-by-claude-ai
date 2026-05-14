<script>
  import { api } from '$lib/api.js';
  import { simState, snapshot } from '$lib/stores.js';

  const DURATIONS = [
    { label: '2 h',  value: 120  },
    { label: '4 h',  value: 240  },
    { label: '6 h',  value: 360  },
    { label: '8 h',  value: 480  },
    { label: '12 h', value: 720  },
    { label: '24 h', value: 1440 },
    { label: '48 h', value: 2880 },
  ];
  const SPEEDS = [0.5, 1, 2, 5, 10, 30, 60];

  let duration = $state(1440);
  let speedIndex = $state(1);
  let loading = $state(false);
  let sim = $state({ running: false, elapsed: 0, speed: 1, duration: 1440 });

  let actualSpeed = $derived(SPEEDS[speedIndex] ?? 1);
  let elapsed    = $derived(sim?.elapsed ?? 0);
  let dur        = $derived(sim?.duration ?? duration);
  let pct        = $derived(Math.min(elapsed / (dur || 1440), 1));
  let rows       = $derived($snapshot?.rows ?? []);

  function fmtTime(minutes) {
    const total = Math.floor((minutes ?? 0) * 60);
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = total % 60;
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  }

  async function refresh() {
    try {
      const s = await api.simState();
      sim = s;
      simState.set(s);
    } catch {}
  }

  $effect(() => {
    refresh();
    const iv = setInterval(refresh, 1000);
    return () => clearInterval(iv);
  });

  async function start() {
    loading = true;
    try {
      const s = await api.simStart(actualSpeed, duration);
      sim = s;
      simState.set(s);
    } finally { loading = false; }
  }

  async function pause() {
    loading = true;
    try {
      const s = await api.simPause();
      sim = s;
      simState.set(s);
    } finally { loading = false; }
  }

  async function reset() {
    loading = true;
    try {
      const s = await api.simReset();
      sim = s;
      simState.set(s);
      snapshot.set(null);
    } finally { loading = false; }
  }

  async function jump() {
    loading = true;
    try { await api.simJump(5); await refresh(); } finally { loading = false; }
  }

  async function changeSpeed() {
    if (sim?.running) {
      try { await api.simSpeed(actualSpeed); } catch {}
    }
  }
</script>

<svelte:head><title>Simulateur — Race Engineer</title></svelte:head>

<div class="p-6 space-y-6 max-w-3xl">

  <div>
    <h1 class="text-2xl font-bold tracking-tight">Simulateur</h1>
    <p class="text-xs text-f1-sub mt-1">Génère un flux fictif pour tester toutes les pages en temps réel.</p>
  </div>

  <!-- Durée de course -->
  <section class="space-y-2">
    <p class="section-title">Durée de course</p>
    <div class="flex flex-wrap gap-2">
      {#each DURATIONS as d}
        <button
          class="btn-ghost text-sm px-4 py-2
            {duration === d.value && !sim?.running && elapsed === 0 ? '!border-f1-gold !text-f1-gold' : ''}
            {sim?.running || elapsed > 0 ? 'opacity-40 cursor-not-allowed' : ''}"
          disabled={sim?.running || elapsed > 0}
          onclick={() => duration = d.value}>
          {d.label}
        </button>
      {/each}
    </div>
  </section>

  <!-- Curseur de vitesse -->
  <section class="space-y-3">
    <div class="flex items-center justify-between">
      <p class="section-title mb-0">Vitesse d'écoulement</p>
      <span class="text-f1-gold font-bold font-mono text-lg">{actualSpeed}×</span>
    </div>

    <input
      type="range"
      min="0"
      max={SPEEDS.length - 1}
      step="1"
      bind:value={speedIndex}
      onchange={changeSpeed}
      class="w-full accent-f1-gold cursor-pointer" />

    <div class="flex justify-between text-xs text-f1-muted font-mono">
      {#each SPEEDS as s}
        <span class="{actualSpeed === s ? 'text-f1-gold font-bold' : ''}">{s}×</span>
      {/each}
    </div>

    <p class="text-xs text-f1-muted">
      {actualSpeed}× → {actualSpeed * 60} min simulées / min réelle
    </p>
  </section>

  <!-- Boutons de contrôle -->
  <div class="flex gap-3 flex-wrap">
    {#if sim?.running}
      <button class="btn-primary" onclick={pause} disabled={loading}>⏸ Pause</button>
    {:else}
      <button class="btn-primary" onclick={start} disabled={loading || elapsed >= dur}>
        ▶ Démarrer
      </button>
    {/if}
    <button class="btn-ghost" onclick={jump} disabled={loading || sim?.running}>⏭ +5 min</button>
    <button class="btn-danger" onclick={reset} disabled={loading}>↺ Reset</button>
  </div>

  <!-- Chrono + progression -->
  <section class="card p-5 space-y-4">
    <div class="grid grid-cols-3 gap-4 text-center">
      <div>
        <div class="text-f1-muted text-xs uppercase tracking-widest mb-1">Chrono</div>
        <div class="text-3xl font-bold font-mono text-f1-gold">{fmtTime(elapsed)}</div>
      </div>
      <div>
        <div class="text-f1-muted text-xs uppercase tracking-widest mb-1">Restant</div>
        <div class="text-3xl font-bold font-mono">{fmtTime(Math.max(dur - elapsed, 0))}</div>
      </div>
      <div>
        <div class="text-f1-muted text-xs uppercase tracking-widest mb-1">État</div>
        <div class="text-3xl font-bold
          {sim?.running ? 'text-f1-green' : elapsed > 0 ? 'text-f1-sub' : 'text-f1-muted'}">
          {#if elapsed >= dur && elapsed > 0}🏁
          {:else if sim?.running}▶
          {:else if elapsed > 0}⏸
          {:else}■{/if}
        </div>
      </div>
    </div>

    <div>
      <div class="progress-bar">
        <div class="progress-bar-fill" style="width:{pct * 100}%"></div>
      </div>
      <div class="flex justify-between text-xs text-f1-muted mt-1 font-mono">
        <span>{fmtTime(elapsed)}</span>
        <span>{(pct * 100).toFixed(1)}%</span>
        <span>{fmtTime(dur)}</span>
      </div>
    </div>
  </section>

  <!-- Tableau snapshot courant -->
  {#if rows.length > 0}
    <section>
      <p class="section-title">Dernier snapshot — {rows.length} motos</p>
      <div class="card overflow-hidden">
        <table class="timing-table">
          <thead>
            <tr>
              <th>N°</th><th>Cat.</th><th>Équipe</th>
              <th class="text-right">Tours</th>
              <th class="text-right">Der. tour</th>
              <th class="text-right">Arrêts</th>
            </tr>
          </thead>
          <tbody>
            {#each rows as r (r.numero)}
              {@const isOurs = String(r.numero) === '96'}
              <tr class="{isOurs ? 'our-bike' : ''}">
                <td class="font-bold {isOurs ? 'text-f1-gold' : ''}">{r.numero}</td>
                <td class="text-f1-muted">{r.categorie}</td>
                <td class="truncate max-w-[180px]">{r.team}</td>
                <td class="text-right font-mono">{r.laps}</td>
                <td class="text-right font-mono">{r.l_lap}</td>
                <td class="text-right font-mono">{r.total_pit}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  {:else}
    <div class="card p-6 text-center text-f1-muted text-sm">
      {#if elapsed === 0}
        Appuyez sur <strong class="text-f1-text">▶ Démarrer</strong>
        ou <strong class="text-f1-text">⏭ +5 min</strong> pour générer les premières données.
      {:else}
        En attente du prochain snapshot…
      {/if}
    </div>
  {/if}

</div>
