import "./forms.css";
import BigButton from "./BigButton";
import { useEffect, useState } from "react";
import type { Location } from "./types";

type FormEditLocationProps = {
    location: Location;
    onSave: (updatedLocation: Partial<Location>) => void;
};

function FormEditLocation({ location, onSave }: FormEditLocationProps) {
    const [locationName, setLocationName] = useState("");

    useEffect(() => {
        if (location) {
            setLocationName(location.name);
        }
    }, [location]);

    const handleSubmit = () => {

        const updatedLocation: Partial<Location> = {
            name: locationName,
        };

        console.log("Updated location:", updatedLocation);
        onSave?.(updatedLocation);
    };

    return (
        <div className="page">
            <div className="login-card">
                <h2 className="title">Rename location</h2>

                <input
                    type="text"
                    placeholder="Location Name"
                    className="input"
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                />

                <BigButton text="Save changes" onClick={handleSubmit} />
            </div>
        </div>
    );
}

export default FormEditLocation;