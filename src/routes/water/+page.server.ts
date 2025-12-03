import { supabase } from '$lib/server/database';
import type { WaterRecord } from '$lib/$types';

export async function load() {
	const { data, error } = await supabase
		.from('water_records')
		.select('*')
		.order('created_at', { ascending: false });

	if (error) {
		console.error('Error fetching water records:', error);
		return { records: [] };
	}

	const records: WaterRecord[] = data.map((record: any) => ({
		locality: record.locality,
		coords: {
			latitude: record.coords.latitude,
			longitude: record.coords.longitude
		},
		value: record.value,
		timestamp: record.created_at,
		extra: record.extra
	}));

	return { records };
}
