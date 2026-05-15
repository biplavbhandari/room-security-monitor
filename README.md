# Room Security Monitor

Dockerized setup for Mosquitto (MQTT broker), InfluxDB, and a Python subscriber that stores sensor data and sends SNS alerts.

## Services
- **Mosquitto** (MQTT) on port **1883**
- **InfluxDB 2.x** on port **8086**
- **Room Subscriber** (Python) → InfluxDB + SNS

## Quick start
1) Create `.env` from `.env.example`:
```bash
cp .env.example .env
# edit .env with your AWS + Influx values
```

2) Run:
```bash
docker compose up -d --build
```

## Test MQTT
Terminal 1:
```bash
mosquitto_sub -h localhost -t "room/sensors"
```

Terminal 2:
```bash
mosquitto_pub -h localhost -t "room/sensors" -m '{"temp":35,"light":900,"motion":1}'
```

## InfluxDB UI
Open:
```
http://YOUR_EC2_PUBLIC_IP:8086
```

## Notes
- This repo does **not** store secrets or tokens.
- Keep `.env` on the server (already in `.gitignore`).