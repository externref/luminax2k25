<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/stores';
	
	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="min-h-screen bg-slate-950">
	<nav class="border-b border-slate-800 bg-slate-900/95 backdrop-blur-sm sticky top-0 z-50">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="flex h-16 items-center justify-between">
				<a href="/" class="flex items-center gap-2 hover:opacity-80 transition-opacity">
					<div class="h-8 w-8 rounded-lg bg-linear-to-br from-cyan-500 to-blue-600"></div>
					<span class="text-xl font-semibold text-white">Surge</span>
				</a>
				<div class="flex items-center gap-6">
					<a href="/" class="text-sm font-medium text-slate-400 hover:text-white transition-colors">
						Home
					</a>
					<a href="/air" class="text-sm font-medium text-slate-400 hover:text-white transition-colors">
						Air Quality
					</a>
					<a href="/water" class="text-sm font-medium text-slate-400 hover:text-white transition-colors">
						Water Quality
					</a>
				</div>
			</div>
		</div>
	</nav>
	
	{@render children()}
</div>
