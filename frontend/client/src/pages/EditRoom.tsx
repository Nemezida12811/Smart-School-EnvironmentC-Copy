import "./Log.css";
import Footer from "../components/Footer";
import BackButton from "../components/BackButton";
import HeaderLogged from "../components/HeaderLogged.tsx";
import FormEditRoom from "../components/FormEditRoom.tsx";
import {useNavigate} from "react-router-dom";
import {locationApi} from "../newRestApiService.tsx";


function EditRoom({ room, user, onLogout }: any) {
    const navigate = useNavigate();

    const handleSave = async (configData: any) => {
        const token = localStorage.getItem('token') || "";

        try {
            await locationApi.updateDeviceSettings(
                room.location.id,
                room.id,
                configData,
                token
            );

            alert("Configuration sent to sensor successfully!");
            navigate(`/locations/${room.location.id}/${room.id}`);
        } catch (error: any) {
            console.error("Save error:", error);
            alert(error.message || "Failed to reach sensor.");
        }
    };

    return (
        <div className="content">
            <HeaderLogged username={user.username} onLogout={onLogout} onLogoClick={() => navigate('/locations')} />
            <BackButton text="Back" transparent onClick={() => navigate(-1)} />
            <FormEditRoom room={room} onSave={handleSave} />
            <Footer/>
        </div>
    );
}

export default EditRoom;
