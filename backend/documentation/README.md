# Backend Setup

## Requirements
- Node.js (LTS)
- MongoDB
- MQTT Broker

## Install
```bash
npm install
```

## Run (dev mode)
```bash
npm run dev
```

## Run (production)
```bash
npm start
```

---

## Documentation

For detailed information on communication and integration, please refer to:

- [REST API Documentation (REST.md)](file:///e:/repos/iotProj-backend/REST.md) - Endpoints, request/response formats, and examples.
- [MQTT Documentation (MQTT.md)](file:///e:/repos/iotProj-backend/MQTT.md) - Topics, telemetry payload formats, and edge device communication.

## Integration Examples

- **Frontend**: [restApiService_example.ts](file:///e:/repos/iotProj-backend/restApiService_example.ts) (TypeScript)
- **Devices**: [mqttDeviceCommunication_example.py](file:///e:/repos/iotProj-backend/mqttDeviceCommunication_example.py) (MicroPython)
