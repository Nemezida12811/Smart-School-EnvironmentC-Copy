import asyncio
import json
import logging
import time
from urllib.parse import unquote, urlparse

import paho.mqtt.client as mqtt

from .config import settings
from .telemetry import TOPIC_BACKEND_STATUS, TOPIC_TELEMETRY

log = logging.getLogger("mqtt")

_SCHEMES = {  # scheme -> (transport, tls, default_port)
    "mqtt": ("tcp", False, 1883), "tcp": ("tcp", False, 1883),
    "mqtts": ("tcp", True, 8883), "ssl": ("tcp", True, 8883), "tls": ("tcp", True, 8883),
    "ws": ("websockets", False, 80), "wss": ("websockets", True, 443),
}


def _status(state: str) -> str:
    return json.dumps({"status": state, "ts": int(time.time() * 1000)})


class MqttClient:
    def __init__(self):
        self.client: mqtt.Client | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._handler = None

    def initialize(self, loop: asyncio.AbstractEventLoop, handler) -> None:
        """handler(topic, payload_bytes) — async-функція, виконується в event loop FastAPI."""
        if not settings.mqtt_url:
            log.warning("⚠️ MQTT_URL is not set — MQTT is disabled")
            return
        self._loop, self._handler = loop, handler

        url = urlparse(settings.mqtt_url)
        transport, tls, default_port = _SCHEMES.get(url.scheme, ("tcp", False, 1883))

        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=settings.mqtt_client_id,
            clean_session=True,
            transport=transport,
        )
        if tls:
            client.tls_set()
        if transport == "websockets":
            client.ws_set_options(path=url.path or "/mqtt")
        if url.username:
            client.username_pw_set(unquote(url.username), unquote(url.password or ""))

        client.will_set(TOPIC_BACKEND_STATUS, _status("offline"), qos=1, retain=True)
        client.reconnect_delay_set(min_delay=3, max_delay=3)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = lambda *a, **k: log.warning("⚠️ MQTT disconnected")

        self.client = client
        client.connect_async(url.hostname, url.port or default_port)
        client.loop_start()

    # Колбеки paho працюють у власному потоці
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("❌ MQTT error: %s", reason_code)
            return
        log.info("✅ MQTT connected")
        client.publish(TOPIC_BACKEND_STATUS, _status("online"), qos=1, retain=True)
        client.subscribe(TOPIC_TELEMETRY, qos=1)

    def _on_message(self, client, userdata, msg):
        if not self._handler or not self._loop:
            return
        fut = asyncio.run_coroutine_threadsafe(self._handler(msg.topic, msg.payload), self._loop)
        fut.add_done_callback(lambda f: f.exception() and log.error("❌ MQTT handler: %s", f.exception()))

    def publish(self, topic: str, payload, qos: int = 1, retain: bool = False) -> None:
        if not self.client:
            return
        message = json.dumps(payload) if isinstance(payload, (dict, list)) else payload
        self.client.publish(topic, message, qos=qos, retain=retain)

    def close(self) -> None:
        if not self.client:
            return
        info = self.client.publish(TOPIC_BACKEND_STATUS, _status("offline"), qos=1, retain=True)
        try:
            info.wait_for_publish(timeout=2)
        except Exception:
            pass
        self.client.loop_stop()
        self.client.disconnect()


mqtt_client = MqttClient()
