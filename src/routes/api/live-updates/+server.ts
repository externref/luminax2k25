import { supabase } from '$lib/server/database';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	const stream = new ReadableStream({
		async start(controller) {
			const encoder = new TextEncoder();
			let isClosed = false;

			const channel = supabase
				.channel('aqi_realtime')
				.on(
					'postgres_changes',
					{ event: 'INSERT', schema: 'public', table: 'aqi_records' },
					(payload) => {
						if (isClosed) return;
						
						const record = {
							locality: payload.new.locality,
							coords: payload.new.coords,
							value: payload.new.value,
							timestamp: new Date(payload.new.created_at),
							extra: payload.new.extra
						};

						const message = `data: ${JSON.stringify(record)}\n\n`;
						try {
							controller.enqueue(encoder.encode(message));
						} catch (error) {
							isClosed = true;
						}
					}
				)
				.subscribe();

			const keepAlive = setInterval(() => {
				if (isClosed) {
					clearInterval(keepAlive);
					return;
				}
				try {
					controller.enqueue(encoder.encode(': keepalive\n\n'));
				} catch (error) {
					isClosed = true;
					clearInterval(keepAlive);
				}
			}, 30000);

			return () => {
				isClosed = true;
				clearInterval(keepAlive);
				channel.unsubscribe();
			};
		}
	});

	return new Response(stream, {
		headers: {
			'Content-Type': 'text/event-stream',
			'Cache-Control': 'no-cache',
			Connection: 'keep-alive'
		}
	});
};
