<script>
  import '../app.css';
  import Sidebar from '$lib/components/Sidebar.svelte';
  // L'import seul des stores déclenche le chargement automatique
  import '$lib/stores.js';
</script>

<div class="flex h-screen overflow-hidden bg-f1-bg text-f1-text">
  <Sidebar />
  <main class="flex-1 overflow-y-auto">
    <slot />
  </main>
</div>
