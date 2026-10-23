import json
import logging
import math
import re

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

_ai_client = None


def _get_ai():
    global _ai_client
    if _ai_client is None:
        from google import genai
        _ai_client = genai.Client(api_key=settings.google_api_key)
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
    prompt = f"""Hi. You are an indoor comfort inspector. You have the following sensor data:
Temperature: {latest['temperature']} {u.get('temperature', '')}
Humidity: {latest['humidity']} {u.get('humidity', '')}
Gas (Air Quality): {latest['gas']} {u.get('gas', '')}
Light: {latest['light']} {u.get('light', '')}
Sound (Noise): {latest['sound']} {u.get('sound', '')}

Ideal ranges: Temperature (20-24), Humidity (30-60%), Gas (400-1000 ppm), Light (300-1000 lx), Sound (0-50 dB).

Based on this data, generate a list of 2-3 specific recommendations to improve comfort.
Return ONLY a JSON array of objects with the following format:
[{{"priority": "high"|"medium"|"low", "type": "temperature"|"humidity"|"gas"|"light"|"sound", "message": "recommendation text", "reason": "why this is important"}}]
"""
    try:
        response = await _get_ai().aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        clean = re.sub(r"```json|```", "", response.text).strip()
        return json.loads(clean)
    except Exception:
        log.exception("❌ [AI] Error generating tips")
        return []
