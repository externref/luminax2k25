import { createClient } from '@supabase/supabase-js';
import { SURGE_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY } from '$env/static/private';
import type { SensorPayload } from '$lib/$types';

export const supabase = createClient(SURGE_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

export async function addAQIRecord(payload: SensorPayload) {
	const { data, error } = await supabase
		.from('aqi_records')
		.insert({
			locality: payload.locality.name,
			coords: payload.coords,
			value: payload.value,
            extra: payload.extra
		})
		.select();

	if (error) {
		throw new Error(`Failed to insert AQI record: ${error.message}`);
	}

	return data;
}

export async function getHistoricalDataByLocality(locality: string, limit: number = 20) {
	const { data, error } = await supabase
		.from('aqi_records')
		.select('*')
		.eq('locality', locality)
		.order('created_at', { ascending: false })
		.limit(limit);

	if (error) {
		throw new Error(`Failed to fetch historical data: ${error.message}`);
	}

	return data;
}

export async function subscribeToAQIUpdates(callback: (payload: any) => void) {
	return supabase
		.channel('aqi_updates')
		.on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'aqi_records' }, callback)
		.subscribe();
}

export async function addWaterRecord(payload: SensorPayload) {
	const { data, error } = await supabase
		.from('water_records')
		.insert({
			locality: payload.locality.name,
			coords: payload.coords,
			value: payload.value,
            extra: payload.extra
		})
		.select();

	if (error) {
		throw new Error(`Failed to insert water record: ${error.message}`);
	}

	return data;
}

export async function getHistoricalWaterDataByLocality(locality: string, limit: number = 20) {
	const { data, error } = await supabase
		.from('water_records')
		.select('*')
		.eq('locality', locality)
		.order('created_at', { ascending: false })
		.limit(limit);

	if (error) {
		throw new Error(`Failed to fetch historical water data: ${error.message}`);
	}

	return data;
}

export async function subscribeToWaterUpdates(callback: (payload: any) => void) {
	return supabase
		.channel('water_updates')
		.on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'water_records' }, callback)
		.subscribe();
}