export const MQTT_TOPICS = {
    TELEMETRY: 'iot/device/+/telemetry',
    BACKEND_STATUS: 'iot/backend/status',
};

export const TOPIC_PARSERS = {
    getDeviceId: (topic) => {
        const match = topic.match(/^iot\/device\/([^\/]+)\/telemetry$/);
        return match ? match[1] : null;
    }
};
