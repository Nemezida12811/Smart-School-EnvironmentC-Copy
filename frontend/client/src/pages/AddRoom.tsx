import "./Log.css";
import Footer from "../components/Footer";
import BackButton from "../components/BackButton";
import HeaderLogged from "../components/HeaderLogged.tsx";
import FormAddRoom from "../components/FormAddRoom.tsx";
import {useNavigate} from "react-router-dom";
import {locationApi} from "../newRestApiService.tsx";

function AddRoom({ currentLocationId, availableLocations, user, onLogout }: any) {
    const navigate = useNavigate();

    const handleCreate = async (formData: any) => {
        const token = localStorage.getItem('token');
        if (!token) return;

        try {
            // Use the locationId chosen from the dropdown
            await locationApi.addDevice(
                formData.locationId,
                formData.deviceId,
                formData.name,
                token
            );

            if (formData.hideRoom) {
                await locationApi.hideDevice(formData.locationId, formData.deviceId, token);
            }

            alert("Room added successfully!");
            navigate(`/locations/${formData.locationId}`);
        } catch (error: any) {
            alert(error.message || "Failed to add room.");
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
            <FormAddRoom
                locations={availableLocations}
                defaultLocationId={currentLocationId}
                onSave={handleCreate}
            />
            <Footer />
        </div>
    );
}

export default AddRoom;
