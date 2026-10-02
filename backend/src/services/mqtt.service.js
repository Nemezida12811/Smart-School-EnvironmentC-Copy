import { TOPIC_PARSERS } from '../mqtt/mqtt.topics.js';
import SensorReading from '../db/models/SensorReading.js';

class MqttService {

    async handleMessage(topic, message) {
        try {
            const payload = JSON.parse(message.toString());
            const deviceId = TOPIC_PARSERS.getDeviceId(topic);

            if (!deviceId) {
                console.log('📩 MQTT message (unknown source)', { topic, payload });
                return;
            }

            let telemetry = this.parseTelemetry(payload);
            console.log(`📩 Device ${deviceId} telemetry`, telemetry);

            if (!this.isValidTelemetry(telemetry)) {
                console.warn(`⚠️ Invalid telemetry data from ${deviceId}`, telemetry);
                return;
            }

            telemetry = this.convertTelemetryUnits(telemetry);

            try {
                const reading = new SensorReading({
                    deviceId,
                    ...telemetry
                });
                await reading.save();
                console.log(`✅ Saved telemetry for ${deviceId}`);
            } catch (saveErr) {
                console.error(`❌ Failed to save telemetry for ${deviceId}:`, saveErr);
            }

        } catch (err) {
            console.error('❌ Invalid MQTT message', err.message);
        }
    }

    convertTelemetryUnits(data) {
        const RAW_MAX = 65535;

        // Helper for linear mapping
        const mapValue = (val, targetMin, targetMax) => {
            if (isNaN(val)) return val;
            return targetMin + (val / RAW_MAX) * (targetMax - targetMin);
        };

        // Газ: 0-65535 -> 200-10000
        data.gas = Math.round(mapValue(data.gas, 200, 10000));

        // Шум: 0-65535 -> 40-120 dB
        data.sound = Math.round(mapValue(data.sound, 40, 120));

        // Свет: 0-65535 -> 0.1-100,000 lux
        data.light = Number(mapValue(data.light, 0.1, 100000).toFixed(1));

        return data;
    }

    parseTelemetry(payload) {
        const s = payload.sensors || {};
        return {
            temperature: s.temperature?.value !== undefined ? Number(s.temperature.value) : NaN,
            humidity: s.humidity?.value !== undefined ? Number(s.humidity.value) : NaN,
            gas: s.gas?.value !== undefined ? Number(s.gas.value) : NaN,
            light: s.light?.value !== undefined ? Number(s.light.value) : NaN,
            sound: s.sound?.value !== undefined ? Number(s.sound.value) : NaN,
            units: {
                temperature: s.temperature?.units,
                humidity: s.humidity?.units,
                gas: s.gas?.units,
                light: s.light?.units,
                sound: s.sound?.units
            },
            timestamp: payload.timestamp ? Number(payload.timestamp) * 1000 : Date.now()
        };
    }

    isValidTelemetry(data) {
        return (
            !isNaN(data.temperature) &&
            !isNaN(data.humidity) &&
            !isNaN(data.gas) &&
            !isNaN(data.light) &&
            !isNaN(data.sound) &&
            !!data.units.temperature &&
            !!data.units.humidity &&
            !!data.units.gas &&
            !!data.units.light &&
            !!data.units.sound
        );
    }

}

export default new MqttService();
