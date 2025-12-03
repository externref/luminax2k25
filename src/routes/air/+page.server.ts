import { supabase } from '$lib/server/database';
import type { AQIRecord } from '$lib/$types';

export async function load() {
	const { data, error } = await supabase
		.from('aqi_records')
		.select('*')
		.order('created_at', { ascending: false });

	if (error) {
		console.error('Error fetching AQI records:', error);
		return {
			records: [] as AQIRecord[]
		};
	}

	const records: AQIRecord[] = data.map((record) => ({
		locality: record.locality,
		coords: record.coords,
		value: record.value,
		timestamp: new Date(record.created_at),
        extra: record.extra
	}));

	return {
		records
	};
}
