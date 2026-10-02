import database from '../database.js';
import { ObjectId } from 'mongodb';

class Location {
    constructor(data) {
        this.name = data.name;
        this.adminId = data.adminId ? new ObjectId(data.adminId) : null;
        this.userIds = (data.userIds || []).map(id => new ObjectId(id));
        this.deviceIds = data.deviceIds || [];
        this.createdAt = data.createdAt || new Date();
    }

    static getCollection() {
        return database.getCollection('locations');
    }

    async save() {
        const collection = Location.getCollection();
        const result = await collection.insertOne({
            name: this.name,
            adminId: this.adminId,
            userIds: this.userIds,
            deviceIds: this.deviceIds,
            createdAt: this.createdAt
        });
        return result;
    }

    static async findById(id) {
        const collection = Location.getCollection();
        return await collection.findOne({ _id: new ObjectId(id) });
    }

    static async findAll() {
        const collection = Location.getCollection();
        return await collection.find({}).toArray();
    }

    static async findByAdminId(adminId) {
        const collection = Location.getCollection();
        return await collection.find({ adminId: new ObjectId(adminId) }).toArray();
    }

    static async findByUserId(userId) {
        const collection = Location.getCollection();
        return await collection.find({ userIds: new ObjectId(userId) }).toArray();
    }

    static async update(id, data) {
        const collection = Location.getCollection();
        return await collection.updateOne(
            { _id: new ObjectId(id) },
            { $set: data }
        );
    }

    static async delete(id) {
        const collection = Location.getCollection();
        return await collection.deleteOne({ _id: new ObjectId(id) });
    }

    static async addUser(locationId, userId) {
        const collection = Location.getCollection();
        return await collection.updateOne(
            { _id: new ObjectId(locationId) },
            { $addToSet: { userIds: new ObjectId(userId) } }
        );
    }

    static async removeUser(locationId, userId) {
        const collection = Location.getCollection();
        return await collection.updateOne(
            { _id: new ObjectId(locationId) },
            { $pull: { userIds: new ObjectId(userId) } }
        );
    }

    static async addDevice(locationId, deviceId) {
        const collection = Location.getCollection();
        return await collection.updateOne(
            { _id: new ObjectId(locationId) },
            { $addToSet: { deviceIds: deviceId } }
        );
    }

    static async removeDevice(locationId, deviceId) {
        const collection = Location.getCollection();
        return await collection.updateOne(
            { _id: new ObjectId(locationId) },
            { $pull: { deviceIds: deviceId } }
        );
    }

    static toJSON(location) {
        return {
            id: location._id.toString(),
            name: location.name,
            adminId: location.adminId.toString(),
            userIds: location.userIds.map(id => id.toString()),
            deviceIds: location.deviceIds,
            createdAt: location.createdAt
        };
    }
}

export default Location;
