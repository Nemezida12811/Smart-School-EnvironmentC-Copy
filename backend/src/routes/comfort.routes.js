import BaseRoute from './base-route.js';
import SensorReading from '../db/models/SensorReading.js';
import ComfortService from '../services/comfort.service.js';

class ComfortRoutes extends BaseRoute {
    constructor() {
        super();
        this.setupRoutes();
    }

    setupRoutes() {
        // GET /api/comfort/:audienceId - Get comfort percentage for specific audience
        this.getComfortLevel = async (req, res) => {
            console.log('GET /api/comfort/:audienceId', { audienceId: req.params.audienceId });
            try {
                const { audienceId } = req.params;

                const result = await ComfortService.calculateComfortByAudience(audienceId);
                if (!result) {
                    return this.sendError(res, 404, 'No sensor data found');
                }

                this.sendSuccessResponse(res, result);
            } catch (error) {
                console.error('❌ Error getting comfort level:', error);
                this.sendError(res, 500, 'Failed to get comfort level', {
                    message: error.message
                });
            }
        };

        // GET /api/comfort/:audienceId/recommendations - Get comfort improvement recommendations
        this.getRecommendations = async (req, res) => {
            console.log('GET /api/comfort/:audienceId/recommendations', { audienceId: req.params.audienceId });
            try {
                const { audienceId } = req.params;

                const recommendations = await ComfortService.generateTips(audienceId);
                if (!recommendations) {
                    return this.sendError(res, 404, 'No recommendations found');
                }

                this.sendSuccessResponse(res, {
                    audienceId: parseInt(audienceId),
                    recommendations: recommendations,
                    generatedAt: new Date().toISOString(),
                });
            } catch (error) {
                console.error('❌ Error getting recommendations:', error);
                this.sendError(res, 500, 'Failed to get recommendations', {
                    message: error.message
                });
            }
        };

        // GET /api/comfort/:deviceId/sensors - Get last sensor measurements for device
        this.getSensorData = async (req, res) => {
            console.log('GET /api/comfort/:deviceId/sensors', { deviceId: req.params.deviceId });
            try {
                const { deviceId } = req.params;

                const latestReading = await SensorReading.findLatestByDeviceId(deviceId);
                if (!latestReading) {
                    return this.sendError(res, 404, 'No sensor data found for this device');
                }

                this.sendSuccessResponse(res, {
                    deviceId: deviceId,
                    name: latestReading.name || "",
                    hidden: latestReading.hidden ?? false,
                    latestReading: {
                        temperature: latestReading.temperature,
                        humidity: latestReading.humidity,
                        gas: latestReading.gas,
                        light: latestReading.light,
                        sound: latestReading.sound,
                        units: latestReading.units
                    },
                    timestamp: latestReading.timestamp
                });
            } catch (error) {
                console.error('❌ Error getting sensor data:', error);
                this.sendError(res, 500, 'Failed to get sensor data', {
                    message: error.message
                });
            }
        };
    }

    registerRoutes(app) {
        app.get('/api/comfort/:audienceId', this.getComfortLevel.bind(this));
        app.get('/api/comfort/:audienceId/recommendations', this.getRecommendations.bind(this));
        app.get('/api/comfort/:deviceId/sensors', this.getSensorData.bind(this));
    }
}

export default ComfortRoutes;
