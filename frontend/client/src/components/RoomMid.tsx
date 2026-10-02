import './Room.css';
import {getComfortGradient} from "./RoomSmall.tsx";
import eyeClosed from "../assets/eye-closed.svg";
import eyeOpened from "../assets/eye-opened.svg";

type ComfortCardProps = {
    roomName: string;
    comfortIndex?: number;
    isHidden: boolean;
    isOwner?: boolean | null | undefined
};

function RoomMid({roomName, comfortIndex, isHidden, isOwner}: ComfortCardProps) {
    const visibilityTitle = isHidden
        ? "This room is hidden from other users"
        : "Users who joined the location can see this room";

    return (
        <div
            className="comfort-card-mid"
            style={{background: getComfortGradient(comfortIndex)}}
        >
            <div className="comfort-card-mid__content">
                <div className="comfort-card-header">
                    <h3 className="comfort-card-mid__title">{roomName}</h3>
                    {isOwner && (
                        <div className="comfort-card__visibility" title={visibilityTitle}>
                            <img
                                src={isHidden ? eyeClosed : eyeOpened}
                                alt="visibility status"
                            />
                        </div>)}
                </div>

                <div className="comfort-card-mid__value">
                    {comfortIndex !== undefined ? `${comfortIndex}%` : '-%'}
                </div>
            </div>
        </div>
    );
}

export default RoomMid;
