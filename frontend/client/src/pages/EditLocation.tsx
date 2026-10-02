import "./Log.css";
import Footer from "../components/Footer";
import BackButton from "../components/BackButton";
import HeaderLogged from "../components/HeaderLogged.tsx";
import type {Location, User} from "../components/types.tsx";
import {useNavigate} from "react-router-dom";
import FormEditLocation from "../components/FormEditLocation.tsx";
import {locationApi} from "../newRestApiService.tsx";

type EditLocationProps = {
    location: Location;
    user: User;
    onLogout: () => void
};

function EditLocation({ location, user, onLogout }: EditLocationProps ) {
    const navigate = useNavigate();

    const handleSave = async (updatedData: Partial<Location>) => {
        const token = localStorage.getItem('token');

        if (!updatedData.name || !token) {
            alert("Error: Missing data or not logged in.");
            return;
        }

        try {
            await locationApi.updateName(location.id, updatedData.name, token);

            alert("Name updated successfully!");
            navigate(`/locations/${location.id}`);
        } catch (error: any) {
            alert(error.message || "Failed to update location name.");
        }
    };

    return (
        <div className="content">
            <HeaderLogged
                username={user.username}
                onLogout={onLogout}
                onLogoClick={() => navigate('/locations')}
            />
            <BackButton text="Back" transparent onClick={() => navigate(-1)} />

            <FormEditLocation
                location={location}
                onSave={handleSave}
            />

            <Footer/>
        </div>
    );
}

export default EditLocation;
