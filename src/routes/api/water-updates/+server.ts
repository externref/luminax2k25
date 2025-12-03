import { subscribeToWaterUpdates } from '$lib/server/database';

export async function GET() {
	const stream = new ReadableStream({
		start(controller) {
			let isClosed = false;

			const encoder = new TextEncoder();

			const send = (data: string) => {
				if (isClosed) return;
				try {
					controller.enqueue(encoder.encode(`data: ${data}\n\n`));
				} catch (error) {
					console.error('Error sending SSE:', error);
				}
			};

			const keepAlive = setInterval(() => {
				send(JSON.stringify({ type: 'keepalive' }));
			}, 30000);

			subscribeToWaterUpdates((payload) => {
				if (payload.new) {
					const record = {
						id: payload.new.id,
						locality: payload.new.locality,
						coords: payload.new.coords,
						value: payload.new.value,
						created_at: payload.new.created_at,
						extra: payload.new.extra
					};
					send(JSON.stringify(record));
				}
			});

			return () => {
				isClosed = true;
				clearInterval(keepAlive);
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
}
