import "./RoomPage.css"

type ParameterCardProps = {
    label: string,
    value: string | number,
    unit: string
};

function ParameterCard({label, value, unit}: ParameterCardProps) {
    return (
        <div className="parameter-card">
            <span className="parameter-label">{label}:</span>
            <span className="parameter-value">
                {value}{value !== "-" ? unit : ""}
            </span>
        </div>
    );
}

export default ParameterCard;