import httpx
import json
from datetime import datetime, timedelta
import time

url = "http://localhost:5173/api/report"
WAQI_TOKEN = "2ec482f4c0f10861638fb438cdb2af6adaa342f3"

localities = [
    {"name": "Koramangala", "coords": {"latitude": 12.9352, "longitude": 77.6245}},
    {"name": "Indiranagar", "coords": {"latitude": 12.9716, "longitude": 77.6412}},
    {"name": "Whitefield", "coords": {"latitude": 12.9698, "longitude": 77.7499}},
    {"name": "Jayanagar", "coords": {"latitude": 12.9250, "longitude": 77.5838}},
    {"name": "MG Road", "coords": {"latitude": 12.9750, "longitude": 77.6062}},
    {"name": "Electronic City", "coords": {"latitude": 12.8456, "longitude": 77.6603}},
    {"name": "HSR Layout", "coords": {"latitude": 12.9116, "longitude": 77.6473}},
    {"name": "Marathahalli", "coords": {"latitude": 12.9591, "longitude": 77.6974}},
    {"name": "BTM Layout", "coords": {"latitude": 12.9165, "longitude": 77.6101}},
    {"name": "Yelahanka", "coords": {"latitude": 13.1007, "longitude": 77.5963}},
    {"name": "Bannerghatta Road", "coords": {"latitude": 12.8889, "longitude": 77.5958}},
    {"name": "Rajajinagar", "coords": {"latitude": 12.9910, "longitude": 77.5552}},
    {"name": "Malleshwaram", "coords": {"latitude": 13.0033, "longitude": 77.5703}},
    {"name": "JP Nagar", "coords": {"latitude": 12.9081, "longitude": 77.5856}},
    {"name": "Bellandur", "coords": {"latitude": 12.9259, "longitude": 77.6751}},
    {"name": "Sarjapur Road", "coords": {"latitude": 12.9107, "longitude": 77.7085}},
    {"name": "Hebbal", "coords": {"latitude": 13.0358, "longitude": 77.5970}},
    {"name": "Banashankari", "coords": {"latitude": 12.9250, "longitude": 77.5482}},
    {"name": "Bommanahalli", "coords": {"latitude": 12.9141, "longitude": 77.6269}},
    {"name": "KR Puram", "coords": {"latitude": 13.0117, "longitude": 77.6961}}
]

def fetch_aqi_data(lat, lon):
    """Fetch real-time AQI data from WAQI API"""
    try:
        api_url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
        response = httpx.get(api_url, timeout=10.0)
        data = response.json()
        
        if data.get("status") == "ok":
            aqi = data["data"].get("aqi", None)
            if aqi and aqi != "-":
                iaqi = data["data"].get("iaqi", {})
                return {
                    "aqi": int(aqi),
                    "pm25": iaqi.get("pm25", {}).get("v"),
                    "pm10": iaqi.get("pm10", {}).get("v"),
                    "no2": iaqi.get("no2", {}).get("v"),
                    "so2": iaqi.get("so2", {}).get("v"),
                    "co": iaqi.get("co", {}).get("v"),
                    "o3": iaqi.get("o3", {}).get("v")
                }
        return None
    except Exception as e:
        print(f"Error fetching AQI: {e}")
        return None

def generate_historical_data():
    """Generate historical data using current AQI values with realistic variations"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=2)
    
    print("📡 Fetching real-time AQI data for all localities...")
    locality_current_aqi = {}
    
    for locality in localities:
        print(f"   Fetching {locality['name']}...", end=" ")
        aqi_data = fetch_aqi_data(locality["coords"]["latitude"], locality["coords"]["longitude"])
        
        if aqi_data and aqi_data["aqi"]:
            locality_current_aqi[locality["name"]] = aqi_data
            print(f"✅ AQI: {aqi_data['aqi']}")
        else:
            print(f"⚠️  Using fallback (data unavailable)")
            locality_current_aqi[locality["name"]] = {
                "aqi": 150,
                "pm25": 90, "pm10": 120, "no2": 45, "so2": 15, "co": 1.2, "o3": 35
            }
        
        time.sleep(0.5)
    
    print(f"\n📊 Generating historical data with realistic variations...\n")
    
    current_time = start_time
    records_sent = 0
    
    locality_values = {}
    for name, data in locality_current_aqi.items():
        locality_values[name] = {
            "aqi": data["aqi"],
            "pm25": data["pm25"] or data["aqi"] * 0.6,
            "pm10": data["pm10"] or data["aqi"] * 0.8,
            "no2": data["no2"] or 45,
            "so2": data["so2"] or 15,
            "co": data["co"] or 1.2,
            "o3": data["o3"] or 35
        }
    
    while current_time <= end_time:
        for locality in localities:
            values = locality_values[locality["name"]]
            
            import random
            hour_factor = current_time.hour
            if 6 <= hour_factor <= 10 or 17 <= hour_factor <= 21:
                traffic_factor = 1.15
            else:
                traffic_factor = 0.95
            
            aqi_variation = random.randint(-10, 10)
            aqi_value = int(max(50, min(300, values["aqi"] * traffic_factor + aqi_variation)))
            
            payload = {
                "coords": locality["coords"],
                "type": "AQI",
                "value": aqi_value,
                "locality": locality,
                "timestamp": current_time.isoformat() + "Z",
                "extra": {
                    "pm25": round(values["pm25"] * traffic_factor + random.uniform(-5, 5), 2),
                    "pm10": round(values["pm10"] * traffic_factor + random.uniform(-8, 8), 2),
                    "no2": round(values["no2"] + random.uniform(-10, 10), 2),
                    "so2": round(values["so2"] + random.uniform(-3, 3), 2),
                    "co": round(values["co"] + random.uniform(-0.2, 0.2), 2),
                    "o3": round(values["o3"] + random.uniform(-8, 8), 2)
                }
            }
            
            try:
                response = httpx.post(url, json=payload, timeout=10.0)
                records_sent += 1
                print(f"[{records_sent}] {current_time.strftime('%Y-%m-%d %H:%M')} | {locality['name']:20} | AQI: {aqi_value:3} | Status: {response.status_code}")
                
                time.sleep(0.05)
                
            except Exception as e:
                print(f"Error sending data for {locality['name']}: {e}")
        
        current_time += timedelta(hours=1)
    
    print(f"\n✅ Completed! Sent {records_sent} records for {len(localities)} localities over 2 days (1-hour intervals)")
    print(f"Total expected: {len(localities) * 49} records (2 days * 24 hours + 1)")

if __name__ == "__main__":
    print("🚀 Starting AQI historical data generation with real-time values...")
    print(f"📍 Localities: {len(localities)}")
    print(f"📅 Time range: Last 2 days")
    print(f"⏱️  Interval: 1 hour")
    print(f"📊 Total records to send: {len(localities) * 49}\n")
    
    generate_historical_data()
