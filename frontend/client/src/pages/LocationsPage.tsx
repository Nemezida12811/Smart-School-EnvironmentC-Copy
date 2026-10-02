import HeaderLogged from "../components/HeaderLogged";
import HeaderUnlogged from "../components/HeaderUnlogged";
import Footer from "../components/Footer";
import SmallButton from "../components/SmallButton";
import "../components/locationSection.css";
import type {User, Location} from "../components/types.tsx";
import LocationSection from "../components/LocationSection.tsx";
import {useNavigate} from "react-router-dom";
import {useEffect, useState} from "react";
import {comfortApi, locationApi} from "../newRestApiService.tsx";

type LocationsPageProps = {
    user: User | null;
    onLogout: () => void
};

function LocationsPage({user, onLogout}: LocationsPageProps) {
    const navigate = useNavigate();
    const [createdLocations, setCreatedLocations] = useState<Location[]>([]);
    const [joinedLocations, setJoinedLocations] = useState<Location[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchLocations = async () => {
            const token = localStorage.getItem('token');
            if (!token) {
                setIsLoading(false);
                return;
            }

            try {
                const result = await locationApi.list(token);

                const inflateLocation = async (loc: any): Promise<Location> => {
                    const roomPromises = loc.deviceIds.map(async (deviceId: string) => {
                        try {
                            const sensorData = await comfortApi.getLatestSensors(deviceId, token);
                            const comfortData = await comfortApi.getComfortLevel(deviceId, token);

                            return {
                                id: deviceId,
                                // Use the NEW name field from the API
                                name: sensorData.name || `Room ${deviceId.substring(0, 5)}`,
                                metrics: {
                                    comfortIndex: comfortData.comfortPercentage,
                                },
                                // Use the NEW hidden field from the API
                                hideRoom: sensorData.hidden || false
                            };
                        } catch (err) {
                            return null;
                        }
                    });

                    const rooms = (await Promise.all(roomPromises)).filter(r => r !== null);

                    return {
                        ...loc,
                        adminId: loc.adminId,
                        rooms: rooms
                    };
                };

                // Process all created and joined locations in parallel
                const [inflatedCreated, inflatedJoined] = await Promise.all([
                    Promise.all(result.created.map(inflateLocation)),
                    Promise.all(result.joined.map(inflateLocation))
                ]);

                setCreatedLocations(inflatedCreated);
                setJoinedLocations(inflatedJoined);

            } catch (error) {
                console.error("Fetch error:", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchLocations();
    }, [user]);


//джоинд только те что видны всем


    if (isLoading) {
        return <div className="loading-screen">Loading your locations...</div>;
    }


    return (
        <div className="locations-page">
            {user ? <HeaderLogged username={user.username} onLogout={onLogout}
                                  onLogoClick={() => navigate('/locations')}/> :
                <HeaderUnlogged onLoginClick={() => navigate('/login')} onLogoClick={() => navigate('/locations')}/>}

            <main className="locations-content">
                <div className="page-header">
                    <div>
                        <h1 className="page-header-title">Locations</h1>
                        <p className="subtitle">
                            Comfort Index (%) – overall quality of learning conditions in the room
                        </p>
                    </div>

                    <SmallButton text="New location" image="plus" onClick={() => navigate('/locations/new')}/>
                </div>

                <LocationSection
                    title="Created locations"
                    locations={createdLocations}
                />

                <LocationSection
                    title="Joined locations"
                    locations={joinedLocations}
                />

                <div className="center-action">
                    <SmallButton text="New location" image="plus" onClick={() => navigate('/locations/new')}/>
                </div>
            </main>

            <Footer/>
        </div>
    );
}

export default LocationsPage;
