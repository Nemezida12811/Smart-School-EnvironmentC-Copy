import HeaderLogged from "../components/HeaderLogged";
import HeaderUnlogged from "../components/HeaderUnlogged";
import Footer from "../components/Footer";
import BackButton from "../components/BackButton";
import SmallButton from "../components/SmallButton";
import RoomBig from "../components/RoomBig";
import ParameterCard from "../components/ParameterCard";
import type {User, Room} from "../components/types.tsx";
import "../components/RoomPage.css";
import infoIcon from "../assets/info.svg";
import {useNavigate} from "react-router-dom";
import {locationApi} from "../newRestApiService.tsx";

type RoomPageProps = {
    user?: User | null;
    room: Room;
    advice: string[] | null;
    onLogout: () => void
};

function RoomPage({user, room, advice, onLogout}: RoomPageProps) {
    const isAuthor = user && user.id === room.location.adminId ;

    const navigate = useNavigate();
    const metricsList = room.metrics;

    const isDataMissing = !metricsList || [
        metricsList.temperature,
        metricsList.humidity,
        metricsList.co2,
        metricsList.lighting,
        metricsList.noise
    ].some(val => val === undefined || val === null);


    const formatValue = (value: number | undefined): string | number => {
        return (value !== undefined && value !== null) ? value : "-";
    };


    const getDefaultAdvice = () => {
        if (isDataMissing) {
            return "Some sensor data is missing. Please check the device connection for a complete comfort analysis.";
        }
        return "The room environment is currently optimal. No improvements needed.";
    };

    const handleDelete = async () => {
        const confirmed = window.confirm(
            `Are you sure you want to delete "${room.name}"? This will remove all associated and data.`
        );

        if (confirmed && user) {
            const token = localStorage.getItem('token');
            try {
                await locationApi.removeDevice(room.location.id, room.id, token || "");

                alert("Room deleted successfully.");
                navigate(`/locations/${room.location.id}`);
            } catch (error: any) {
                alert(error.message || "Failed to delete room.");
            }
        }
    };

    return (
        <div className="room-page">
            {user ? <HeaderLogged username={user.username} onLogout={onLogout}
                                  onLogoClick={() => navigate('/locations')}/> :
                <HeaderUnlogged onLoginClick={() => navigate('/login')}
                                onLogoClick={() => navigate('/locations')}/>}

            <main className="room-content">
                <BackButton text={room.location.name} transparent
                            onClick={() => navigate(`/locations/${room.location.id}`)}/>

                <div className="room-header">
                    <h1 className="room-title">{room.name}</h1>
                    {isAuthor && (
                        <div className="actions">
                            <SmallButton text="Edit room" image="pencil"
                                         onClick={() => navigate(`/locations/${room.location.id}/${room.id}/edit`)}/>
                            <SmallButton text="Delete room" image="cross" onClick={handleDelete}/>
                        </div>
                    )}
                </div>

                <div className="comfort-section">
                    <RoomBig comfortIndex={room.metrics?.comfortIndex ?? "-"}
                             isHidden={room.hideRoom}
                             isOwner={isAuthor}
                             locationId={room.location.id}
                             roomId={room.id}/>

                    <div className="advice-container">
                        <div className="advice-header">
                            <img src={infoIcon} alt="info"/>
                            <h2>How to improve comfort:</h2>
                        </div>
                        <ul className="advice-list">
                            {advice === null ? (
                                <li className="loading-advice">Loading recommendations...</li>
                            ) : advice.length > 0 ? (
                                // When AI finished
                                advice.map((item, index) => (
                                    <li key={index}>{item}</li>
                                ))
                            ) : (
                                // If AI found nothing or errored
                                <li>{getDefaultAdvice()}</li>
                            )}
                        </ul>
                    </div>
                </div>

                <section className="parameters-section">
                    <h3 className="section-label">Other parameters:</h3>
                    <div className="parameters-grid">
                        <ParameterCard
                            label="Temperature"
                            value={formatValue(room.metrics?.temperature)}
                            unit="°C"
                        />
                        <ParameterCard
                            label="Humidity"
                            value={formatValue(room.metrics?.humidity)}
                            unit="%"
                        />
                        <ParameterCard
                            label="CO₂"
                            value={formatValue(room.metrics?.co2)}
                            unit=" ppm"
                        />
                        <ParameterCard
                            label="Lighting"
                            value={formatValue(room.metrics?.lighting)}
                            unit=" lx"
                        />
                        <ParameterCard
                            label="Noise"
                            value={formatValue(room.metrics?.noise)}
                            unit=" dB"
                        />
                    </div>
                </section>
            </main>

            <Footer/>
        </div>
    );
}

export default RoomPage;