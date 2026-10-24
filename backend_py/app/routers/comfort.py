import re
from datetime import datetime, timezone

from fastapi import APIRouter

from .. import comfort
from ..errors import ApiError, failing_as, iso, ok
from ..repositories import SensorReadings

router = APIRouter(prefix="/api/comfort")


def _parse_int(value: str) -> int | None:
    """Like parseInt in JS: '12abc' -> 12, 'abc' -> None (would be null in JSON)."""
    m = re.match(r"\s*([+-]?\d+)", value)
    return int(m.group(1)) if m else None


@router.get("/{audience_id}")
async def get_comfort_level(audience_id: str):
    with failing_as("Failed to get comfort level", with_details=True):
        result = await comfort.calculate_comfort_by_audience(audience_id)
        if not result:
            raise ApiError(404, "No sensor data found")
        return ok(result)


@router.get("/{audience_id}/recommendations")
async def get_recommendations(audience_id: str):
    with failing_as("Failed to get recommendations", with_details=True):
        tips = await comfort.generate_tips(audience_id)
        if tips is None:  # empty list [] is a valid response (as in Node)
            raise ApiError(404, "No recommendations found")
        return ok({
            "audienceId": _parse_int(audience_id),
            "recommendations": tips,
            "generatedAt": iso(datetime.now(timezone.utc)),
        })


@router.get("/{device_id}/sensors")
async def get_sensor_data(device_id: str):
    with failing_as("Failed to get sensor data", with_details=True):
        latest = await SensorReadings.find_latest(device_id)
        if not latest:
            raise ApiError(404, "No sensor data found for this device")
        return ok({
            "deviceId": device_id,
            "name": latest.get("name") or "",
            "hidden": latest.get("hidden", False),
            "latestReading": {
                "temperature": latest["temperature"],
                "humidity": latest["humidity"],
                "gas": latest["gas"],
                "light": latest["light"],
                "sound": latest["sound"],
                "units": latest.get("units"),
            },
            "timestamp": iso(latest["timestamp"]),
        })
