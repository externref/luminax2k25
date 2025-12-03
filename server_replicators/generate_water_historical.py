import httpx
import json
from datetime import datetime, timedelta
import time
import random

url = "http://localhost:5173/api/report"

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

def fetch_water_quality_data(lat, lon):
    """
    Fetch water quality data from OpenWeatherMap Water Quality API
    Note: This is a placeholder - OpenWeatherMap doesn't have a public water quality API
    Instead, we'll generate realistic data based on typical Bangalore water parameters
    """
    try:
        base_wqi = random.randint(55, 85)
        
        if base_wqi >= 90:
            status = "Excellent"
        elif base_wqi >= 70:
            status = "Good"
        elif base_wqi >= 50:
            status = "Fair"
        elif base_wqi >= 30:
            status = "Poor"
        else:
            status = "Very Poor"
        
        return {
            "wqi": base_wqi,
            "pH": round(random.uniform(6.8, 8.2), 2),
            "tds": random.randint(180, 350),
            "turbidity": round(random.uniform(0.5, 4.0), 2),
            "status": status
        }
    except Exception as e:
        print(f"Error generating water quality data: {e}")
        return None

def generate_historical_data():
    """Generate historical water quality data using realistic baseline values"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=2)
    
    print("💧 Generating realistic water quality data for all localities...\n")
    locality_baseline = {}
    
    for locality in localities:
        print(f"   Setting baseline for {locality['name']}...", end=" ")
        water_data = fetch_water_quality_data(
            locality["coords"]["latitude"], 
            locality["coords"]["longitude"]
        )
        
        if water_data:
            locality_baseline[locality["name"]] = water_data
            print(f"✅ WQI: {water_data['wqi']}, pH: {water_data['pH']}, TDS: {water_data['tds']}")
        else:
            print(f"⚠️  Using fallback")
            locality_baseline[locality["name"]] = {
                "wqi": 70,
                "pH": 7.5,
                "tds": 250,
                "turbidity": 2.0,
                "status": "Good"
            }
        
        time.sleep(0.1)
    
    print(f"\n📊 Generating 2 days of historical data with realistic variations...\n")
    
    current_time = start_time
    records_sent = 0
    
    while current_time <= end_time:
        for locality in localities:
            baseline = locality_baseline[locality["name"]]
            
            hour_factor = current_time.hour
            if 0 <= hour_factor <= 6:
                usage_factor = 0.95
            elif 6 <= hour_factor <= 10:
                usage_factor = 1.1
            elif 18 <= hour_factor <= 22:
                usage_factor = 1.08
            else:
                usage_factor = 1.0
            
            wqi_variation = random.randint(-8, 8)
            wqi_value = int(max(30, min(100, baseline["wqi"] + wqi_variation)))
            
            pH = round(baseline["pH"] + random.uniform(-0.3, 0.3), 2)
            pH = max(6.5, min(8.5, pH))
            
            tds = int(baseline["tds"] * usage_factor + random.randint(-20, 20))
            tds = max(100, min(500, tds))
            
            turbidity = round(baseline["turbidity"] + random.uniform(-0.5, 0.5), 2)
            turbidity = max(0.5, min(5.0, turbidity))
            
            if wqi_value >= 90:
                status = "Excellent"
            elif wqi_value >= 70:
                status = "Good"
            elif wqi_value >= 50:
                status = "Fair"
            elif wqi_value >= 30:
                status = "Poor"
            else:
                status = "Very Poor"
            
            payload = {
                "coords": locality["coords"],
                "type": "water",
                "value": wqi_value,
                "locality": locality,
                "timestamp": current_time.isoformat() + "Z",
                "extra": {
                    "pH": pH,
                    "tds": tds,
                    "turbidity": turbidity,
                    "status": status
                }
            }
            
            try:
                response = httpx.post(url, json=payload, timeout=10.0)
                records_sent += 1
                print(f"[{records_sent}] {current_time.strftime('%Y-%m-%d %H:%M')} | {locality['name']:20} | WQI: {wqi_value:3} | pH: {pH:.2f} | TDS: {tds:3} | {response.status_code}")
                
                time.sleep(0.05)
                
            except Exception as e:
                print(f"Error sending data for {locality['name']}: {e}")
        
        current_time += timedelta(hours=1)
    
    print(f"\n✅ Completed! Sent {records_sent} records for {len(localities)} localities over 2 days (1-hour intervals)")
    print(f"Total expected: {len(localities) * 49} records (2 days * 24 hours + 1)")

if __name__ == "__main__":
    print("🚀 Starting Water Quality historical data generation...")
    print(f"📍 Localities: {len(localities)}")
    print(f"📅 Time range: Last 2 days")
    print(f"⏱️  Interval: 1 hour")
    print(f"📊 Total records to send: {len(localities) * 49}\n")
    
    generate_historical_data()
