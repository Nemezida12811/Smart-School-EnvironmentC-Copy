from lib.simple import MQTTClient # <- your path to lib

import time
import json
import network

# WI-FI
ssid = "iPhone (Никита)"
password = "1234555565"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
print("WiFi OK")

# MQTT
BROKER = "broker.hivemq.com"
CLIENT_ID = "pico-001"
TOPIC = b"iot/device/pico-001/telemetry"

client = MQTTClient(CLIENT_ID, BROKER)
client.connect()
print("MQTT connected")

# SEND DATA
while True:
    payload = {
        "sensors": {
            "light": {
                "value": 1120,
                "units": "lx"
            },
            "sound": {
                "value": 50,
                "units": "dB"
            },
            "gas": {
                "value": 400,
                "units": "ppm"
            },
            "temperature": {
                "value": 23.4,
                "units": "standard"
            },
            "humidity": {
                "value": 41,
                "units": "%"
            }
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    client.publish(TOPIC, json.dumps(payload))
    print("Published:", payload)
    time.sleep(5)

