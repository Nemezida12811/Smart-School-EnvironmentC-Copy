import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import LocationDetailsPage from "./LocationDetailsPage.tsx";
import type { User, Location } from "../components/types.tsx";
import {comfortApi, locationApi} from "../newRestApiService.tsx";

function LocationDetailsWrapper({ user, onLogout }: { user: User | null, onLogout: () => void }) {
    const { locationId } = useParams();
    const navigate = useNavigate();

    // Separate states for the header and the room content
    const [location, setLocation] = useState<Location | null>(null);
    const [rooms, setRooms] = useState<any[]>([]);
    const [isInitialLoading, setIsInitialLoading] = useState(true);
    const [isRoomsLoading, setIsRoomsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchLocationStructure = async () => {
            const token = localStorage.getItem('token') || "";
            if (!locationId) return;

            try {
                setIsInitialLoading(true);

                // 1. FAST CALL: Just get the location name and admin info
                const locData = await locationApi.get(locationId, token);
                setLocation(locData);

                // Show the page immediately now that we have the header info
                setIsInitialLoading(false);

                // 2. SLOW CALLS: Start fetching rooms in the background
                if (locData.deviceIds && locData.deviceIds.length > 0) {
                    setIsRoomsLoading(true);

                    const roomPromises = locData.deviceIds.map(async (deviceId: string) => {
                        try {
                            const sensorData = await comfortApi.getLatestSensors(deviceId, token);
                            const comfortData = await comfortApi.getComfortLevel(deviceId, token);

                            return {
                                id: deviceId,
                                name: sensorData.name || `Room ${deviceId.substring(0, 5)}`,
                                metrics: {
                                    comfortIndex: comfortData.comfortPercentage,
                                },
                                hideRoom: sensorData.hidden || false
                            };
                        } catch (err) {
                            console.error(`Failed room ${deviceId}`, err);
                            return null;
                        }
                    });

                    const resolvedRooms = (await Promise.all(roomPromises)).filter(r => r !== null);
                    setRooms(resolvedRooms);
                    setIsRoomsLoading(false);
                }

            } catch (err: any) {
                setError(err.message);
                setIsInitialLoading(false);
            }
        };

        fetchLocationStructure();
    }, [locationId]);

    // Only show the big loading screen for the initial Location Name fetch
    if (isInitialLoading) return <div className="loading-screen">Loading location...</div>;

    if (error || !location) {
        return (
            <div className="error-screen">
                <h2>{error || "Location not found"}</h2>
                <button onClick={() => navigate('/locations')}>Back to Locations</button>
            </div>
        );
    }

    return (
        <LocationDetailsPage
            user={user}
            location={{ ...location, rooms }}
            isRoomsLoading={isRoomsLoading}
            onLogout={onLogout}
        />
    );
}

export default LocationDetailsWrapper;