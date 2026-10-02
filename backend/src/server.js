import express from "express";
import AuthRoutes from "./routes/auth.routes.js";
import LocationRoutes from "./routes/location.routes.js";
import ComfortRoutes from "./routes/comfort.routes.js";
import mqttClient from "./mqtt/mqtt.client.js";
import MqttService from "./services/mqtt.service.js";
import database from "./db/database.js";
import cors from "cors";

const allowedOrigins = [];

function createApp() {
    const app = express();

    app.use(cors({
        // origin: allowedOrigins,
        // credentials: true,
    }));
    app.use(express.json()); // Middleware
    setupRoutes(app);

    app.get("/", (req, res) => {
        res.json({ message: "Backend is running" });
    });

    mqttClient.initialize((topic, message) => {
        MqttService.handleMessage(topic, message);
    });

    database.connect().catch(err => {
        console.error('Failed to connect to MongoDB:', err);
    });

    return app;
}

function setupRoutes(app) {
    const authRoutes = new AuthRoutes();
    authRoutes.registerRoutes(app);

    const comfortRoutes = new ComfortRoutes();
    comfortRoutes.registerRoutes(app);

    const locationRoutes = new LocationRoutes();
    locationRoutes.registerRoutes(app);
}

export default createApp;
