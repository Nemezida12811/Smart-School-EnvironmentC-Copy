import "./forms.css";
import BigButton from "./BigButton";
import Select from "react-select";
import { useState } from "react";


function FormEditRoom({ room, onSave }: any) {
    const [roomName, setRoomName] = useState(room.name || "");
    const [units, setUnits] = useState("");
    const [ntpHost, setNtpHost] = useState("");
    const [broker, setBroker] = useState("");
    const [ssid, setSsid] = useState("");
    const [password, setPassword] = useState("");
    const [interval, setInterval] = useState<number | "">("");

    const unitOptions = [
        { value: "standard", label: "Standard" },
        { value: "metric", label: "Metric" },
        { value: "imperial", label: "Imperial" }
    ];

    const handleSubmit = () => {
        const data: any = {};
        if (roomName) data.name = roomName;
        if (units) data.units = units;
        if (ntpHost) data.ntpHost = ntpHost;
        if (broker) data.brokerAddress = broker;
        if (ssid) data.wifiSsid = ssid;
        if (password) data.wifiPassword = password;
        if (interval) data.interval = Number(interval);

        onSave(data);
    };

    return (
        <div className="page">
            <div className="login-card edit-card">
                <h2 className="title-sensor">Sensor Configuration</h2>
                <h3 className="subtitle">Configuring: {room.id}</h3>

                <div className="input-group">
                    <label>Display Name</label>
                    <input type="text" className="input" value={roomName} onChange={(e) => setRoomName(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>Measurement Units</label>
                    <Select
                        options={unitOptions}
                        placeholder="Select units..."
                        onChange={(opt) => setUnits(opt?.value || "")}
                        className="my-select"
                        classNamePrefix="my-select"
                    />
                </div>

                <div className="input-group">
                    <label>NTP Host (Time Sync)</label>
                    <input type="text" className="input" placeholder="e.g. pool.ntp.org" value={ntpHost} onChange={(e) => setNtpHost(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>MQTT Broker Address</label>
                    <input type="text" className="input" placeholder="e.g. mqtt.example.com" value={broker} onChange={(e) => setBroker(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>WiFi SSID</label>
                    <input type="text" className="input" placeholder="Network Name" value={ssid} onChange={(e) => setSsid(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>WiFi Password</label>
                    <input type="password" className="input" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>Update Interval (ms)</label>
                    <input type="number" className="input" placeholder="e.g. 10000" value={interval} onChange={(e) => setInterval(e.target.value === "" ? "" : Number(e.target.value))} />
                </div>

                <BigButton text="Save Configuration" onClick={handleSubmit} />
            </div>
        </div>
    );
}

export default FormEditRoom;