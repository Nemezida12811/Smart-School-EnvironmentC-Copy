import SensorReading from '../db/models/SensorReading.js';
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({
    apiKey: process.env.GOOGLE_API_KEY
});

class ComfortService {

    async calculateComfortByAudience(audienceId) {
        const deviceId = audienceId;
        const latest = await SensorReading.findLatestByDeviceId(deviceId);
        if (!latest) return null;

        const comfortPercentage = this._calculateManualComfort(latest);

        return {
            audienceId: deviceId,
            comfortPercentage: comfortPercentage,
            timestamp: latest.timestamp
        };
    }

    _calculateManualComfort(latest) {
        const metrics = [
            { val: latest.temperature, range: [20, 24], threshold: 5 },
            { val: latest.humidity, range: [30, 60], threshold: 30 },
            { val: latest.gas, range: [400, 1000], threshold: 1000 },
            { val: latest.light, range: [300, 1000], threshold: 500 },
            { val: latest.sound, range: [0, 50], threshold: 40 }
        ];

        let totalScore = 0;
        metrics.forEach(m => {
            let score = 1.0;
            if (m.val < m.range[0]) {
                score = 1 - (m.range[0] - m.val) / m.threshold;
            } else if (m.val > m.range[1]) {
                score = 1 - (m.val - m.range[1]) / m.threshold;
            }
            totalScore += Math.max(0, Math.min(1, score));
        });

        return Math.round((totalScore / metrics.length) * 100);
    }

    async generateTips(audienceId) {
        const deviceId = audienceId;
        const latest = await SensorReading.findLatestByDeviceId(deviceId);
        if (!latest) return null;

        const tips = [];

        try {
            const response = await ai.models.generateContent({
                model: "gemini-3-flash-preview",
                contents: [
                    {
                        role: "user",
                        parts: [{
                            text: `Hi. You are an indoor comfort inspector. You have the following sensor data:
                                Temperature: ${latest.temperature} ${latest.units.temperature}
                                Humidity: ${latest.humidity} ${latest.units.humidity}
                                Gas (Air Quality): ${latest.gas} ${latest.units.gas}
                                Light: ${latest.light} ${latest.units.light}
                                Sound (Noise): ${latest.sound} ${latest.units.sound}

                                Ideal ranges: Temperature (20-24), Humidity (30-60%), Gas (400-1000 ppm), Light (300-1000 lx), Sound (0-50 dB).
                                
                                Based on this data, generate a list of 2-3 specific recommendations to improve comfort. 
                                Return ONLY a JSON array of objects with the following format:
                                [{"priority": "high"|"medium"|"low", "type": "temperature"|"humidity"|"gas"|"light"|"sound", "message": "recommendation text", "reason": "why this is important"}]
                                `
                        }]
                    }
                ]
            });

            const text = response.candidates[0].content.parts[0].text;
            const cleanJson = text.replace(/```json|```/g, '').trim();
            return JSON.parse(cleanJson);
        } catch (error) {
            console.error('❌ [AI] Error generating tips:', error);
            return [];
        }
    }
}

export default new ComfortService();