import httpx 
import json

client = httpx.Client(base_url="http://localhost:5173")


with open("server_replicators/aqi.jsonl") as file:
    lines = file.readlines()
    for line in lines:
        data = json.loads(line)
        print(f"Sending: {data}")
        res = client.post("/api/report", json=data)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
        print("---")