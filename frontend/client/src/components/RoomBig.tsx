import './Room.css';
import {getComfortGradient} from "./RoomSmall.tsx";
import eyeClosed from "../assets/eye-closed.svg";
import eyeOpened from "../assets/eye-opened.svg";


import {useEffect, useState} from 'react';
import { locationApi } from "../newRestApiService.tsx";

function RoomBig({ comfortIndex, isHidden: initialHidden, isOwner, locationId, roomId }: any) {
    const [isHidden, setIsHidden] = useState(initialHidden);
    const [isLoading, setIsLoading] = useState(false);
    useEffect(() => {
        setIsHidden(initialHidden);
    }, [initialHidden]);

    const handleToggleVisibility = async (e: React.MouseEvent) => {
        e.stopPropagation(); // Prevent any parent click events

        const token = localStorage.getItem('token');
        if (!token || isLoading) return;

        setIsLoading(true);
        try {
            if (isHidden) {
                await locationApi.showDevice(locationId, roomId, token);
                setIsHidden(false);
            } else {
                await locationApi.hideDevice(locationId, roomId, token);
                setIsHidden(true);
            }
        } catch (error: any) {
            alert(error.message || "Failed to update visibility");
        } finally {
            setIsLoading(false);
        }
    };

    const visibilityTitle = isHidden
        ? "This room is hidden from other users"
        : "Users who joined the location can see this room";

    return (
        <div
            className="comfort-card-big"
            style={{
                background: getComfortGradient(comfortIndex),
                opacity: isLoading ? 0.7 : 1 // Visual feedback during save
            }}
        >
            <div className="comfort-card-big__content">
                <div>
                    <div className="comfort-card-header">
                        <h3 className="comfort-card-big__title">Comfort Index:</h3>
                        {isOwner && (
                            <div
                                className="comfort-card__visibility"
                                title={visibilityTitle}
                                onClick={handleToggleVisibility}
                                style={{ cursor: isLoading ? "wait" : "pointer" }}
                            >
                                <img
                                    src={isHidden ? eyeClosed : eyeOpened}
                                    alt="visibility status"
                                    style={{ transform: isLoading ? "scale(0.9)" : "scale(1)" }}
                                />
                            </div>
                        )}
                    </div>
                    <p className="comfort-card-big__subtitle">
                        Calculated from temperature, humidity,<br/>
                        CO₂ level, noise and lighting
                    </p>
                </div>

                <div className="comfort-card-big__value">
                    {comfortIndex}{comfortIndex !== "-" ? "%" : ""}
                </div>
            </div>
        </div>
    );
}

export default RoomBig;