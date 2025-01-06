# CoAP 2 MQTT Bridge
- aiocoap (Python)
- MQTT
- Telegraf
- InfluxDB
- Grafana

The CoAP server will relay all messaged received under the `sensor/data` endpoint.

## Launch
```bash
# With the TIG Stack
docker compose up --profile tig --detach

# Only the CoAP & MQTT Server
docker compose up --detach
```

- `COAP_BIND_NAME`
- `COAP_PORT`
- `MQTT_SERVER`
- `MQTT_PORT`
- `MQTT_USER`
- `MQTT_PASSWORD`
