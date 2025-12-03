import type { SensorPayload } from "$lib/$types";
import { addAQIRecord, addWaterRecord } from "$lib/server/database";
import type { RequestHandler } from "@sveltejs/kit";

export const POST: RequestHandler = async ({request}) => {
    let data: SensorPayload =await request.json()
    
    switch (data.type){
        case "AQI": {
            await addAQIRecord(data)
            break;
        }
        case "water": {
            await addWaterRecord(data)
            break;
        }
    }
    return new Response("added")
}