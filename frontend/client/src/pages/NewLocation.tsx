import "./Log.css";
import Footer from "../components/Footer";
import BackButton from "../components/BackButton";
import HeaderLogged from "../components/HeaderLogged";
import HeaderUnlogged from "../components/HeaderUnlogged";
import FormLocationLogged from "../components/FormLocationLogged";
import FormLocationUnlogged from "../components/FormLocationUnlogged";
import type {User} from "../components/types.tsx";
import {useNavigate} from "react-router-dom";
import {locationApi} from "../newRestApiService.tsx";

type NewLocationProps = {
    user?: User | null;
    onLogout: () => void
};

function NewLocation({user, onLogout}: NewLocationProps) {
    const navigate = useNavigate();

    const handleCreate = async (name: string) => {
        const token = localStorage.getItem('token');
        if (!name.trim() || !user || !token) return;

        try {
            const newLoc = await locationApi.create({ name }, token);

            console.log("Created:", newLoc);
            navigate(`/locations/${newLoc.id}`);
        } catch (error: any) {
            alert(error.message || "Failed to create location");
        }
    };

    const handleJoin = async (id: string) => {
        const token = localStorage.getItem('token');
        if (!id.trim()) return;

        if (user && token) {
            try {
                await locationApi.addUser(id, user.id, token);
                navigate(`/locations/${id}`);
            } catch (error: any) {
                alert("Could not join: " + error.message);
            }
        } else {
            navigate(`/locations/${id}`);
        }
    };

    return (
        <div className="content">

            {user ?
                <HeaderLogged
                    username={user.username}
                    onLogout={onLogout}
                    onLogoClick={() => navigate('/locations')}/> :

                <HeaderUnlogged
                    onLoginClick={() => navigate('/login')}
                    onLogoClick={() => navigate('/locations')}/>
            }


            <BackButton text="Back" onClick={() => navigate(-1)}/>
            {user ?
                <FormLocationLogged onCreateClick={handleCreate}
                                    onJoinClick={handleJoin}/> : <FormLocationUnlogged onLoginClick={() => navigate('/login')} onJoinClick={handleJoin}/>
            }


            <Footer/>
        </div>
    );
}

export default NewLocation;