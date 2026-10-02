import { useParams } from 'react-router-dom';
import type {User} from "../components/types.tsx";
import RoomPage from "./RoomPage.tsx";
import {useEffect, useState} from "react";
import {comfortApi, locationApi} from "../newRestApiService.tsx";


function RoomWrapper({ user, onLogout }: { user: User | null, onLogout: () => void }) {
    const { locationId, roomId } = useParams<{ locationId: string; roomId: string }>();
    const [roomData, setRoomData] = useState<any>(null);
    const [recommendations, setRecommendations] = useState<string[] | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token') || "";
        if (!locationId || !roomId) return;

        const fetchMetrics = async (isInitialLoad: boolean) => {
            try {
                const [locData, sensorData, comfortData] = await Promise.all([
                    locationApi.get(locationId, token),
                    comfortApi.getLatestSensors(roomId, token),
                    comfortApi.getComfortLevel(roomId, token),
                ]);

                const room = {
                    id: roomId,
                    name: sensorData.name || `Room ${roomId.substring(0, 5)}`,
                    hideRoom: sensorData.hidden,
                    location: {
                        id: locationId,
                        name: locData.name,
                        adminId: locData.adminId
                    },
                    metrics: {
                        comfortIndex: comfortData.comfortPercentage,
                        temperature: sensorData.latestReading?.temperature,
                        humidity: sensorData.latestReading?.humidity,
                        co2: sensorData.latestReading?.gas,
                        lighting: sensorData.latestReading?.light,
                        noise: sensorData.latestReading?.sound,
                    }
                };

                setRoomData(room);
                if (isInitialLoad) setIsLoading(false);
            } catch (err) {
                console.error("Polling error:", err);
                if (isInitialLoad) setIsLoading(false);
            }
        };

        const fetchAdvice = () => {
            comfortApi.getRecommendations(roomId, token)
                .then(recData => setRecommendations(recData.recommendations.map(r => r.message)))
                .catch(() => setRecommendations([]));
        };

        fetchMetrics(true);
        fetchAdvice();

        // 2. Setup Polling for metrics (every 10 seconds)
        const metricsInterval = setInterval(() => {
            fetchMetrics(false);
        }, 10000);

        // 3. Setup Polling for AI (every 2 minutes, optional)
        const adviceInterval = setInterval(fetchAdvice, 120000);

        return () => {
            clearInterval(metricsInterval);
            clearInterval(adviceInterval);
        };
    }, [locationId, roomId]);

    if (isLoading) return <div className="loading-screen">Connecting to sensor...</div>;
    if (!roomData) return <div className="error">Room not found.</div>;

    return (
        <RoomPage
            user={user}
            room={roomData}
            advice={recommendations}
            onLogout={onLogout}
        />
    );
}

export default RoomWrapper;