import json

AQI = []
TRAFFIC = []
WATER = []

with open("filename") as file:
    data = file.read()
    for line in data.splitlines():
        jsond = json.loads(line)
        if jsond.type=="AQI": AQI.append(jsond)
        elif jsond.type == "water": WATER.append(jsond)
        else: TRAFFIC.append(jsond)



open("aqi.jsonl").write("\n".join([json.dumps(data) for data in AQI]))
open("traffic.jsonl").write("\n".join([json.dumps(data) for data in TRAFFIC]))
open("water.jsonl").write("\n".join([json.dumps(data) for data in WATER]))

