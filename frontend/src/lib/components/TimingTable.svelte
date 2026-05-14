<script>
  import { config } from '$lib/stores.js';

  export let rows = [];
  export let ourNumber = '96';
  export let highlight = true;

  const cols = [
    { key: 'position', label: 'Pos', class: 'w-10 text-center font-bold' },
    { key: 'numero',   label: 'N°',  class: 'w-12 text-f1-gold font-bold' },
    { key: 'categorie',label: 'Cat', class: 'w-12 text-f1-muted' },
    { key: 'team',     label: 'Équipe', class: 'max-w-[160px] truncate' },
    { key: 'rider',    label: 'Pilote', class: 'text-f1-sub' },
    { key: 'laps',     label: 'Tours', class: 'w-14 text-right font-mono' },
    { key: 'l_lap',    label: 'Der. tour', class: 'w-24 text-right font-mono' },
    { key: 'best_lap', label: 'Meilleur', class: 'w-24 text-right font-mono text-f1-purple' },
    { key: 'last_pit', label: '↺ pit', class: 'w-14 text-right font-mono text-f1-muted' },
    { key: 'total_pit',label: 'Arrêts', class: 'w-14 text-right font-mono' },
  ];

  // Pilote actif pour notre moto : un pilote par relais, on cycle dans la liste
  // des pilotes actifs configurés selon le nombre d'arrêts au stand.
  $: activePilots = ($config?.pilots ?? []).filter(p => p.active);
  function ourRider(row) {
    if (!activePilots.length) return row.rider ?? '—';
    const idx = (Number(row.total_pit) || 0) % activePilots.length;
    return activePilots[idx]?.name ?? row.rider ?? '—';
  }
</script>

<div class="overflow-x-auto">
  <table class="timing-table">
    <thead>
      <tr>
        {#each cols as col}
          <th class={col.class}>{col.label}</th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each rows as row (row.numero)}
        {@const isOurs = highlight && String(row.numero) === String(ourNumber)}
        {@const isPitIn  = row.pit_state === 'PIT_IN'}
        {@const isPitOut = row.pit_state === 'PIT_OUT'}
        <tr class="{isOurs ? 'our-bike' : ''} {isPitIn ? 'pit-in' : ''} {isPitOut ? 'pit-out' : ''}">
          {#each cols as col}
            <td class={col.class}>
              {#if col.key === 'numero'}
                <span class="{isOurs ? 'text-f1-gold' : ''} font-bold">{row[col.key] ?? '—'}</span>
              {:else if col.key === 'l_lap'}
                <span class="{isPitIn ? 'text-f1-red' : isPitOut ? 'text-f1-green' : ''}">
                  {row[col.key] ?? (isPitIn ? 'PIT IN' : isPitOut ? 'PIT OUT' : '—')}
                </span>
              {:else if col.key === 'rider'}
                <span class="{isOurs ? 'text-f1-gold font-semibold' : ''}">
                  {isOurs ? ourRider(row) : (row[col.key] ?? '—')}
                </span>
              {:else}
                {row[col.key] ?? '—'}
              {/if}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
