import {useParams, Navigate} from 'react-router-dom';
import EditRoom from "./EditRoom.tsx";
import {useEffect, useState} from "react";
import {comfortApi, locationApi} from "../newRestApiService.tsx";

function EditRoomWrapper({ user, onLogout }: any) {
    const { locationId, roomId } = useParams();
    const [room, setRoom] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            const token = localStorage.getItem('token') || "";
            if (!locationId || !roomId) return;
            try {
                const sensorData = await comfortApi.getLatestSensors(roomId, token);
                const locData = await locationApi.get(locationId, token);

                setRoom({
                    id: roomId,
                    name: sensorData.name,
                    location: { id: locationId, name: locData.name }
                });
            } catch (err) {
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [locationId, roomId]);

    if (!user) return <Navigate to="/login" />;
    if (isLoading) return <div className="loading-screen">Loading room configuration...</div>;
    if (!room) return <div>Room not found</div>;

    return <EditRoom user={user} room={room} onLogout={onLogout} />;
}
export default EditRoomWrapper;