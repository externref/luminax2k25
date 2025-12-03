<script lang="ts">
	import { onMount } from 'svelte';
	import type { Map as LeafletMap } from 'leaflet';
	import type { WaterRecord } from '$lib/$types';

	interface Props {
		data: {
			records: WaterRecord[];
		};
	}

	let { data }: Props = $props();

	let latestRecords = $derived(getLatestRecordPerLocation(data.records));

	let mapContainer: HTMLDivElement;
	let map: LeafletMap;
	let L: any;
	let heatLayer: any;
	let markerLayer: any;
	let selectedLocality: string | null = $state(null);
	let historicalData: any[] = $state([]);
	let loadingHistory = $state(false);
	let liveUpdates: WaterRecord[] = $state([]);
	let eventSource: EventSource | null = null;
	let poorQualityAreas = $derived.by(() => {
		const seen = new Set<string>();
		return data.records
			.filter(record => record.value < 50)
			.filter(record => {
				if (seen.has(record.locality)) return false;
				seen.add(record.locality);
				return true;
			})
			.sort((a, b) => a.value - b.value);
	});
	let sidebarOpen = $state(false);
	let markerMap = new Map<string, any>();

	function getLatestRecordPerLocation(records: WaterRecord[]) {
		const locationMap = new Map<string, WaterRecord>();
		records.forEach(record => {
			const key = `${record.coords.latitude},${record.coords.longitude}`;
			const existing = locationMap.get(key);
			if (!existing || new Date(record.timestamp) > new Date(existing.timestamp)) {
				locationMap.set(key, record);
			}
		});
		return Array.from(locationMap.values());
	}

	async function selectLocality(locality: string) {
		selectedLocality = locality;
		loadingHistory = true;

		try {
			const response = await fetch(`/api/water-history?locality=${encodeURIComponent(locality)}`);
			if (!response.ok) throw new Error('Failed to fetch historical data');
			historicalData = await response.json();
		} catch (error) {
			console.error('Error fetching historical data:', error);
			historicalData = [];
		} finally {
			loadingHistory = false;
		}
	}

	function addMarkerToMap(record: WaterRecord) {
		if (!map || !L || !markerLayer) return;

		const key = `${record.coords.latitude},${record.coords.longitude}`;
		const color = getWaterQualityColor(record.value);
		const existingMarker = markerMap.get(key);

		if (existingMarker) {
			existingMarker.setStyle({ fillColor: color });
			existingMarker.setTooltipContent(`${record.locality}: ${record.value}`);
		} else {
			const marker = L.circleMarker([record.coords.latitude, record.coords.longitude], {
				radius: 18,
				fillColor: color,
				color: '#fff',
				weight: 3,
				opacity: 1,
				fillOpacity: 0.8
			});

			marker.bindTooltip(`${record.locality}: ${record.value}`, {
				permanent: true,
				direction: 'top',
				className: 'water-label',
				offset: [0, -20]
			});

			marker.on('click', function (this: any) {
				selectLocality(record.locality);
			});

			markerLayer.addLayer(marker);
			markerMap.set(key, marker);
		}

		if (heatLayer) {
			const heatData = latestRecords.map(r => {
				const normalized = Math.max(0, Math.min(1, (100 - r.value) / 100));
				return [r.coords.latitude, r.coords.longitude, normalized];
			});
			heatLayer.setLatLngs(heatData);
		}
	}

	function getWaterQualityColor(wqi: number): string {
		if (wqi >= 90) return '#22c55e';
		if (wqi >= 70) return '#84cc16';
		if (wqi >= 50) return '#fbbf24';
		if (wqi >= 30) return '#f59e0b';
		if (wqi >= 10) return '#dc2626';
		return '#7f1d1d';
	}

	function getWaterQualityCategory(wqi: number): string {
		if (wqi >= 90) return 'Excellent';
		if (wqi >= 70) return 'Good';
		if (wqi >= 50) return 'Fair';
		if (wqi >= 30) return 'Poor';
		if (wqi >= 10) return 'Very Poor';
		return 'Unsafe';
	}

	onMount(async () => {
		L = (await import('leaflet')).default;

		await import('leaflet/dist/leaflet.css');
		await import('leaflet.heat');

		map = L.map(mapContainer, {
			center: [12.9716, 77.5946],
			zoom: 12,
			zoomControl: true
		});

		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '© OpenStreetMap contributors',
			maxZoom: 18
		}).addTo(map);

		const wqiValues = data.records.map(r => r.value).sort((a, b) => a - b);
		const minWQI = wqiValues[0];
		const maxWQI = wqiValues[wqiValues.length - 1];

		const heatData = latestRecords.map(record => {
			const normalized = Math.max(0, Math.min(1, (100 - record.value) / 100));
			return [record.coords.latitude, record.coords.longitude, normalized];
		});

		setTimeout(() => {
			heatLayer = (L as any).heatLayer(heatData, {
				radius: 35,
				blur: 20,
				maxZoom: 13,
				max: 1.0,
				gradient: {
					0.0: '#00ff00',
					0.1: '#33ff00',
					0.2: '#66ff00',
					0.3: '#99ff00',
					0.4: '#ccff00',
					0.5: '#ffff00',
					0.6: '#ffcc00',
					0.7: '#ff9900',
					0.8: '#ff3300',
					0.9: '#ff0000',
					1.0: '#990000'
				}
			}).addTo(map);
		}, 100);

		markerLayer = L.layerGroup();

		latestRecords.forEach((record) => {
			const color = getWaterQualityColor(record.value);
			const key = `${record.coords.latitude},${record.coords.longitude}`;
			const marker = L.circleMarker([record.coords.latitude, record.coords.longitude], {
				radius: 18,
				fillColor: color,
				color: '#fff',
				weight: 3,
				opacity: 1,
				fillOpacity: 0.8
			});

			marker.bindTooltip(`${record.locality}: ${record.value}`, {
				permanent: true,
				direction: 'top',
				className: 'water-label',
				offset: [0, -20]
			});

			marker.on('click', function (this: any) {
				selectLocality(record.locality);
			});

			markerLayer.addLayer(marker);
			markerMap.set(key, marker);
		});

		function updateLayerVisibility() {
			const zoom = map.getZoom();
			if (zoom >= 14) {
				if (!map.hasLayer(markerLayer)) {
					map.addLayer(markerLayer);
				}
				if (map.hasLayer(heatLayer)) {
					map.removeLayer(heatLayer);
				}
			} else {
				if (map.hasLayer(markerLayer)) {
					map.removeLayer(markerLayer);
				}
				if (!map.hasLayer(heatLayer)) {
					map.addLayer(heatLayer);
				}
			}
		}

		map.on('zoomend', updateLayerVisibility);
		updateLayerVisibility();

		eventSource = new EventSource('/api/water-updates');

		eventSource.onmessage = (event) => {
			const newRecord: WaterRecord = JSON.parse(event.data);
			liveUpdates = [newRecord, ...liveUpdates].slice(0, 10);
			data.records = [newRecord, ...data.records];
			addMarkerToMap(newRecord);
		};

		eventSource.onerror = (error) => {
			console.error('SSE Error:', error);
		};
	});

	$effect(() => {
		return () => {
			if (eventSource) {
				eventSource.close();
			}
		};
	});
</script>

<div class="min-h-screen bg-slate-950">
	<div class="flex h-screen">
		<div class="flex-1 overflow-y-auto px-8 py-8">
			<div class="mb-8 flex items-center justify-between">
				<div>
					<h1 class="text-4xl font-bold text-white">Water Quality Monitor</h1>
					<p class="mt-2 text-slate-400">Real-time WQI data across India</p>
				</div>
				<div class="flex gap-3">
					<button
						onclick={() => (sidebarOpen = !sidebarOpen)}
						class="rounded-lg border border-slate-800 bg-slate-900 px-4 py-2 text-white hover:bg-slate-800"
					>
						{sidebarOpen ? 'Hide' : 'Show'} Poor Quality Areas ({poorQualityAreas.length})
					</button>
				</div>
			</div>

			<div>
				<div class="rounded-xl border border-slate-800 bg-slate-900 p-6">
					<div class="mb-4 flex items-center justify-between">
						<h2 class="text-xl font-semibold text-white">Live Water Quality Map</h2>
						<div class="flex gap-4 text-sm">
							<div class="flex items-center gap-2">
								<div class="h-3 w-3 rounded-full bg-[#22c55e]"></div>
								<span class="text-slate-400">Excellent</span>
							</div>
							<div class="flex items-center gap-2">
								<div class="h-3 w-3 rounded-full bg-[#fbbf24]"></div>
								<span class="text-slate-400">Fair</span>
							</div>
							<div class="flex items-center gap-2">
								<div class="h-3 w-3 rounded-full bg-[#f59e0b]"></div>
								<span class="text-slate-400">Poor</span>
							</div>
							<div class="flex items-center gap-2">
								<div class="h-3 w-3 rounded-full bg-[#dc2626]"></div>
								<span class="text-slate-400">Very Poor</span>
							</div>
						</div>
					</div>

					<div bind:this={mapContainer} class="h-[800px] w-full rounded-lg"></div>
				</div>

				{#if selectedLocality}
					<div class="fixed inset-0 z-9999 flex items-center justify-center bg-black/50 p-4">
						<div class="max-h-[90vh] w-full max-w-4xl overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-2xl">
							<div class="flex items-center justify-between border-b border-slate-800 p-6">
								<div>
									<h2 class="text-2xl font-semibold text-white">
										{selectedLocality}
									</h2>
									<p class="mt-1 text-sm text-slate-400">Historical Water Quality Trends</p>
								</div>
								<button
									onclick={() => (selectedLocality = null)}
									class="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
									aria-label="Close modal"
								>
									<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
									</svg>
								</button>
							</div>

							<div class="overflow-y-auto p-6" style="max-height: calc(90vh - 100px)">
								{#if loadingHistory}
									<div class="flex items-center justify-center py-12">
										<div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-blue-500"></div>
									</div>
								{:else if historicalData.length === 0}
									<p class="py-8 text-center text-slate-400">No historical data available</p>
								{:else}
									<div class="mb-6">
										<h3 class="mb-4 text-lg font-semibold text-white">WQI Trend</h3>
										<svg viewBox="0 0 800 300" class="w-full" style="background: #0f172a; border-radius: 8px;">
											{#if historicalData.length > 0}
												{@const maxValue = Math.max(...historicalData.map(r => r.value))}
												{@const minValue = Math.min(...historicalData.map(r => r.value))}
												{@const range = maxValue - minValue || 1}
												{@const points = historicalData
													.slice()
													.reverse()
													.map((record, i) => {
														const x = 50 + (i * 700) / (historicalData.length - 1 || 1);
														const y = 250 - ((record.value - minValue) / range) * 200;
														return `${x},${y}`;
													})
													.join(' ')}

												<polyline
													points={points}
													fill="none"
													stroke="#3b82f6"
													stroke-width="3"
													stroke-linecap="round"
													stroke-linejoin="round"
												/>

												{#each historicalData.slice().reverse() as record, i}
													{@const x = 50 + (i * 700) / (historicalData.length - 1 || 1)}
													{@const y = 250 - ((record.value - minValue) / range) * 200}
													<circle cx={x} cy={y} r="5" fill={getWaterQualityColor(record.value)} stroke="#fff" stroke-width="2" />
												{/each}

												<line x1="50" y1="250" x2="750" y2="250" stroke="#475569" stroke-width="2" />
												<line x1="50" y1="50" x2="50" y2="250" stroke="#475569" stroke-width="2" />

												<text x="10" y="45" fill="#94a3b8" font-size="12">{maxValue}</text>
												<text x="10" y="285" fill="#94a3b8" font-size="12">{minValue}</text>
											{/if}
										</svg>
									</div>

									<div class="grid gap-3 md:grid-cols-2">
										{#each historicalData as record}
											<div class="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950 p-4">
												<div>
													<p class="text-sm text-slate-400">
														{new Date(record.created_at).toLocaleString()}
													</p>
													<p class="mt-1 text-xs text-slate-500">{getWaterQualityCategory(record.value)}</p>
													{#if record.extra}
														<div class="mt-2 space-y-1 text-xs text-slate-400">
															<p>pH: {record.extra.pH}</p>
															<p>TDS: {record.extra.tds} ppm</p>
															<p>Turbidity: {record.extra.turbidity} NTU</p>
														</div>
													{/if}
												</div>
												<div class="flex items-center gap-2">
													<div
														class="h-3 w-3 rounded-full"
														style="background-color: {getWaterQualityColor(record.value)}"
													></div>
													<span class="text-xl font-bold text-white">{record.value}</span>
												</div>
											</div>
										{/each}
									</div>
								{/if}
							</div>
						</div>
					</div>
				{/if}
			</div>

			{#if sidebarOpen}
				<div class="fixed right-0 top-0 z-9999 h-screen w-96 overflow-y-auto border-l border-slate-800 bg-slate-900 p-6 shadow-2xl">
					<div class="mb-4 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<div class="h-2 w-2 rounded-full bg-red-500"></div>
							<h2 class="text-xl font-semibold text-white">Poor Quality Areas</h2>
						</div>
						<button
							onclick={() => (sidebarOpen = false)}
							class="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
							aria-label="Close sidebar"
						>
							<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>

					{#if poorQualityAreas.length === 0}
						<p class="py-8 text-center text-sm text-slate-400">All areas have good water quality!</p>
					{:else}
						<div class="space-y-3">
							{#each poorQualityAreas as area}
								<button
									onclick={() => selectLocality(area.locality)}
									class="w-full rounded-lg border border-slate-800 bg-slate-950 p-4 text-left transition-colors hover:border-slate-700 hover:bg-slate-900"
								>
									<div class="flex items-start justify-between">
										<div class="flex-1">
											<h3 class="font-semibold text-white">{area.locality}</h3>
											<p class="mt-1 text-xs text-slate-400">
												{new Date(area.timestamp).toLocaleString()}
											</p>
											{#if area.extra}
												<div class="mt-2 space-y-1 text-xs text-slate-500">
													<p>pH: {area.extra.pH}</p>
													<p>TDS: {area.extra.tds} ppm</p>
													<p>Turbidity: {area.extra.turbidity} NTU</p>
													<p class="font-medium text-slate-400">{area.extra.status}</p>
												</div>
											{/if}
										</div>
										<div class="ml-3 flex flex-col items-end gap-2">
											<div
												class="h-3 w-3 rounded-full"
												style="background-color: {getWaterQualityColor(area.value)}"
											></div>
											<span class="text-2xl font-bold text-white">{area.value}</span>
											<span class="text-xs text-slate-400">{getWaterQualityCategory(area.value)}</span>
										</div>
									</div>
								</button>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	:global(.leaflet-container) {
		background: #0f172a;
	}

	:global(.leaflet-popup-content-wrapper) {
		background: #1e293b;
		color: #e2e8f0;
		border-radius: 0.5rem;
	}

	:global(.leaflet-popup-tip) {
		background: #1e293b;
	}

	:global(.water-label) {
		background: rgba(15, 23, 42, 0.95) !important;
		border: 1px solid rgba(71, 85, 105, 0.5) !important;
		border-radius: 6px !important;
		color: white !important;
		font-size: 11px !important;
		font-weight: 600 !important;
		padding: 4px 8px !important;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
		white-space: nowrap !important;
	}

	:global(.water-label::before) {
		display: none !important;
	}

	::-webkit-scrollbar {
		width: 8px;
	}

	::-webkit-scrollbar-track {
		background: #1e293b;
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb {
		background: #475569;
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb:hover {
		background: #64748b;
	}
</style>
