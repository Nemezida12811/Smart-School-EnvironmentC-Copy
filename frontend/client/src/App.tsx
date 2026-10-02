import {ALL_LOCATIONS} from "./mockData.tsx"
import {BrowserRouter, Route, Routes, useLocation} from "react-router-dom";
import LocationsPage from "./pages/LocationsPage.tsx";
import Hero from "./pages/Hero.tsx";
import Login from "./pages/Login.tsx";
import Signup from "./pages/Signup.tsx";
import {useEffect, useState} from "react";
import type {User} from "./components/types.tsx";
import NewLocation from "./pages/NewLocation.tsx";
import LocationDetailsWrapper from "./pages/LocationDetailsWrapper.tsx";
import RoomWrapper from "./pages/RoomWrapper.tsx";
import AddRoomWrapper from "./pages/AddRoomWrapper.tsx";
import EditRoomWrapper from "./pages/EditRoomWrapper.tsx";
import {authApi} from "./newRestApiService.tsx";
import EditLocationWrapper from "./pages/EditLocationWrapper.tsx";

function ScrollToTop() {
    const { pathname } = useLocation();

    useEffect(() => {
        window.scrollTo(0, 0);
    }, [pathname]);
    return null;
}



function App() {
    const [user, setUser] = useState<User | null>(null);

    const [loading, setLoading] = useState(true);
    useEffect(() => {
        const checkLoggedIn = async () => {
            const token = localStorage.getItem('token');
            if (token) {
                try {
                    const userData = await authApi.me(token);
                    setUser(userData);
                } catch (error) {
                    console.error("Session expired");
                    localStorage.removeItem('token');
                }
            }
            setLoading(false);
        };
        checkLoggedIn();
    }, []);
    if (loading) return <div>Loading...</div>;

    const handleLogin = (userData: User) => {
        setUser(userData);
    };

    const handleLogout = () => {
        setUser(null);
        localStorage.removeItem('token');
    };

    return (
        <BrowserRouter>
            <ScrollToTop />
            <Routes>
                <Route path="/" element={<Hero />} />

                <Route path="/login" element={<Login onLogin={handleLogin} />} />
                <Route path="/signup" element={<Signup onSignup={handleLogin} />} />

                <Route path="/locations" element={
                    <LocationsPage
                        user={user}
                        onLogout={handleLogout}
                    />
                } />
                <Route path="/locations/new" element={<NewLocation user={user} onLogout={handleLogout}/>} />

                <Route path="/locations/:locationId" element={<LocationDetailsWrapper user={user} onLogout={handleLogout} />} />
                <Route
                    path="/locations/:locationId/add-room"
                    element={<AddRoomWrapper user={user} onLogout={handleLogout} />}
                />
                <Route
                    path="/locations/:locationId/:roomId"
                    element={<RoomWrapper user={user} onLogout={handleLogout} />}
                />
                <Route
                    path="/locations/:locationId/edit"
                    element={<EditLocationWrapper user={user} onLogout={handleLogout} />}
                />
                <Route
                    path="/locations/:locationId/:roomId/edit"
                    element={<EditRoomWrapper user={user} onLogout={handleLogout} allLocations={ALL_LOCATIONS} />}
                />

            </Routes>
        </BrowserRouter>
    );
}

export default App