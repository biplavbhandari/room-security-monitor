#!/usr/bin/env python3
"""
Room Security MQTT Subscriber
Receives ESP32 sensor data -> writes to InfluxDB -> checks thresholds -> alerts via SNS
"""

import json
import time
import boto3
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

# ── CONFIGURATION — FILL IN YOUR VALUES ─────────────────────
INFLUX_URL    = "http://localhost:8086"
INFLUX_TOKEN  = "PASTE_YOUR_INFLUXDB_TOKEN_HERE"
INFLUX_ORG    = "IslingtonCollege"
INFLUX_BUCKET = "room_security"

SNS_TOPIC_ARN = "PASTE_YOUR_SNS_TOPIC_ARN_HERE"
AWS_REGION    = "us-east-1"   # change to your sandbox region

MQTT_BROKER   = "localhost"
MQTT_PORT     = 1883
MQTT_TOPIC    = "room/sensors"

# ── THRESHOLDS ───────────────────────────────────────────────
TEMP_MAX      = 30    # celsius — above this = anomaly
LIGHT_MAX     = 700   # ADC units — above this at night = anomaly
NIGHT_START   = 20    # 8pm
NIGHT_END     = 8     # 8am
# ─────────────────────────────────────────────────────────────

# Clients
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api     = influx_client.write_api(write_options=SYNCHRONOUS)
sns_client    = boto3.client("sns", region_name=AWS_REGION)

last_alert_time = 0   # prevents spam alerts

def is_night():
    h = datetime.now().hour
    return h >= NIGHT_START or h < NIGHT_END

def check_anomalies(temp, light, motion):
    anomalies = []
    if temp > TEMP_MAX:
        anomalies.append(f"TEMPERATURE SPIKE: {temp}C (threshold: {TEMP_MAX}C)")
    if motion == 1 and is_night():
        anomalies.append(f"MOTION DETECTED AT NIGHT: {datetime.now().strftime('%H:%M')}")
    if light > LIGHT_MAX and is_night():
        anomalies.append(f"LIGHT ANOMALY AT NIGHT: level {light} (threshold: {LIGHT_MAX})")
    return anomalies

def send_sns_alert(anomalies):
    global last_alert_time
    now = time.time()
    if now - last_alert_time < 300:  # 5 min cooldown between alerts
        print("Alert cooldown active — skipping SNS")
        return
    msg = "ROOM SECURITY ALERT\n\n"
    msg += "\n".join(anomalies)
    msg += f"\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    msg += "\nDevice: ESP32 Room Monitor"
    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=msg,
        Subject="ANOMALY DETECTED — Room Security Monitor"
    )
    last_alert_time = now
    print(f"SNS alert sent: {anomalies}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        temp   = float(payload.get("temp",   0))
        light  = float(payload.get("light",  0))
        motion = int(payload.get("motion",   0))
        hour   = int(payload.get("hour",     datetime.now().hour))

        print(f"Received: temp={temp}C  light={light}  motion={motion}  hour={hour}")

        # Write to InfluxDB
        point = (Point("sensor_data")
            .tag("device", "ESP32Room1")
            .field("temperature", temp)
            .field("light",       light)
            .field("motion",      motion)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print("Written to InfluxDB")

        # Check for anomalies
        anomalies = check_anomalies(temp, light, motion)
        if anomalies:
            print(f"ANOMALY DETECTED: {anomalies}")
            send_sns_alert(anomalies)
        else:
            print("Status: NORMAL")

    except Exception as e:
        print(f"Error processing message: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to Mosquitto broker on {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"Connection failed with code {rc}")

# Main
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Starting Room Security MQTT Subscriber...")
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_forever()
