import {useParams} from 'react-router-dom';
import AddRoom from "./AddRoom.tsx";
import type {Location} from "../components/types.tsx";
import {useEffect, useState} from "react";
import {locationApi} from "../newRestApiService.tsx";


function AddRoomWrapper({ user, onLogout }: any) {
    const { locationId } = useParams();
    const [myLocations, setMyLocations] = useState<Location[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchLocations = async () => {
            const token = localStorage.getItem('token');
            if (!token) return;

            try {
                // We fetch the list to get all locations the user owns
                const result = await locationApi.list(token);
                setMyLocations(result.created); // Only allow adding rooms to "created" locations
            } catch (error) {
                console.error("Error fetching locations for dropdown:", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchLocations();
    }, []);

    if (isLoading) return <div className="loading-screen">Loading locations...</div>;

    return (
        <AddRoom
            user={user}
            currentLocationId={locationId}
            availableLocations={myLocations}
            onLogout={onLogout}
        />
    );
}
export default AddRoomWrapper;