export interface Locality {
    name: string,
    coords: {
        latitude: number,
        longitude: number
    }

}
export interface SensorPayload {
    coords: {
        longitude: number,
        latitude: number
    },
    type: "AQI" | "traffic" | "water",
    value: number,
    locality: Locality
    timestamp: Date
    extra?: any
}

export interface AQIRecord {
    locality: string,
    coords: {
        longitude: number,
        latitude: number,
    }, value: number, timestamp: Date,
    extra: any,
}

export interface WaterRecord {
    locality: string,
    coords: {
        longitude: number,
        latitude: number,
    }, 
    value: number, 
    timestamp: Date,
    extra: {
        pH: number,
        tds: number,
        turbidity: number,
        status: string
    },
}