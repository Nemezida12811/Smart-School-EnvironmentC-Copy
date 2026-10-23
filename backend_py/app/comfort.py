import json
import logging
import math

from .config import settings
from .errors import iso
from .repositories import SensorReadings

log = logging.getLogger("comfort")

# (поле, ідеальний діапазон, поріг штрафу)
_METRICS = [
    ("temperature", (20, 24), 5),
    ("humidity", (30, 60), 30),
    ("gas", (400, 1000), 1000),
    ("light", (300, 1000), 500),
    ("sound", (0, 50), 40),
]

# Structured Outputs: модель гарантовано повертає JSON саме такої форми.
# Корінь мусить бути об'єктом, тому масив порад лежить у полі "recommendations".
_TIPS_SCHEMA = {
    "name": "comfort_recommendations",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                        "type": {"type": "string", "enum": [m[0] for m in _METRICS]},
                        "message": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["priority", "type", "message", "reason"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["recommendations"],
        "additionalProperties": False,
    },
}

_ai_client = None


def _get_ai():
    """Створюється ліниво, щоб відсутній OPENAI_API_KEY не ламав запуск сервера."""
    global _ai_client
    if _ai_client is None:
        from openai import AsyncOpenAI
        _ai_client = AsyncOpenAI(api_key=settings.openai_api_key or None, timeout=30, max_retries=1)
    return _ai_client


def calculate_manual_comfort(latest: dict) -> int:
    total = 0.0
    for field, (lo, hi), threshold in _METRICS:
        val = latest[field]
        score = 1.0
        if val < lo:
            score = 1 - (lo - val) / threshold
        elif val > hi:
            score = 1 - (val - hi) / threshold
        total += max(0.0, min(1.0, score))
    return math.floor(total / len(_METRICS) * 100 + 0.5)  # як Math.round


async def calculate_comfort_by_audience(audience_id: str) -> dict | None:
    latest = await SensorReadings.find_latest(audience_id)
    if not latest:
        return None
    return {
        "audienceId": audience_id,
        "comfortPercentage": calculate_manual_comfort(latest),
        "timestamp": iso(latest["timestamp"]),
    }


async def generate_tips(audience_id: str) -> list | None:
    latest = await SensorReadings.find_latest(audience_id)
    if not latest:
        return None

    u = latest.get("units") or {}
    prompt = f"""You are an indoor comfort inspector. You have the following sensor data:
Temperature: {latest['temperature']} {u.get('temperature', '')}
Humidity: {latest['humidity']} {u.get('humidity', '')}
Gas (Air Quality): {latest['gas']} {u.get('gas', '')}
Light: {latest['light']} {u.get('light', '')}
Sound (Noise): {latest['sound']} {u.get('sound', '')}

Ideal ranges: Temperature (20-24), Humidity (30-60%), Gas (400-1000 ppm), Light (300-1000 lx), Sound (0-50 dB).

Based on this data, give 2-3 specific recommendations to improve comfort.
For each one provide: priority (high/medium/low), type (the sensor it concerns),
message (the recommendation text) and reason (why this is important)."""
    try:
        response = await _get_ai().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a concise indoor comfort assistant."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_schema", "json_schema": _TIPS_SCHEMA},
        )
        return json.loads(response.choices[0].message.content)["recommendations"]
    except Exception:
        log.exception("❌ [AI] Error generating tips")
        return []
