import './forms.css';
import BigButton from "./BigButton.tsx";
import {useState} from "react";

type FormLocationLoggedProps = {
    onJoinClick?: (id: string) => void;
    onCreateClick?: (name: string) => void;
};

function FormLocationLogged({onJoinClick, onCreateClick}: FormLocationLoggedProps) {
    const [accessId, setAccessId] = useState("");
    const [locationName, setLocationName] = useState("");

    return (
        <div className="page">
            <div className="login-card" style = {{width: 430}}>
                <h2 className="title">Join location</h2>
                <h3 className="subtitle">Enter the access ID to join an existing location</h3>

                <input
                    type="text"
                    placeholder="Access ID"
                    className="input"
                    value={accessId}
                    onChange={(e) => setAccessId(e.target.value)}
                />

                <BigButton text="Join" onClick={() => onJoinClick?.(accessId)}/>
            </div>
            <h2 className="title" style={{ fontSize: 26 }}> or </h2>

            <div className="login-card" style = {{width: 430}}>
                <h2 className="title">Create new location</h2>
                <h3 className="subtitle">For adding your own devices and rooms</h3>


                <input
                    type="text"
                    placeholder="Location Name"
                    className="input"
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                />

                <BigButton text="Create" onClick={() => onCreateClick?.(locationName)}/>
            </div>
        </div>

    );
}

export default FormLocationLogged;