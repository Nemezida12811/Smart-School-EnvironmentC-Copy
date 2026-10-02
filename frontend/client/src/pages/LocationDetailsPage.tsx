import {useState, useMemo} from "react";
import HeaderLogged from "../components/HeaderLogged";
import HeaderUnlogged from "../components/HeaderUnlogged";
import Footer from "../components/Footer";
import BackButton from "../components/BackButton";
import RoomMid from "../components/RoomMid";
import type {User, Location} from "../components/types.tsx";
import "../components/locationSection.css";
import searchIcon from "../assets/search.svg";
import Select, {components} from "react-select";
import arrowIcon from "../assets/arrow.svg";
import SmallButton from "../components/SmallButton.tsx";
import {Link, useNavigate} from "react-router-dom";
import {locationApi} from "../newRestApiService.tsx";


type LocationDetailsPageProps = {
    user?: User | null;
    location: Location;
    onLogout: () => void
    isRoomsLoading: boolean;
};

const sortOptions = [
    {value: "name-asc", label: "Name (A-Z)"},
    {value: "name-desc", label: "Name (Z-A)"},
    {value: "index-desc", label: "Comfort Index (High-Low)"},
];

const DropdownIndicator = (props: any) => {
    const {menuIsOpen} = props.selectProps;
    return (
        <components.DropdownIndicator {...props}>
            <img
                src={arrowIcon}
                alt="arrow"
                className="w-4 h-4 transition-transform duration-200"
                style={{transform: menuIsOpen ? "rotate(180deg)" : "rotate(0deg)"}}
            />
        </components.DropdownIndicator>
    );
};

function LocationDetailsPage({user, location, onLogout, isRoomsLoading}: LocationDetailsPageProps) {
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState("");
    const [sortBy, setSortBy] = useState(sortOptions[0]);

    const isOwner = user && user.id === location.adminId;

    const processedRooms = useMemo(() => {
        if (!location.rooms || location.rooms.length === 0) return [];

        let roomsToShow = location.rooms;
        if (!isOwner) {
            roomsToShow = roomsToShow.filter(room => !room.hideRoom);
        }

        const filtered = roomsToShow.filter((room) =>
            room.name.toLowerCase().includes(searchTerm.toLowerCase())
        );

        return [...filtered].sort((a, b) => {
            if (sortBy.value === "name-asc") return a.name.localeCompare(b.name);
            if (sortBy.value === "name-desc") return b.name.localeCompare(a.name);
            if (sortBy.value === "index-desc") {
                return (b.metrics?.comfortIndex || 0) - (a.metrics?.comfortIndex || 0);
            }
            return 0;
        });
    }, [location.rooms, searchTerm, sortBy, isOwner]);

    const handleDelete = async () => {
        const confirmed = window.confirm(
            `Are you sure you want to delete "${location.name}"? This will remove all associated rooms and data.`
        );

        if (confirmed && user) {
            const token = localStorage.getItem('token');

            if (!token) {
                alert("You must be logged in to perform this action.");
                return;
            }

            try {
                await locationApi.delete(location.id, token);

                alert("Location deleted successfully.");
                navigate('/locations');
            } catch (error: any) {
                alert(error.message || "Failed to delete location.");
            }
        }
    };

    return (
        <div className="locations-page">
            {user ?
                <HeaderLogged
                    username={user.username}
                    onLogout={onLogout}
                    onLogoClick={() => navigate('/locations')}/> :

                <HeaderUnlogged
                    onLoginClick={() => navigate('/login')}
                    onLogoClick={() => navigate('/locations')}/>
            }

            <main className="locations-content">
                <BackButton text="All locations" transparent onClick={() => navigate('/locations')}/>
                {!isOwner && (
                    <div className="page-details-header">
                        <h1 className="page-header-title">{location.name}</h1>
                        <p className="subtitles">
                            Comfort Index (%) – overall quality of learning conditions in the room
                        </p>
                    </div>
                )
                }
                {isOwner && (
                    <div className="page-header">
                        <div>
                            <h1 className="page-header-title">{location.name}</h1>
                            <h2 className="access-id">Access ID: {location.id}</h2>
                            <p className="subtitles">
                                Anyone with access ID can view and track this location
                            </p>
                        </div>
                        <div className="page-header-actions">
                            <SmallButton text="Add room" image="plus"
                                         onClick={() => navigate(`/locations/${location.id}/add-room`)}/>
                            <SmallButton text="Rename location" image="pencil"
                                         onClick={() => navigate(`/locations/${location.id}/edit`)}/>
                            <SmallButton text="Delete location" image="cross" onClick={handleDelete}/>
                        </div>
                    </div>
                )
                }

                <div className="controls-row">
                    <div className="search-container">
                        <input
                            type="text"
                            placeholder="Search for a room"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="room-search-input"
                        />
                        <img src={searchIcon} className="search-icon" alt="search"/>
                    </div>

                    <div className="sort-container">
                        <label className="sort-label">Sort by:</label>
                        <Select
                            options={sortOptions}
                            value={sortBy}
                            onChange={(option) => option && setSortBy(option)}
                            components={{DropdownIndicator, IndicatorSeparator: () => null}}
                            className="my-select sort-select-width"
                            classNamePrefix="my-select"
                            isSearchable={false}
                        />
                    </div>
                </div>

                <div className="rooms-grid">
                    {isRoomsLoading && processedRooms.length === 0 ? (
                        <div className="grid-loader">
                            <p>Loading rooms...</p>
                        </div>
                    ) : processedRooms.length > 0 ? (
                        processedRooms.map((room) => (
                            <Link key={room.id} to={`/locations/${location.id}/${room.id}`} className="room-card-link">
                                <RoomMid
                                    roomName={room.name}
                                    comfortIndex={room.metrics?.comfortIndex}
                                    isHidden={room.hideRoom}
                                    isOwner={isOwner}
                                />
                            </Link>
                        ))
                    ) : (
                        <p className="empty-text">No rooms here yet.</p>
                    )}
                </div>
            </main>

            <Footer/>
        </div>
    );
}

export default LocationDetailsPage;