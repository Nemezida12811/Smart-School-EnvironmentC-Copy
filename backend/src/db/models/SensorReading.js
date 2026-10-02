import database from '../database.js';

class SensorReading {
    constructor(data) {
        this.deviceId = data.deviceId;
        this.name = data.name || "";
        this.hidden = data.hidden ?? false;
        this.temperature = data.temperature;
        this.humidity = data.humidity;
        this.gas = data.gas;
        this.light = data.light;
        this.sound = data.sound;
        this.units = data.units || {};
        this.timestamp = new Date(data.timestamp || Date.now());
    }

    static getCollection() {
        return database.getCollection('sensor_readings');
    }

    async save() {
        const collection = SensorReading.getCollection();

        try {
            const result = await collection.updateOne(
                { deviceId: this.deviceId },
                {
                    $set: {
                        temperature: this.temperature,
                        humidity: this.humidity,
                        gas: this.gas,
                        light: this.light,
                        sound: this.sound,
                        units: this.units,
                        timestamp: this.timestamp,
                        updatedAt: new Date()
                    },
                    $setOnInsert: {
                        deviceId: this.deviceId,
                        name: this.name,
                        hidden: this.hidden
                    }
                },
                { upsert: true }
            );

            return result;
        } catch (error) {
            console.error(`❌ [DB] Error saving sensor reading for ${this.deviceId}:`, error);
            throw error;
        }
    }

    static async findByDeviceId(deviceId, limit = 100) {
        const collection = SensorReading.getCollection();
        return await collection.find({ deviceId })
            .sort({ timestamp: -1 })
            .limit(limit)
            .toArray();
    }

    static async findLatestByDeviceId(deviceId) {
        const collection = SensorReading.getCollection();
        return await collection.findOne(
            { deviceId },
            { sort: { timestamp: -1 } }
        );
    }

    static async updateMetadata(deviceId, metadata) {
        const collection = SensorReading.getCollection();
        return await collection.updateOne(
            { deviceId },
            { $set: { ...metadata, updatedAt: new Date() } }
        );
    }

    static async exists(deviceId) {
        const collection = SensorReading.getCollection();
        const count = await collection.countDocuments({ deviceId }, { limit: 1 });
        return count > 0;
    }

}

export default SensorReading;
