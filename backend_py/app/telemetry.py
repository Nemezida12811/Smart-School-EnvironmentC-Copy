"""MQTT telemetry processing (analog of mqtt.service.js + mqtt.topics.js)."""
import json
import logging
import math
import re
import time
from datetime import datetime, timezone

from .repositories import SensorReadings

log = logging.getLogger("mqtt")

TOPIC_TELEMETRY = "iot/device/+/telemetry"
TOPIC_BACKEND_STATUS = "iot/backend/status"

_DEVICE_RE = re.compile(r"^iot/device/([^/]+)/telemetry$")
_RAW_MAX = 65535
_FIELDS = ("temperature", "humidity", "gas", "light", "sound")


def get_device_id(topic: str) -> str | None:
    m = _DEVICE_RE.match(topic)
    return m.group(1) if m else None


def _number(sensor: dict, key: str = "value") -> float:
    """Like Number(x) in JS for missing/null/non-numeric value."""
    if key not in sensor:
        return math.nan
    v = sensor[key]
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return math.nan


def parse_timestamp(ts) -> float:
    """Returns epoch milliseconds. Accepts:
      - number/string-number: epoch in seconds (as in MQTT.md); values > 1e11 are considered milliseconds;
      - ISO-8601 string 'YYYY-MM-DDTHH:MM:SSZ' — exactly what real firmware sends (to_iso8601).
    If time is missing or unparseable — server time is used (measurement is not lost)."""
    now_ms = time.time() * 1000
    if ts is None or ts == "" or isinstance(ts, bool):
        return now_ms
    try:
        value = float(ts)
        return value if value > 1e11 else value * 1000
    except (TypeError, ValueError):
        pass
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp() * 1000
        except ValueError:
            pass
    log.warning("⚠️ Unparseable timestamp %r — using server time", ts)
    return now_ms


def parse_telemetry(payload) -> dict:
    sensors = payload.get("sensors") if isinstance(payload, dict) else None
    sensors = sensors if isinstance(sensors, dict) else {}

    def sensor(name: str) -> dict:
        s = sensors.get(name)
        return s if isinstance(s, dict) else {}

    ts = payload.get("timestamp") if isinstance(payload, dict) else None

    return {
        **{f: _number(sensor(f)) for f in _FIELDS},
        "units": {f: sensor(f).get("units") for f in _FIELDS},
        "timestamp_ms": parse_timestamp(ts),
    }


def is_valid(t: dict) -> bool:
    return all(not math.isnan(t[f]) for f in _FIELDS) \
        and all(t["units"][f] for f in _FIELDS)


def convert_units(t: dict) -> dict:
    """Raw 16-bit ADC values -> physical values (ranges as in Node version)."""
    def map_value(val: float, lo: float, hi: float) -> float:
        return lo + (val / _RAW_MAX) * (hi - lo)

    t["gas"] = math.floor(map_value(t["gas"], 200, 10000) + 0.5)      # 200–10000
    t["sound"] = math.floor(map_value(t["sound"], 40, 120) + 0.5)     # 40–120 dB
    t["light"] = round(map_value(t["light"], 0.1, 100000), 1)         # 0.1–100000 lux
    return t


async def handle_message(topic: str, raw: bytes) -> None:
    try:
        payload = json.loads(raw.decode())
    except Exception as exc:
        log.error("❌ Invalid MQTT message: %s", exc)
        return

    device_id = get_device_id(topic)
    if not device_id:
        log.info("📩 MQTT message (unknown source) %s %s", topic, payload)
        return

    telemetry = parse_telemetry(payload)
    log.info("📩 Device %s telemetry %s", device_id, telemetry)

    if not is_valid(telemetry):
        log.warning("⚠️ Invalid telemetry data from %s %s", device_id, telemetry)
        return

    telemetry = convert_units(telemetry)
    telemetry["timestamp"] = datetime.fromtimestamp(telemetry["timestamp_ms"] / 1000, tz=timezone.utc)
    try:
        await SensorReadings.save(device_id, telemetry)
        log.info("✅ Saved telemetry for %s", device_id)
    except Exception:
        log.exception("❌ Failed to save telemetry for %s", device_id)
