<script>
  import { ourBike, config } from '$lib/stores.js';
  import { consumables, resetPart, setMaxLaps } from '$lib/consumables.js';

  let currentLap   = 0;
  let lastPitLaps  = 0;
  let bikeNum      = '96';
  let ft_used = 0, rt_used = 0, fb_used = 0;
  let ft_pct  = 0, rt_pct  = 0, fb_pct  = 0;
  let ft_max  = 60, rt_max = 45, fb_max = 120;
  let ft_color = '#00d787', rt_color = '#00d787', fb_color = '#00d787';
  let fuel_color = '#00d787';
  let tankCap = 16, consLap = 0.95;
  let fuelUsedL = 0, fuelLeftL = 16, fuel_pct = 0;

  // Un seul bloc réactif qui dépend directement des stores — pas de chaînage $:
  $: {
    const b = $ourBike;
    const c = $config;
    const cons = $consumables;

    currentLap  = Number(b?.laps) || 0;
    lastPitLaps = Number(b?.last_pit) || 0;
    bikeNum     = c?.our_bike_number ?? '96';

    const ft_inst = Number(cons?.front_tire?.installed_at_lap)  || 0;
    const rt_inst = Number(cons?.rear_tire?.installed_at_lap)   || 0;
    const fb_inst = Number(cons?.front_brake?.installed_at_lap) || 0;

    ft_max = Number(cons?.front_tire?.max_laps)  || 60;
    rt_max = Number(cons?.rear_tire?.max_laps)   || 45;
    fb_max = Number(cons?.front_brake?.max_laps) || 120;

    ft_used = Math.max(currentLap - ft_inst, 0);
    rt_used = Math.max(currentLap - rt_inst, 0);
    fb_used = Math.max(currentLap - fb_inst, 0);

    ft_pct = clamp01(ft_used / ft_max);
    rt_pct = clamp01(rt_used / rt_max);
    fb_pct = clamp01(fb_used / fb_max);

    ft_color = colorFor(ft_pct);
    rt_color = colorFor(rt_pct);
    fb_color = colorFor(fb_pct);

    tankCap   = Number(c?.fuel?.tank_capacity_l)      || 16;
    consLap   = Number(c?.fuel?.consumption_l_per_lap) || 0.95;
    fuelUsedL = lastPitLaps * consLap;
    fuelLeftL = Math.max(tankCap - fuelUsedL, 0);
    fuel_pct  = clamp01(fuelUsedL / tankCap);
    fuel_color = colorFor(fuel_pct);
  }

  function clamp01(v) { return Math.min(Math.max(v, 0), 1); }
  function colorFor(p) {
    if (p >= 0.9)  return '#e8001a';
    if (p >= 0.75) return '#ff7a00';
    if (p >= 0.5)  return '#e8b800';
    return '#00d787';
  }

  function resetAll() {
    if (!confirm('Réinitialiser tous les consommables à 0 ?')) return;
    resetPart('front_tire',  0);
    resetPart('rear_tire',   0);
    resetPart('front_brake', 0);
  }

  const C = 2 * Math.PI * 22; // circonférence de l'arc (r=22)
</script>

<section class="space-y-4">
  <div class="flex items-center justify-between">
    <p class="section-title mb-0">YAMAHA YZF-R1 · WEC · n°{bikeNum}</p>
    <button class="text-xs text-f1-muted hover:text-f1-gold" onclick={resetAll}>↺ Reset consommables</button>
  </div>

  <div class="card overflow-hidden bg-gradient-to-b from-[#0c0c14] to-[#050508] p-4">
    <div class="relative w-full">
      <img src="/r1-bike.png" alt="Yamaha YZF-R1 Thorn / Bardahl" class="w-full h-auto block" />

      <!-- ESSENCE — haut-centre, label AU-DESSUS de la jauge -->
      <div class="absolute" style="left: 50%; top: 3%; transform: translateX(-50%);">
        <div class="flex flex-col items-center gap-1">
          <span class="text-xs font-bold uppercase tracking-widest px-2.5 py-1 rounded bg-black/85 text-white border border-white/10">Essence</span>
          <svg viewBox="0 0 50 50" class="w-24 h-24 drop-shadow-[0_3px_6px_rgba(0,0,0,0.9)]">
            <circle cx="25" cy="25" r="22" fill="rgba(0,0,0,0.82)" stroke="#222" stroke-width="1"/>
            <circle cx="25" cy="25" r="22" fill="none" stroke="#2a2a2a" stroke-width="4"/>
            <circle cx="25" cy="25" r="22" fill="none" stroke={fuel_color} stroke-width="4"
                    stroke-dasharray="{(1-fuel_pct)*C} {C}" stroke-linecap="round"
                    transform="rotate(-90 25 25)" style="transition:stroke-dasharray .3s linear, stroke .3s"/>
            <text x="25" y="20" font-size="8" fill="#fff" text-anchor="middle">⛽</text>
            <text x="25" y="32" font-size="11" fill={fuel_color} text-anchor="middle" font-weight="900" font-family="JetBrains Mono,monospace">{fuelLeftL.toFixed(1)}</text>
            <text x="25" y="40" font-size="6"  fill="#aaa" text-anchor="middle" font-family="JetBrains Mono,monospace">/{tankCap.toFixed(0)} L</text>
          </svg>
        </div>
      </div>

      <!-- PNEU ARRIÈRE — gauche, centré verticalement sur l'image -->
      <div class="absolute" style="left: 4%; top: 50%; transform: translateY(-50%);">
        <div class="flex flex-col items-center gap-1">
          <svg viewBox="0 0 50 50" class="w-24 h-24 drop-shadow-[0_3px_6px_rgba(0,0,0,0.9)]">
            <circle cx="25" cy="25" r="22" fill="rgba(0,0,0,0.85)" stroke="#222" stroke-width="1"/>
            <circle cx="25" cy="25" r="22" fill="none" stroke="#2a2a2a" stroke-width="4"/>
            <circle cx="25" cy="25" r="22" fill="none" stroke={rt_color} stroke-width="4"
                    stroke-dasharray="{rt_pct*C} {C}" stroke-linecap="round"
                    transform="rotate(-90 25 25)" style="transition:stroke-dasharray .3s linear, stroke .3s"/>
            <text x="25" y="22" font-size="13" fill="#fff" text-anchor="middle" font-weight="900" font-family="JetBrains Mono,monospace">{rt_used}</text>
            <text x="25" y="34" font-size="7"  fill={rt_color} text-anchor="middle" font-weight="bold" font-family="JetBrains Mono,monospace">/ {rt_max}</text>
            <text x="25" y="41" font-size="5"  fill="#aaa" text-anchor="middle" font-family="sans-serif">{(rt_pct*100).toFixed(0)}%</text>
          </svg>
          <span class="text-xs font-bold uppercase tracking-widest px-2.5 py-1 rounded bg-black/85 text-white border border-white/10">Pneu AR</span>
        </div>
      </div>

      <!-- PNEU AVANT — droite, centré verticalement -->
      <div class="absolute" style="right: 2%; top: 50%; transform: translateY(-50%);">
        <div class="flex flex-col items-center gap-1">
          <svg viewBox="0 0 50 50" class="w-24 h-24 drop-shadow-[0_3px_6px_rgba(0,0,0,0.9)]">
            <circle cx="25" cy="25" r="22" fill="rgba(0,0,0,0.85)" stroke="#222" stroke-width="1"/>
            <circle cx="25" cy="25" r="22" fill="none" stroke="#2a2a2a" stroke-width="4"/>
            <circle cx="25" cy="25" r="22" fill="none" stroke={ft_color} stroke-width="4"
                    stroke-dasharray="{ft_pct*C} {C}" stroke-linecap="round"
                    transform="rotate(-90 25 25)" style="transition:stroke-dasharray .3s linear, stroke .3s"/>
            <text x="25" y="22" font-size="13" fill="#fff" text-anchor="middle" font-weight="900" font-family="JetBrains Mono,monospace">{ft_used}</text>
            <text x="25" y="34" font-size="7"  fill={ft_color} text-anchor="middle" font-weight="bold" font-family="JetBrains Mono,monospace">/ {ft_max}</text>
            <text x="25" y="41" font-size="5"  fill="#aaa" text-anchor="middle" font-family="sans-serif">{(ft_pct*100).toFixed(0)}%</text>
          </svg>
          <span class="text-xs font-bold uppercase tracking-widest px-2.5 py-1 rounded bg-black/85 text-white border border-white/10">Pneu AV</span>
        </div>
      </div>

      <!-- PLAQUETTES AV — droite, en bas -->
      <div class="absolute" style="right: 22%; bottom: 4%;">
        <div class="flex flex-col items-center gap-1">
          <svg viewBox="0 0 50 50" class="w-24 h-24 drop-shadow-[0_3px_6px_rgba(0,0,0,0.9)]">
            <circle cx="25" cy="25" r="22" fill="rgba(0,0,0,0.85)" stroke="#222" stroke-width="1"/>
            <circle cx="25" cy="25" r="22" fill="none" stroke="#2a2a2a" stroke-width="4"/>
            <circle cx="25" cy="25" r="22" fill="none" stroke={fb_color} stroke-width="4"
                    stroke-dasharray="{fb_pct*C} {C}" stroke-linecap="round"
                    transform="rotate(-90 25 25)" style="transition:stroke-dasharray .3s linear, stroke .3s"/>
            <text x="25" y="22" font-size="13" fill="#fff" text-anchor="middle" font-weight="900" font-family="JetBrains Mono,monospace">{fb_used}</text>
            <text x="25" y="34" font-size="7"  fill={fb_color} text-anchor="middle" font-weight="bold" font-family="JetBrains Mono,monospace">/ {fb_max}</text>
            <text x="25" y="41" font-size="5"  fill="#aaa" text-anchor="middle" font-family="sans-serif">{(fb_pct*100).toFixed(0)}%</text>
          </svg>
          <span class="text-xs font-bold uppercase tracking-widest px-2.5 py-1 rounded bg-black/85 text-white border border-white/10">Plaq. AV</span>
        </div>
      </div>

      <!-- Numéro de course -->
      <div class="absolute" style="left: 1%; top: 1%;">
        <div class="bg-f1-gold text-black font-black text-2xl px-3 py-1 rounded shadow-lg" style="font-family:'JetBrains Mono',monospace">
          #{bikeNum}
        </div>
      </div>
    </div>
  </div>

  <!-- Cartes détaillées -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
    <div class="card p-4 space-y-2 border-l-2" style="border-left-color:{ft_color}">
      <div class="flex items-center justify-between">
        <span class="text-xs uppercase tracking-widest text-f1-muted">Pneu avant</span>
        <button class="text-xs text-f1-gold hover:underline" onclick={() => resetPart('front_tire', currentLap)}>↺ neuf</button>
      </div>
      <div class="text-2xl font-bold font-mono" style="color:{ft_color}">{ft_used} <span class="text-sm text-f1-muted">/ {ft_max} tours</span></div>
      <div class="progress-bar"><div class="h-full rounded-full transition-all" style="width:{ft_pct*100}%; background:{ft_color}"></div></div>
      <div class="flex items-center justify-between text-xs">
        <span class="text-f1-muted">{(ft_pct*100).toFixed(0)}% usé</span>
        <label class="flex items-center gap-1 text-f1-muted">
          max
          <input type="number" min="1" class="w-12 bg-f1-bg border border-f1-border rounded-sm px-1 py-0.5 text-xs font-mono text-right"
                 value={ft_max}
                 onchange={(e) => setMaxLaps('front_tire', e.target.value)} />
        </label>
      </div>
    </div>

    <div class="card p-4 space-y-2 border-l-2" style="border-left-color:{rt_color}">
      <div class="flex items-center justify-between">
        <span class="text-xs uppercase tracking-widest text-f1-muted">Pneu arrière</span>
        <button class="text-xs text-f1-gold hover:underline" onclick={() => resetPart('rear_tire', currentLap)}>↺ neuf</button>
      </div>
      <div class="text-2xl font-bold font-mono" style="color:{rt_color}">{rt_used} <span class="text-sm text-f1-muted">/ {rt_max} tours</span></div>
      <div class="progress-bar"><div class="h-full rounded-full transition-all" style="width:{rt_pct*100}%; background:{rt_color}"></div></div>
      <div class="flex items-center justify-between text-xs">
        <span class="text-f1-muted">{(rt_pct*100).toFixed(0)}% usé</span>
        <label class="flex items-center gap-1 text-f1-muted">
          max
          <input type="number" min="1" class="w-12 bg-f1-bg border border-f1-border rounded-sm px-1 py-0.5 text-xs font-mono text-right"
                 value={rt_max}
                 onchange={(e) => setMaxLaps('rear_tire', e.target.value)} />
        </label>
      </div>
    </div>

    <div class="card p-4 space-y-2 border-l-2" style="border-left-color:{fuel_color}">
      <div class="flex items-center justify-between">
        <span class="text-xs uppercase tracking-widest text-f1-muted">Essence</span>
        <span class="text-xs text-f1-muted font-mono">{(fuel_pct*100).toFixed(0)}% consommé</span>
      </div>
      <div class="text-2xl font-bold font-mono" style="color:{fuel_color}">{fuelLeftL.toFixed(1)} <span class="text-sm text-f1-muted">/ {tankCap.toFixed(1)} L</span></div>
      <div class="progress-bar"><div class="h-full rounded-full transition-all" style="width:{(1-fuel_pct)*100}%; background:{fuel_color}"></div></div>
      <div class="text-xs text-f1-muted">{lastPitLaps} tours dep. stand · {consLap.toFixed(2)} L/tour</div>
    </div>

    <div class="card p-4 space-y-2 border-l-2" style="border-left-color:{fb_color}">
      <div class="flex items-center justify-between">
        <span class="text-xs uppercase tracking-widest text-f1-muted">Plaquettes AV</span>
        <button class="text-xs text-f1-gold hover:underline" onclick={() => resetPart('front_brake', currentLap)}>↺ neuves</button>
      </div>
      <div class="text-2xl font-bold font-mono" style="color:{fb_color}">{fb_used} <span class="text-sm text-f1-muted">/ {fb_max} tours</span></div>
      <div class="progress-bar"><div class="h-full rounded-full transition-all" style="width:{fb_pct*100}%; background:{fb_color}"></div></div>
      <div class="flex items-center justify-between text-xs">
        <span class="text-f1-muted">{(fb_pct*100).toFixed(0)}% usées</span>
        <label class="flex items-center gap-1 text-f1-muted">
          max
          <input type="number" min="1" class="w-12 bg-f1-bg border border-f1-border rounded-sm px-1 py-0.5 text-xs font-mono text-right"
                 value={fb_max}
                 onchange={(e) => setMaxLaps('front_brake', e.target.value)} />
        </label>
      </div>
    </div>
  </div>
</section>
