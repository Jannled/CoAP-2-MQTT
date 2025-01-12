# CoAP 2 MQTT Bridge
- aiocoap (Python)
- MQTT
- Telegraf
- InfluxDB
- Grafana

The CoAP server will relay all messaged received under the `sensor/data` endpoint.

## Launch
```bash
# Need to be run every time you update the Python file
docker compose --profile tig build --no-cache

# Start with the TIG Stack
docker compose --profile tig up --detach

# Start only the CoAP & MQTT Server
docker compose --profile mqtt up --detach
```

```bash
docker exec -it iot-ws24-influxdb-1 influx auth list
docker exec -it iot-ws24-influxdb-1 influx telegrafs
```

## Environment Variables
- `COAP_BIND_NAME`
- `COAP_PORT`
- `MQTT_SERVER`
- `MQTT_PORT`
- `MQTT_USER`
- `MQTT_PASSWORD`

## CoAP Cheat Sheet
```mermaid
packet-beta
title CoAP Packet
0-1: "Ver"
2-3: "Type"
4-7: "Token length"
8-15: "Request/Response Code"
16-31: "Message ID"
32-95: "Token (0-8 bytes)"
96-127: "Options (if available)"
128-128: "1"
129-129: "1"
130-130: "1"
131-131: "1"
132-132: "1"
133-133: "1"
134-134: "1"
135-135: "1"
136-159: "Payload (if available)"
```

- GET: Code 0.01 (or 1 in hexadecimal).
- POST: Code 0.02 (or 2 in hexadecimal).
- PUT: Code 0.03 (or 3 in hexadecimal).
- DELETE: Code 0.04 (or 4 in hexadecimal).
