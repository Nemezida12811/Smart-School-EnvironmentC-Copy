import './forms.css';
import BigButton from "./BigButton.tsx";
import arrowIcon from "../assets/arrow.svg";
import Select from "react-select";
import { components } from "react-select";
import {useMemo, useState} from "react";

export const DropdownIndicator = (props:any) => {
    const { menuIsOpen } = props.selectProps;

    return (
        <components.DropdownIndicator {...props}>
            <img src={arrowIcon} alt="arrow" className="w-4 h-4 transition-transform duration-200"
                 style={{ transform: menuIsOpen ? "rotate(180deg)" : "rotate(0deg)" }}/>

        </components.DropdownIndicator>
    );
};

function FormAddRoom({ onSave, locations, defaultLocationId }: any) {
    const [name, setName] = useState("");
    const [deviceId, setDeviceId] = useState("");
    const [hideRoom, setHideRoom] = useState(false);
    const [selectedLocationId, setSelectedLocationId] = useState(defaultLocationId || "");

    const locationOptions = useMemo(() =>
        locations.map((loc: any) => ({
            value: loc.id,
            label: loc.name
        })), [locations]
    );

    const currentOption = locationOptions.find((opt: any) => opt.value === selectedLocationId);

    const handleSubmit = () => {
        if (!name || !deviceId || !selectedLocationId) {
            alert("Please fill in all fields.");
            return;
        }

        onSave({
            name,
            deviceId,
            hideRoom,
            locationId: selectedLocationId
        });
    };

    return (
        <div className="page">
            <div className="login-card">
                <h2 className="title">Add new room</h2>

                <input
                    type="text"
                    placeholder="Room Name"
                    className="input"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />

                <input
                    type="text"
                    placeholder="Device Access ID"
                    className="input"
                    value={deviceId}
                    onChange={(e) => setDeviceId(e.target.value)}
                />

                <Select
                    options={locationOptions}
                    value={currentOption}
                    placeholder="Select location"
                    className="my-select"
                    classNamePrefix="my-select"
                    onChange={(option) => setSelectedLocationId(option?.value || "")}
                />

                <label className="checkbox-container">
                    <span className="checkbox-text">Hide room from other viewers</span>
                    <input
                        type="checkbox"
                        checked={hideRoom}
                        onChange={(e) => setHideRoom(e.target.checked)}
                    />
                </label>

                <BigButton text="Create" onClick={handleSubmit} />
            </div>
        </div>
    );
}

export default FormAddRoom;