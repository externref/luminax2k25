import { json } from '@sveltejs/kit';
import { supabase } from '$lib/server/database';

export async function GET({ url }) {
	const locality = url.searchParams.get('locality');

	if (!locality) {
		return json({ error: 'Locality parameter is required' }, { status: 400 });
	}

	const { data, error } = await supabase
		.from('water_records')
		.select('*')
		.eq('locality', locality)
		.order('created_at', { ascending: false })
		.limit(50);

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	return json(data);
}
