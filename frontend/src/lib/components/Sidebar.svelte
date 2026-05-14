<script>
  import { page } from '$app/stores';
  import { config, connected, simState } from '$lib/stores.js';

  const nav = [
    { href: '/',            icon: '▣',  label: 'Dashboard'      },
    { href: '/timing',      icon: '📡', label: 'Live Timing'    },
    { href: '/bike',        icon: '🏍', label: 'Notre moto'     },
    { href: '/pilots',      icon: '👤', label: 'Pilotes'        },
    { href: '/competitors', icon: '🏁', label: 'Concurrents'    },
    { href: '/comparison',  icon: '⚖', label: 'Comparatif'     },
    { href: '/strategy',    icon: '🧠', label: 'Stratégie'      },
    { href: '/history',     icon: '🕒', label: 'Historique'     },
    { href: '/simulator',   icon: '🎮', label: 'Simulateur'     },
    { href: '/settings',    icon: '⚙', label: 'Paramètres'     }
  ];

  $: currentPath = $page?.url?.pathname || '/';
</script>

<aside class="flex flex-col h-full bg-f1-surface border-r border-f1-border w-56 shrink-0">
  <!-- Header -->
  <div class="px-4 pt-5 pb-4 border-b border-f1-border">
    <div class="flex items-center gap-2 mb-3">
      <span class="text-f1-gold text-lg font-bold tracking-widest">RACE</span>
      <span class="text-f1-text text-lg font-bold tracking-widest">ENG</span>
    </div>

    {#if $config}
      <div class="text-f1-gold text-xs font-semibold tracking-wider truncate">
        {$config.team_name || 'Team'}
      </div>

      <div class="text-f1-sub text-xs mt-0.5">
        Moto n°{$config.our_bike_number || '-'} · {$config.our_category || '-'}
      </div>
    {:else}
      <div class="text-f1-sub text-xs">
        Configuration en chargement...
      </div>
    {/if}
  </div>

  <!-- Nav -->
  <nav class="flex-1 py-2 overflow-y-auto">
    {#each nav as item}
      <a
        href={item.href}
        class="nav-item {currentPath === item.href ? 'active' : ''}"
      >
        <span class="text-base w-5 text-center">{item.icon}</span>
        <span>{item.label}</span>

        {#if item.href === '/simulator' && $simState?.running}
          <span class="ml-auto w-1.5 h-1.5 rounded-full bg-f1-green animate-pulse"></span>
        {/if}
      </a>
    {/each}
  </nav>

  <!-- Footer -->
  <div class="px-4 py-3 border-t border-f1-border flex items-center gap-2">
    <span class="w-2 h-2 rounded-full {$connected ? 'bg-f1-green' : 'bg-f1-red'} shrink-0"></span>
    <span class="text-xs text-f1-muted">{$connected ? 'Connecté' : 'Déconnecté'}</span>
  </div>
</aside>