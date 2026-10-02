import { MongoClient, ServerApiVersion } from 'mongodb';

class Database {
    constructor() {
        this.client = null;
        this.db = null;
    }

    async connect() {
        try {
            const uri = process.env.MONGO_URI;

            if (!uri) {
                throw new Error('MONGO_URI not found in environment variables');
            }

            this.client = new MongoClient(uri, {
                serverApi: {
                    version: ServerApiVersion.v1,
                    strict: true,
                    deprecationErrors: true,
                }
            });

            await this.client.connect();
            await this.client.db("admin").command({ ping: 1 });

            this.db = this.client.db("iotProj");

            console.log("✅ Successfully connected to MongoDB!");
            return this.db;
        } catch (error) {
            console.error("❌ MongoDB connection error:", error);
            throw error;
        }
    }

    async disconnect() {
        if (this.client) {
            await this.client.close();
            console.log("MongoDB connection closed");
        }
    }

    getDb() {
        if (!this.db) {
            throw new Error('Database not initialized. Call connect() first.');
        }
        return this.db;
    }

    getCollection(name) {
        return this.getDb().collection(name);
    }
}

export default new Database();
