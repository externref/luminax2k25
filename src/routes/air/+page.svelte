<script lang="ts">
	import { onMount } from 'svelte';
	import type { Map as LeafletMap } from 'leaflet';
	import type { AQIRecord } from '$lib/$types';

	interface Props {
		data: {
			records: AQIRecord[];
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
	let liveUpdates: AQIRecord[] = $state([]);
	let eventSource: EventSource | null = null;
	let unhealthyAreas = $derived.by(() => {
		const seen = new Set<string>();
		return data.records
			.filter(record => record.value > 100)
			.filter(record => {
				if (seen.has(record.locality)) return false;
				seen.add(record.locality);
				return true;
			})
			.sort((a, b) => b.value - a.value);
	});
	let sidebarOpen = $state(false);
	let markerMap = new Map<string, any>();

	function getLatestRecordPerLocation(records: AQIRecord[]) {
		const locationMap = new Map<string, AQIRecord>();
		records.forEach(record => {
			const key = `${record.coords.latitude},${record.coords.longitude}`;
			const existing = locationMap.get(key);
			if (!existing || new Date(record.timestamp) > new Date(existing.timestamp)) {
				locationMap.set(key, record);
			}
		});
		return Array.from(locationMap.values());
	}

	async function fetchHistoricalData(locality: string) {
		loadingHistory = true;
		try {
			const response = await fetch(`/api/historical?locality=${encodeURIComponent(locality)}&limit=20`);
			const result = await response.json();
			if (result.data) {
				historicalData = result.data;
			}
		} catch (error) {
			console.error('Error fetching historical data:', error);
		} finally {
			loadingHistory = false;
		}
	}

	function selectLocality(locality: string) {
		selectedLocality = locality;
		fetchHistoricalData(locality);
	}

	function addMarkerToMap(record: AQIRecord) {
		if (!L || !map || !heatLayer || !markerLayer) return;

		const allRecords = [...data.records];
		const aqiValues = allRecords.map(r => r.value).sort((a, b) => a - b);
		const minAQI = aqiValues[0];
		const maxAQI = aqiValues[aqiValues.length - 1];
		const normalized = (record.value - minAQI) / (maxAQI - minAQI);

		const newPoint: [number, number, number] = [
			record.coords.latitude,
			record.coords.longitude,
			normalized
		];
		(heatLayer as any).addLatLng(newPoint);

		const key = `${record.coords.latitude},${record.coords.longitude}`;
		const existingMarker = markerMap.get(key);
		
		if (existingMarker) {
			const color = getAQIColor(record.value);
			existingMarker.setStyle({
				fillColor: color
			});
			existingMarker.setTooltipContent(`${record.locality}: ${record.value}`);
		} else {
			const color = getAQIColor(record.value);
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
				className: 'aqi-label',
				offset: [0, -20]
			});

			marker.on('click', function (this: any) {
				selectLocality(record.locality);
			});

			markerLayer.addLayer(marker);
			markerMap.set(key, marker);
		}
	}

	function getAQIColor(aqi: number): string {
		if (aqi <= 50) return '#00e400';
		if (aqi <= 75) return '#7acc16';
		if (aqi <= 100) return '#ffff00';
		if (aqi <= 125) return '#ffcc00';
		if (aqi <= 150) return '#ff9900';
		if (aqi <= 175) return '#ff6600';
		if (aqi <= 200) return '#ff3300';
		if (aqi <= 225) return '#ff0000';
		if (aqi <= 250) return '#cc0000';
		if (aqi <= 275) return '#990033';
		if (aqi <= 300) return '#660066';
		return '#4d004d';
	}

	function getAQICategory(aqi: number): string {
		if (aqi <= 50) return 'Good';
		if (aqi <= 75) return 'Satisfactory';
		if (aqi <= 100) return 'Moderate';
		if (aqi <= 125) return 'Moderate to Poor';
		if (aqi <= 150) return 'Poor';
		if (aqi <= 175) return 'Poor to Very Poor';
		if (aqi <= 200) return 'Very Poor';
		if (aqi <= 225) return 'Very Poor to Severe';
		if (aqi <= 250) return 'Severe';
		if (aqi <= 275) return 'Severe+';
		if (aqi <= 300) return 'Severe++';
		return 'Hazardous';
	}

	onMount(async () => {
		L = (await import('leaflet')).default;

		await import('leaflet/dist/leaflet.css');
		await import('leaflet.heat');
		
		console.log('Leaflet loaded:', L);
		console.log('L.heatLayer:', (L as any).heatLayer);

		map = L.map(mapContainer, {
			center: [12.9716, 77.5946],
			zoom: 12,
			zoomControl: true
		});

		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '© OpenStreetMap contributors',
			maxZoom: 18
		}).addTo(map);

		const aqiValues = data.records.map(r => r.value).sort((a, b) => a - b);
		const minAQI = aqiValues[0];
		const maxAQI = aqiValues[aqiValues.length - 1];
		
		console.log('AQI range:', {
			min: minAQI,
			max: maxAQI,
			median: aqiValues[Math.floor(aqiValues.length / 2)],
			sample: aqiValues.slice(0, 10)
		});

		const heatData = data.records.map((record) => {
			const normalized = (record.value - minAQI) / (maxAQI - minAQI);
			return [
				record.coords.latitude,
				record.coords.longitude,
				normalized
			];
		});

		console.log('Heat data points:', heatData.length, heatData.slice(0, 3));

		setTimeout(() => {
			heatLayer = (L as any).heatLayer(heatData, {
				radius: 35,
				blur: 20,
				max: 1.0,
				minOpacity: 0.4,
				gradient: {
					0.0: '#00e400',
					0.1: '#7acc16',
					0.2: '#ffff00',
					0.3: '#ffcc00',
					0.4: '#ff9900',
					0.5: '#ff6600',
					0.6: '#ff3300',
					0.7: '#ff0000',
					0.8: '#cc0000',
					0.85: '#990033',
					0.9: '#660066',
					1.0: '#4d004d'
				}
			}).addTo(map);
			console.log('Heatmap layer created');
		}, 100);

		markerLayer = L.layerGroup();

		latestRecords.forEach((record) => {
			const color = getAQIColor(record.value);
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
				className: 'aqi-label',
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

		eventSource = new EventSource('/api/live-updates');
		
		eventSource.onmessage = (event) => {
			const newRecord: AQIRecord = JSON.parse(event.data);
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
					<h1 class="text-4xl font-bold text-white">Air Quality Monitor</h1>
					<p class="mt-2 text-slate-400">Real-time AQI data across India</p>
				</div>
				<div class="flex gap-3">
					<button
						onclick={() => (sidebarOpen = !sidebarOpen)}
						class="rounded-lg border border-slate-800 bg-slate-900 px-4 py-2 text-white hover:bg-slate-800"
					>
						{sidebarOpen ? 'Hide' : 'Show'} Unhealthy Areas ({unhealthyAreas.length})
					</button>
				</div>
			</div>

			<div>
				<div class="rounded-xl border border-slate-800 bg-slate-900 p-6">
					<div class="mb-4 flex items-center justify-between">
						<h2 class="text-xl font-semibold text-white">Live AQI Map</h2>
						<div class="flex gap-4 text-sm">
							<div class="flex items-center gap-2">
								<div class="h-3 w-3 rounded-full bg-[#22c55e]"></div>
								<span class="text-slate-400">Good</span>
							</div>
							<div class="flex items-center gap-2">
								<div class="h-3 w-3 rounded-full bg-[#fbbf24]"></div>
								<span class="text-slate-400">Moderate</span>
							</div>
							<div class="flex items-center gap-2">
								<div class="h-3 w-3 rounded-full bg-[#f59e0b]"></div>
								<span class="text-slate-400">Unhealthy</span>
							</div>
							<div class="flex items-center gap-2">
								<div class="h-3 w-3 rounded-full bg-[#dc2626]"></div>
								<span class="text-slate-400">Very Unhealthy</span>
							</div>
					</div>
				</div>

				<div bind:this={mapContainer} class="h-[800px] w-full rounded-lg"></div>
			</div>				{#if selectedLocality}
					<div class="fixed inset-0 z-9999 flex items-center justify-center bg-black/50 p-4">
						<div class="max-h-[90vh] w-full max-w-4xl overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-2xl">
							<div class="flex items-center justify-between border-b border-slate-800 p-6">
								<div>
									<h2 class="text-2xl font-semibold text-white">
										{selectedLocality}
									</h2>
									<p class="mt-1 text-sm text-slate-400">Historical AQI Trends</p>
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
									<div class="py-16 text-center text-slate-400">Loading...</div>
								{:else if historicalData.length === 0}
									<div class="py-16 text-center text-slate-400">No historical data available</div>
								{:else}
									<div class="mb-8 rounded-lg border border-slate-800 bg-slate-950 p-6">
										<svg class="h-80 w-full" viewBox="0 0 800 320">
											<defs>
												<linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
													<stop offset="0%" style="stop-color:#22c55e;stop-opacity:0.3" />
													<stop offset="100%" style="stop-color:#dc2626;stop-opacity:0.3" />
												</linearGradient>
											</defs>
											
											{#if historicalData.length > 0}
												{@const maxValue = Math.max(...historicalData.map(d => d.value), 300)}
												{@const minValue = Math.min(...historicalData.map(d => d.value), 0)}
												{@const range = maxValue - minValue || 1}
												{@const points = historicalData.slice().reverse().map((d, i) => {
													const x = (i / (historicalData.length - 1 || 1)) * 760 + 20;
													const y = 280 - ((d.value - minValue) / range) * 240;
													return { x, y, value: d.value, date: d.created_at };
												})}
												{@const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')}
												{@const areaD = `${pathD} L ${points[points.length - 1]?.x} 280 L 20 280 Z`}
												
												<path d={areaD} fill="url(#gradient)" opacity="0.3"/>
												<path d={pathD} fill="none" stroke="#3b82f6" stroke-width="3"/>
												
												{#each points as point}
													<circle 
														cx={point.x} 
														cy={point.y} 
														r="5" 
														fill={getAQIColor(point.value)}
														stroke="#fff"
														stroke-width="2"
														class="cursor-pointer transition-all hover:r-7"
													>
														<title>{point.value} AQI - {new Date(point.date).toLocaleString()}</title>
													</circle>
												{/each}
												
												<line x1="20" y1="280" x2="780" y2="280" stroke="#475569" stroke-width="1"/>
												<line x1="20" y1="40" x2="20" y2="280" stroke="#475569" stroke-width="1"/>
												
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
													<p class="mt-1 text-xs text-slate-500">{getAQICategory(record.value)}</p>
												</div>
												<div class="flex items-center gap-2">
													<div
														class="h-3 w-3 rounded-full"
														style="background-color: {getAQIColor(record.value)}"
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
							<h2 class="text-xl font-semibold text-white">Unhealthy Areas</h2>
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

					{#if unhealthyAreas.length === 0}
					<p class="py-4 text-center text-sm text-slate-400">All areas are in good condition</p>
				{:else}
					<div class="space-y-3">
							{#each unhealthyAreas as area, index}
								<button
									onclick={() => selectLocality(area.locality)}
									class="w-full rounded-lg border border-slate-800 bg-slate-950 p-4 text-left transition-all hover:border-slate-700"
									style="animation: slideIn 0.3s ease-out {index * 0.05}s backwards"
								>
									<div class="flex items-start justify-between">
										<div class="flex-1">
											<div class="flex items-center gap-2">
												<div
													class="h-2 w-2 rounded-full"
													style="background-color: {getAQIColor(area.value)}"
												></div>
												<h3 class="font-semibold text-white">{area.locality}</h3>
											</div>
											<p class="mt-1 text-xs text-slate-500">
												{new Date(area.timestamp).toLocaleString()}
											</p>
											<p class="mt-1 text-sm text-slate-400">{getAQICategory(area.value)}</p>
										</div>
										<div class="text-right">
											<span class="text-2xl font-bold text-white">{area.value}</span>
											<p class="text-xs text-slate-500">AQI</p>
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

	:global(.aqi-label) {
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

	:global(.aqi-label::before) {
		display: none !important;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
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
