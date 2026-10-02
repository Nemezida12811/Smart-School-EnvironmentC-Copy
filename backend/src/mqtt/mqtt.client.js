import mqtt from 'mqtt';
import { MQTT_TOPICS } from './mqtt.topics.js';

class MqttClient {
    constructor() {
        this.client = null;
        this.messageHandler = null;
    }

    initialize(onMessage) {
        this.messageHandler = onMessage;

        this.client = mqtt.connect(process.env.MQTT_URL, {
            clientId: process.env.MQTT_CLIENT_ID,
            clean: true,
            reconnectPeriod: 3000,

            will: {
                topic: MQTT_TOPICS.BACKEND_STATUS,
                payload: JSON.stringify({
                    status: 'offline',
                    ts: Date.now()
                }),
                qos: 1,
                retain: true
            }
        });

        this.client.on('connect', () => {
            console.log('✅ MQTT connected');

            this.client.publish(
                MQTT_TOPICS.BACKEND_STATUS,
                JSON.stringify({
                    status: 'online',
                    ts: Date.now()
                }),
                { qos: 1, retain: true }
            );

            this.setupSubscriptions();
        });

        // this.client.publish(
        //     'iot/backend/com-de6c1bd8f65bcff7-fort/settings',
        //     JSON.stringify({
        //         "user": { "login": "Admin", "password": "4444" },
        //         "mqtt": { "server": "broker.hivemq.com" },
        //         "measurement_interval": 10000,
        //         "wifi": { "ssid": "Komiki", "password": "Parol222" },
        //         "units": "standard",
        //         "ntp_host": "pool.ntp.org",
        //         "id": "com-de6c1bd8f65bcff7-fort"
        //     }),
        //     { qos: 1, retain: true }
        // );


        this.client.on('message', (topic, message) => {
            if (this.messageHandler) {
                this.messageHandler(topic, message);
            }
        });

        this.client.on('error', (err) => {
            console.error('❌ MQTT error', err.message);
        });
    }

    setupSubscriptions() {
        this.client.subscribe(
            MQTT_TOPICS.TELEMETRY,
            { qos: 1 },
            (err) => {
                if (err) {
                    console.error('❌ MQTT subscribe error', MQTT_TOPICS.TELEMETRY);
                }
            }
        );
    }

    publish(topic, payload, options = { qos: 1 }) {
        if (!this.client) return;
        const message = typeof payload === 'object' ? JSON.stringify(payload) : payload;
        this.client.publish(
            topic,
            message,
            options
        );
    }
}

export default new MqttClient();
