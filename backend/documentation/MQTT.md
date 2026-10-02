# MQTT Documentation

Information about MQTT communication protocols and payload formats.

## Configuration
The backend connects to an MQTT broker defined by the `MQTT_URL` environment variable.

---

## Topics

### 1. Backend Status
**Topic**: `iot/backend/status`
**Direction**: Backend -> Broker
**Payload**:
```json
{
  "status": "online", // or "offline"
  "ts": 1734360000000
}
```

### 2. Device Telemetry
**Topic**: `iot/device/+/telemetry`
**Direction**: Device -> Backend
**Wildcard**: `+` represents the `deviceId` (e.g., `pico-001`).

**Payload**:
```json
{
    "temperature": 23.4,
    "humidity": 41,
    "co2": 400,
    "light": 100,
    "noise": 50,
    "ts": 1765978387
}
```

---

## Example Implementation
For MicroPython (Raspberry Pi Pico) implementation, see [mqttDeviceCommunication_example.py](file:///e:/repos/iotProj-backend/mqttDeviceCommunication_example.py).
