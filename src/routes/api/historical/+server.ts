import { json } from '@sveltejs/kit';
import { getHistoricalDataByLocality } from '$lib/server/database';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ url }) => {
	const locality = url.searchParams.get('locality');
	const limit = parseInt(url.searchParams.get('limit') || '20');

	if (!locality) {
		return json({ error: 'Locality parameter is required' }, { status: 400 });
	}

	try {
		const data = await getHistoricalDataByLocality(locality, limit);
		return json({ data });
	} catch (error) {
		return json({ error: 'Failed to fetch historical data' }, { status: 500 });
	}
};
