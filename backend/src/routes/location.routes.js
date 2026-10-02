import { Router } from "express";
import Location from "../db/models/Location.js";
import User from "../db/models/User.js";
import SensorReading from "../db/models/SensorReading.js";
import { verifyTokenMiddleware } from "../middleware/auth.middleware.js";
import MqttClient from "../mqtt/mqtt.client.js";

class LocationRoutes {
    constructor() {
        this.router = Router();
    }

    async createLocation(req, res) {
        try {
            const { name } = req.body;
            const adminId = req.user.id;
            if (!name) {
                return res.status(400).json({ success: false, error: { message: "Name is required" } });
            }

            // Verify admin user exists
            const adminUser = await User.findById(adminId);
            if (!adminUser) {
                return res.status(404).json({ success: false, error: { message: "Admin user not found" } });
            }

            const location = new Location({
                name,
                adminId: adminId,
                userIds: [adminId], // Admin is also a user
                deviceIds: []
            });

            const result = await location.save();
            await User.addOwnedLocation(adminId, result.insertedId);
            await User.addAccessibleLocation(adminId, result.insertedId);

            res.status(201).json({
                success: true,
                data: {
                    id: result.insertedId,
                    name,
                    adminId
                }
            });
        } catch (error) {
            console.error("Error creating location:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async getLocations(req, res) {
        try {
            const userId = req.user.id;
            const locations = await Location.findByUserId(userId);

            const created = [];
            const joined = [];

            locations.forEach(loc => {
                const jsonLoc = Location.toJSON(loc);
                if (loc.adminId.toString() === userId) {
                    created.push(jsonLoc);
                } else {
                    joined.push(jsonLoc);
                }
            });

            res.json({
                success: true,
                data: {
                    created,
                    joined
                }
            });
        } catch (error) {
            console.error("Error fetching locations:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async updateLocation(req, res) {
        try {
            const userId = req.user.id;
            const { name } = req.body;
            if (!name) {
                return res.status(400).json({ success: false, error: { message: "Name is required" } });
            }

            const location = await Location.findById(req.params.id);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            if (location.adminId.toString() !== userId) {
                return res.status(403).json({ success: false, error: { message: "Only admin can update location" } });
            }

            await Location.update(req.params.id, { name });
            res.json({ success: true, data: { message: "Location updated", name } });
        } catch (error) {
            console.error("Error updating location:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async getLocation(req, res) {
        try {
            const location = await Location.findById(req.params.id);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            res.json({
                success: true,
                data: Location.toJSON(location)
            });
        } catch (error) {
            console.error("Error fetching location:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async deleteLocation(req, res) {
        try {
            const userId = req.user.id;

            const location = await Location.findById(req.params.id);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            if (location.adminId.toString() !== userId) {
                return res.status(403).json({ success: false, error: { message: "Only admin can delete location" } });
            }

            await Location.delete(req.params.id);

            // Remove from admin's owned list
            await User.removeOwnedLocation(location.adminId, req.params.id);

            // Remove from all users' accessible list
            for (const uid of location.userIds) {
                await User.removeAccessibleLocation(uid, req.params.id);
            }

            res.json({ success: true, data: { message: "Location deleted" } });
        } catch (error) {
            console.error("Error deleting location:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async addUser(req, res) {
        try {
            const userId = req.user.id;
            const { targetUserId } = req.body;
            if (!targetUserId) {
                return res.status(400).json({ success: false, error: { message: "targetUserId is required" } });
            }

            const location = await Location.findById(req.params.id);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            // if (location.adminId.toString() !== userId) {
            //     return res.status(403).json({ success: false, error: { message: "Only admin can add users" } });
            // }

            const userToAdd = await User.findById(targetUserId);
            if (!userToAdd) {
                return res.status(404).json({ success: false, error: { message: "User to add not found" } });
            }

            if (location.userIds.some(id => id.toString() === targetUserId)) {
                return res.status(400).json({ success: false, error: { message: "User already in location" } });
            }

            await Location.addUser(req.params.id, targetUserId);
            await User.addAccessibleLocation(targetUserId, req.params.id);

            res.json({ success: true, data: { message: "User added to location" } });
        } catch (error) {
            console.error("Error adding user:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async removeUser(req, res) {
        try {
            const userId = req.user.id;
            const { userId: targetUserId } = req.params;

            const location = await Location.findById(req.params.id);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            if (location.adminId.toString() !== userId) {
                return res.status(403).json({ success: false, error: { message: "Only admin can remove users" } });
            }

            if (targetUserId === location.adminId.toString()) {
                return res.status(400).json({ success: false, error: { message: "Cannot remove admin from location" } });
            }

            await Location.removeUser(req.params.id, targetUserId);
            await User.removeAccessibleLocation(targetUserId, req.params.id);

            res.json({ success: true, data: { message: "User removed from location" } });
        } catch (error) {
            console.error("Error removing user:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async addDevice(req, res) {
        try {
            const userId = req.user.id;
            const { deviceId, name } = req.body;
            if (!deviceId) {
                return res.status(400).json({ success: false, error: { message: "deviceId is required" } });
            }

            const deviceExists = await SensorReading.exists(deviceId);
            if (!deviceExists) {
                return res.status(404).json({ success: false, error: { message: "Device not found (no sensor data received yet)" } });
            }

            const location = await Location.findById(req.params.id);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            if (location.adminId.toString() !== userId) {
                return res.status(403).json({ success: false, error: { message: "Only admin can add devices" } });
            }

            await Location.addDevice(req.params.id, deviceId);

            if (name) {
                await SensorReading.updateMetadata(deviceId, { name });
            }

            res.json({ success: true, data: { message: "Device added to location" } });
        } catch (error) {
            console.error("Error adding device:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async hideDevice(req, res) {
        try {
            const userId = req.user.id;
            const { deviceId } = req.params;

            const location = await Location.findById(req.params.id);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            if (location.adminId.toString() !== userId) {
                return res.status(403).json({ success: false, error: { message: "Only admin can hide devices" } });
            }

            if (!location.deviceIds.includes(deviceId)) {
                return res.status(400).json({ success: false, error: { message: "Device is not in this location" } });
            }

            await SensorReading.updateMetadata(deviceId, { hidden: true });
            res.json({ success: true, data: { message: "Device hidden" } });
        } catch (error) {
            console.error("Error hiding device:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async showDevice(req, res) {
        try {
            const userId = req.user.id;
            const { deviceId } = req.params;

            const location = await Location.findById(req.params.id);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            if (location.adminId.toString() !== userId) {
                return res.status(403).json({ success: false, error: { message: "Only admin can show devices" } });
            }

            if (!location.deviceIds.includes(deviceId)) {
                return res.status(400).json({ success: false, error: { message: "Device is not in this location" } });
            }

            await SensorReading.updateMetadata(deviceId, { hidden: false });
            res.json({ success: true, data: { message: "Device revealed" } });
        } catch (error) {
            console.error("Error showing device:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async removeDevice(req, res) {
        try {
            const userId = req.user.id;
            const { deviceId } = req.params;

            const location = await Location.findById(req.params.id);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            if (location.adminId.toString() !== userId) {
                return res.status(403).json({ success: false, error: { message: "Only admin can remove devices" } });
            }

            await Location.removeDevice(req.params.id, deviceId);
            res.json({ success: true, data: { message: "Device removed from location" } });
        } catch (error) {
            console.error("Error removing device:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    async updateDeviceSettings(req, res) {
        try {
            const userId = req.user.id;
            const { id: locationId, deviceId } = req.params;
            const {
                name,
                units,
                ntpHost,
                brokerAddress,
                wifiSsid,
                wifiPassword,
                interval
            } = req.body;

            const location = await Location.findById(locationId);
            if (!location) {
                return res.status(404).json({ success: false, error: { message: "Location not found" } });
            }

            if (location.adminId.toString() !== userId) {
                return res.status(403).json({ success: false, error: { message: "Only admin can update device settings" } });
            }

            if (!location.deviceIds.includes(deviceId)) {
                return res.status(400).json({ success: false, error: { message: "Device is not in this location" } });
            }

            // 1. Update name in DB if provided
            if (name) {
                await SensorReading.updateMetadata(deviceId, { name });
            }

            // 2. Publish settings to MQTT
            const mqttSettings = {
                "user": { "login": "Admin", "password": "4444" },
                "mqtt": { "server": brokerAddress || "" },
                "measurement_interval": interval || 10000,
                "wifi": { "ssid": wifiSsid || "", "password": wifiPassword || "" },
                "units": units || "standard",
                "ntp_host": ntpHost || "pool.ntp.org",
                "id": deviceId
            };

            const topic = `iot/backend/${deviceId}/settings`;
            MqttClient.publish(topic, mqttSettings, { qos: 1, retain: true });

            res.json({
                success: true,
                data: {
                    message: "Device settings updated and published",
                    topic: topic,
                    settings: mqttSettings
                }
            });
        } catch (error) {
            console.error("Error updating device settings:", error);
            res.status(500).json({ success: false, error: { message: "Internal server error" } });
        }
    }

    registerRoutes(app) {
        this.router.post("/", verifyTokenMiddleware, this.createLocation.bind(this));
        this.router.get("/", verifyTokenMiddleware, this.getLocations.bind(this));

        this.router.get("/:id", this.getLocation.bind(this));
        this.router.patch("/:id", verifyTokenMiddleware, this.updateLocation.bind(this));
        this.router.delete("/:id", verifyTokenMiddleware, this.deleteLocation.bind(this));

        this.router.post("/:id/users", verifyTokenMiddleware, this.addUser.bind(this));
        this.router.delete("/:id/users/:userId", verifyTokenMiddleware, this.removeUser.bind(this));

        this.router.post("/:id/devices", verifyTokenMiddleware, this.addDevice.bind(this));
        this.router.delete("/:id/devices/:deviceId", verifyTokenMiddleware, this.removeDevice.bind(this));

        this.router.patch("/:id/devices/:deviceId/hide", verifyTokenMiddleware, this.hideDevice.bind(this));
        this.router.patch("/:id/devices/:deviceId/show", verifyTokenMiddleware, this.showDevice.bind(this));
        this.router.patch("/:id/devices/:deviceId/settings", verifyTokenMiddleware, this.updateDeviceSettings.bind(this));

        app.use("/api/locations", this.router);
    }
}

export default LocationRoutes;
