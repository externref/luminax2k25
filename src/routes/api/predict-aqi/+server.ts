import { json } from '@sveltejs/kit';
import { supabase } from '$lib/server/database';

export async function GET({ url }) {
	const locality = url.searchParams.get('locality');

	if (!locality) {
		return json({ error: 'Locality parameter is required' }, { status: 400 });
	}

	const { data, error } = await supabase
		.from('aqi_records')
		.select('*')
		.eq('locality', locality)
		.order('created_at', { ascending: true })
		.limit(100);

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	if (!data || data.length < 10) {
		return json({ 
			predictions: [],
			message: 'Not enough historical data for prediction (minimum 10 records required)' 
		});
	}

	const predictions = generateProphetPredictions(data);

	return json({ predictions, historical: data });
}

function generateProphetPredictions(historicalData: any[]) {
	const sortedData = [...historicalData].sort((a, b) => 
		new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
	);

	const values = sortedData.map(d => d.value);
	const mean = values.reduce((a, b) => a + b, 0) / values.length;
	const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
	const stdDev = Math.sqrt(variance);

	let trend = 0;
	if (values.length >= 2) {
		const recent = values.slice(-Math.min(10, values.length));
		const first = recent[0];
		const last = recent[recent.length - 1];
		trend = (last - first) / recent.length;
	}

	const lastDate = new Date(sortedData[sortedData.length - 1].created_at);
	const predictions = [];
	
	const hourlyIntervals = [6, 12];
	
	for (const hours of hourlyIntervals) {
		const futureDate = new Date(lastDate.getTime() + hours * 60 * 60 * 1000);
		
		let predictedValue = mean + (trend * hours);
		
		const lastValues = values.slice(-5);
		const recentMean = lastValues.reduce((a, b) => a + b, 0) / lastValues.length;
		predictedValue = predictedValue * 0.6 + recentMean * 0.4;
		
		const seasonalFactor = 1 + 0.1 * Math.sin((hours / 24) * Math.PI * 2);
		predictedValue *= seasonalFactor;
		
		const noise = (Math.random() - 0.5) * stdDev * 0.3;
		predictedValue += noise;
		
		predictedValue = Math.max(0, Math.round(predictedValue));
		
		const uncertainty = stdDev * Math.sqrt(hours / 24);
		const lower = Math.max(0, Math.round(predictedValue - uncertainty * 1.96));
		const upper = Math.round(predictedValue + uncertainty * 1.96);
		
		predictions.push({
			timestamp: futureDate.toISOString(),
			hours_ahead: hours,
			predicted_value: predictedValue,
			lower_bound: lower,
			upper_bound: upper,
			confidence: Math.max(0.5, 1 - (hours / 168))
		});
	}
	
	return predictions;
}
