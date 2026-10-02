import type {Location} from "./types.tsx";
import RoomSmall from "./RoomSmall.tsx";
import "./locationSection.css";
import forwardArrow from "../assets/forward_arrow.svg";
import plusButton from "../assets/plus_button.svg";
import {Link} from "react-router-dom";

type LocationSectionProps = {
    title: string;
    locations?: Location[];
};

function LocationSection({title, locations}: LocationSectionProps) {
    //const navigate = useNavigate();

    if (!locations || locations.length === 0) {
        return (<section className="location-section">
            <h2 className="section-title">{title}</h2>
            <p className="empty-text">No locations yet.</p>
        </section>);
    }

    return (
        <section className="location-section">
            <h2 className="section-title">{title}</h2>

            {locations.map((location) => {
                const allRooms = location.rooms || [];

                const filteredRooms = title === "Joined locations"
                    ? allRooms.filter(room => !room.hideRoom)
                    : allRooms;

                if (filteredRooms.length > 0) {
                    const visibleRooms = filteredRooms.slice(0, 5);
                    const hasMore = filteredRooms.length > 5;

                    return (
                        <div key={location.id} className="location-block">
                            <div className="location-header">
                                <Link to={`/locations/${location.id}`} className="location-link">
                                    <h3>{location.name}</h3>
                                </Link>
                                {title === "Created locations" && (
                                    <Link to={`/locations/${location.id}/add-room`} className="icon-button" >
                                        <img src={plusButton} alt="plus"/>
                                    </Link>
                                )}
                            </div>

                            <div className="rooms">
                                <div className="rooms-row">
                                    {visibleRooms.map((room) => (
                                        <Link
                                            key={room.id}
                                            to={`/locations/${location.id}/${room.id}`} // Updated path
                                            className="room-card-link"
                                        >
                                            <RoomSmall
                                                roomName={room.name}
                                                comfortIndex={room.metrics?.comfortIndex}
                                            />
                                        </Link>
                                    ))}
                                </div>

                                {hasMore && (
                                    <Link to={`/locations/${location.id}`} className="all-rooms-btn">
                                        All rooms
                                        <img src={forwardArrow} alt="arrow"/>
                                    </Link>
                                )}
                            </div>

                        </div>
                    );
                } else {
                    return (
                        <div key={location.id} className="location-block">
                            <div className="location-header">
                                <Link to={`/locations/${location.id}`} className="location-link">
                                    <h3>{location.name}</h3>
                                </Link>
                                {title === "Created locations" && (
                                    <Link to={`/locations/${location.id}/add-room`} className="icon-button" >
                                        <img src={plusButton} alt="plus"/>
                                    </Link>
                                )}
                            </div>
                            <p className="empty-text">No rooms yet.</p>
                        </div>
                    )
                }
            })}
        </section>
    );
}

export default LocationSection;