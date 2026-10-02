import database from '../database.js';
import bcrypt from 'bcrypt';

class User {
    constructor(data) {
        this.username = data.username;
        this.email = data.email;
        this.password = data.password;
        this.role = data.role || 'user';
        this.ownedLocationIds = (data.ownedLocationIds || []).map(id => new ObjectId(id));
        this.accessibleLocationIds = (data.accessibleLocationIds || []).map(id => new ObjectId(id));
        this.createdAt = data.createdAt || new Date();
    }

    static getCollection() {
        return database.getCollection('users');
    }

    async save() {
        const collection = User.getCollection();

        const salt = await bcrypt.genSalt(10);
        this.password = await bcrypt.hash(this.password, salt);

        const result = await collection.insertOne({
            username: this.username,
            email: this.email,
            password: this.password,
            role: this.role,
            ownedLocationIds: this.ownedLocationIds,
            accessibleLocationIds: this.accessibleLocationIds,
            createdAt: this.createdAt
        });

        return result;
    }

    static async findByEmail(email) {
        const collection = User.getCollection();
        return await collection.findOne({ email });
    }

    static async findById(id) {
        const collection = User.getCollection();
        const { ObjectId } = await import('mongodb');
        return await collection.findOne({ _id: new ObjectId(id) });
    }

    static async addOwnedLocation(userId, locationId) {
        const collection = User.getCollection();
        const { ObjectId } = await import('mongodb');
        return await collection.updateOne(
            { _id: new ObjectId(userId) },
            { $addToSet: { ownedLocationIds: new ObjectId(locationId) } }
        );
    }

    static async addAccessibleLocation(userId, locationId) {
        const collection = User.getCollection();
        const { ObjectId } = await import('mongodb');
        return await collection.updateOne(
            { _id: new ObjectId(userId) },
            { $addToSet: { accessibleLocationIds: new ObjectId(locationId) } }
        );
    }

    static async removeOwnedLocation(userId, locationId) {
        const collection = User.getCollection();
        const { ObjectId } = await import('mongodb');
        return await collection.updateOne(
            { _id: new ObjectId(userId) },
            { $pull: { ownedLocationIds: new ObjectId(locationId) } }
        );
    }

    static async removeAccessibleLocation(userId, locationId) {
        const collection = User.getCollection();
        const { ObjectId } = await import('mongodb');
        return await collection.updateOne(
            { _id: new ObjectId(userId) },
            { $pull: { accessibleLocationIds: new ObjectId(locationId) } }
        );
    }

    static async comparePassword(plainPassword, hashedPassword) {
        return await bcrypt.compare(plainPassword, hashedPassword);
    }

    static toJSON(user) {
        return {
            id: user._id.toString(),
            username: user.username,
            email: user.email,
            role: user.role,
            ownedLocationIds: (user.ownedLocationIds || []).map(id => id.toString()),
            accessibleLocationIds: (user.accessibleLocationIds || []).map(id => id.toString()),
            createdAt: user.createdAt
        };
    }
}

export default User;
