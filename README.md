# Room Security Monitor

Dockerized setup for Mosquitto (MQTT broker) and InfluxDB used in the room-security project.

## Services
- **Mosquitto** (MQTT) on port **1883**
- **InfluxDB 2.x** on port **8086**

## Quick start
```bash
docker compose up -d
```

## Test MQTT
Terminal 1:
```bash
mosquitto_sub -h localhost -t "room/sensors"
```

Terminal 2:
```bash
mosquitto_pub -h localhost -t "room/sensors" -m "test"
```

## InfluxDB UI
Open:
```
http://YOUR_EC2_PUBLIC_IP:8086
```

## Notes
- This repo does **not** store secrets or tokens.
- Add your own `.env` file if needed (kept out of Git).