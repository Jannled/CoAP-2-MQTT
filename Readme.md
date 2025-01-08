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

## Environment Variables
- `COAP_BIND_NAME`
- `COAP_PORT`
- `MQTT_SERVER`
- `MQTT_PORT`
- `MQTT_USER`
- `MQTT_PASSWORD`
