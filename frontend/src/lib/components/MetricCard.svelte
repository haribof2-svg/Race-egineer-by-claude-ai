<script>
  export let label = '';
  export let value = '—';
  export let delta = null;
  export let deltaClass = '';
  export let unit = '';
  export let accent = 'gold'; // 'gold' | 'green' | 'red'
</script>

<div class="card border-l-2 px-4 py-3 flex flex-col gap-0.5
  {accent === 'gold'  ? 'border-l-f1-gold'  :
   accent === 'green' ? 'border-l-f1-green' :
                        'border-l-f1-red'}">
  <div class="metric-label">{label}</div>
  <div class="metric-value">
    {value}{#if unit}<span class="text-sm font-normal text-f1-sub ml-1">{unit}</span>{/if}
  </div>
  {#if delta !== null}
    <div class="metric-delta {deltaClass}">{delta}</div>
  {/if}
</div>
