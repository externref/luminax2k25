import httpx
import json
from datetime import datetime, timezone

url = "http://localhost:5173/api/report"

with open("./server_replicators/water.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        
        payload = {
            "coords": data["coords"],
            "type": "water",
            "value": data["value"],
            "locality": data["locality"],
            "timestamp": data["timestamp"],
            "extra": data["extra"]
        }
        
        print(f"Sending: {payload['locality']['name']} - WQI: {payload['value']}")
        
        response = httpx.post(url, json=payload, timeout=10.0)
        print(f"Response: {response.status_code} - {response.text}")
