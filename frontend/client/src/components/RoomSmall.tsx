import './Room.css';

type ComfortCardProps = {
    roomName: string;
    comfortIndex?: number;
};

function interpolateColor(
    color1: number[],
    color2: number[],
    factor: number
) {
    return color1.map((c, i) =>
        Math.round(c + factor * (color2[i] - c))
    );
}

function comfortToRGB(percent: number): string {
    const clamped = Math.max(0, Math.min(100, percent));

    let result;

    if (clamped <= 50) {
        // red → yellow
        result = interpolateColor(
            [255, 0, 0],
            [255, 255, 0],
            clamped / 50
        );
    } else {
        // yellow → green
        result = interpolateColor(
            [255, 255, 0],
            [0, 255, 0],
            (clamped - 50) / 50
        );
    }

    return `rgb(${result[0]}, ${result[1]}, ${result[2]})`;
}

export function getComfortGradient(index?: number | string): string {
    // Return gray gradient if index is undefined, null, or the string "-"
    if (index === undefined || index === null || index === "-") {
        return `
        linear-gradient(
            311deg,
            rgba(200, 200, 200, 0.5) 15.17%,
            rgba(200, 200, 200, 0.08) 55.32%,
            rgba(153, 153, 153, 0) 77.96%
        )
        `;
    }

    // Ensure we have a number for the color calculation
    const numericIndex = typeof index === 'string' ? parseFloat(index) : index;
    const baseColor = comfortToRGB(numericIndex);

    return `
    linear-gradient(
      311deg,
      ${baseColor.replace("rgb", "rgba").replace(")", ", 0.5)")} 15.17%,
      ${baseColor.replace("rgb", "rgba").replace(")", ", 0.08)")} 55.32%,
      rgba(153, 153, 153, 0) 77.96%
    )
  `;
}

function RoomSmall({ roomName, comfortIndex }: ComfortCardProps) {
    return (
        <div
            className="comfort-card-small"
            style={{ background: getComfortGradient(comfortIndex) }}
        >
            <div className="comfort-card-small__content">
                <div>
                    <h3 className="comfort-card-small__title">{roomName}</h3>
                </div>

                <div className="comfort-card-small__value">
                    {comfortIndex !== undefined ? `${comfortIndex}%` : '-%'}
                </div>
            </div>
        </div>
    );
}

export default RoomSmall;
