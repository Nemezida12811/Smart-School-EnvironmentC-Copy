import { useParams} from 'react-router-dom';
import EditLocation from "./EditLocation.tsx";
import type {User, Location} from "../components/types.tsx";
import {useEffect, useState} from "react";
import {locationApi} from "../newRestApiService.tsx";

function EditLocationWrapper({ user, onLogout }: { user: User | null, onLogout: () => void }) {
    const { locationId } = useParams();
    const [location, setLocation] = useState<Location | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchLocation = async () => {
            const token = localStorage.getItem('token');
            if (!locationId) return;

            try {
                // Fetch real data from the backend
                const data = await locationApi.get(locationId, token || "");
                setLocation(data);
            } catch (err) {
                console.error("Failed to load location for editing", err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchLocation();
    }, [locationId]);

    if (isLoading) return <div className="loading-screen">Loading...</div>;
    if (!location) return <div>Location not found</div>;

    return (
        <EditLocation
            user={user!}
            location={location}
            onLogout={onLogout}
        />
    );
}
export default EditLocationWrapper;