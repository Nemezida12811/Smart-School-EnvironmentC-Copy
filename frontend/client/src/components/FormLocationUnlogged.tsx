import './forms.css';
import BigButton from "./BigButton.tsx";
import {useState} from "react";

type FormLocationUnloggedProps = {
    onJoinClick?: (id: string) => void;
    onLoginClick?: () => void;
};

function FormLocationUnlogged({onJoinClick, onLoginClick}: FormLocationUnloggedProps) {
    const [accessId, setAccessId] = useState("");
    return (
        <div className="page">
            <div className="login-card">
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

            <div className="login-card">
                <h2 className="title">Create new location</h2>
                <h3 className="subtitle">For adding your own devices and rooms</h3>
                <BigButton text="Log in" onClick={onLoginClick}/>
                <h3 className="subtitle" style={{ marginTop: '15px', marginBottom: '0' }}>to create your own locations</h3>
            </div>
        </div>

    );
}

export default FormLocationUnlogged;