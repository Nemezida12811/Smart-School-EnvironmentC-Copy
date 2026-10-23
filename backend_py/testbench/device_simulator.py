#!/usr/bin/env python3
"""
Емулятор IoT-пристрою Inspector-comforT (Raspberry Pi Pico W) для перевірки backend і frontend.

Поводиться як справжня прошивка (device/app_a):
  • id пристрою у форматі  com-<16 hex>-fort
  • телеметрія -> iot/device/<id>/telemetry, статус (retained + last will) -> iot/device/<id>/status
  • payload як у states/publish_data.py: timestamp = ISO-8601 'YYYY-MM-DDTHH:MM:SSZ',
    gas/sound/light — СИРІ 16-бітні значення АЦП (0..65535), temperature/humidity — цілі числа (DHT11)
  • вимірювання буферизуються, якщо «Wi-Fi» недоступний, і відправляються пачкою
  • налаштування з iot/backend/<id>/settings (retained) перевіряються так само, як Settings.validate()
    у прошивці (типи, id, interval >= 1000, units, user, Wi-Fi, NTP) і застосовуються в кінці циклу

Фізична модель кімнати (CO2, температура, вологість, світло, шум) залежить від кількості людей,
вікон та пори доби, тому графіки/відсоток комфорту на фронтенді змінюються правдоподібно.
Фізичні величини переводяться в «сирі» значення АЦП оберненням формул backend (telemetry.convert_units).

Інтерактивні команди (stdin):  help | status | scenario <ім'я> [n] | offline [on|off] | bad | burst <N> | quit
"""
import argparse
import hashlib
import json
import math
import random
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

RAW_MAX = 65535
ALLOWED_UNITS = ("standard", "metric", "imperial")
DEFAULT_SETTINGS = {                       # ключі, які handle_settings_update вимагає в повідомленні
    "user": {"login": "", "password": ""},
    "units": "standard",
    "wifi": {"ssid": "", "password": ""},
    "ntp_host": "pool.ntp.org",
    "mqtt": {"server": "broker.hivemq.com"},
    "id": "",
    "measurement_interval": 10000,
}
HOST_RE = re.compile(r"^(?=.{1,253}$)([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$")


def device_id_for(index: int, prefix: str = "room") -> str:
    """Стабільний id (як ID у constants.py), щоб між запусками пристрої лишались тими самими."""
    return f"com-{hashlib.sha1(f'{prefix}-{index}'.encode()).hexdigest()[:16]}-fort"


# ═════════════════════════════ фізична модель кімнати ═════════════════════════════
def _school_occupancy(h: float) -> float:
    lessons = [(8.0, 8.75), (8.92, 9.67), (9.83, 10.58), (10.92, 11.67), (11.83, 12.58), (12.75, 13.5)]
    if any(a <= h < b for a, b in lessons):
        return 24
    return 3 if 8.0 <= h < 13.6 else 0       # перерви: майже всі виходять


SCENARIOS = {
    # occ(h) — людей у кімнаті; t_out — температура ззовні; k_vent — природна вентиляція (1/с);
    # auto_window — «вчитель» відчиняє вікна; heating — працює опалення; noise — додатковий шум, дБ
    "school-day":  dict(occ=_school_occupancy, t_out=9,  k_vent=1 / 7200,  auto_window=True,  heating=True,  noise=0,  daylight=1.0, lamps=True),
    "comfortable": dict(occ=lambda h: 4,       t_out=20,   k_vent=1 / 900,  auto_window=False, heating=True,  noise=0,  daylight=1.0, lamps=True),
    "stuffy":      dict(occ=lambda h: 30,      t_out=24, k_vent=1 / 4000,  auto_window=False, heating=False, noise=5,  daylight=1.0, lamps=True),
    "cold-dark":   dict(occ=lambda h: 10,      t_out=2,  k_vent=1 / 1200,  auto_window=False, heating=False, noise=0,  daylight=0.03, lamps=False),
    "noisy":       dict(occ=lambda h: 28,      t_out=14, k_vent=1 / 900,   auto_window=False, heating=True,  noise=24, daylight=1.0, lamps=True),
}


class Room:
    def __init__(self, scenario: str, start_hour: float, rng: random.Random):
        self.rng = rng
        self.hour = start_hour
        self.window_open = False
        self.cloud = 1.0
        self.noise_burst = 0.0
        self.set_scenario(scenario)
        self.temp, self.hum, self.co2 = 20.5, 45.0, 430.0
        self.lux, self.noise = 300.0, 38.0
        self.advance(1)

    def set_scenario(self, name: str):
        self.name = name
        self.p = SCENARIOS[name]

    def advance(self, dt: float):
        """Інтегрує модель на dt секунд модельного часу (кроками ≤ 30 с)."""
        while dt > 0:
            step = min(dt, 30.0)
            self._step(step)
            dt -= step

    def _step(self, dt: float):
        p, h = self.p, self.hour % 24
        occ = p["occ"](h)
        if p["auto_window"]:    # відчиняють на перервах або коли душно; зачиняють, коли провітрилось
            in_break = 8.0 <= h < 13.6 and occ < 10
            if in_break or self.co2 > 1600:
                self.window_open = True
            elif self.co2 < 800 and not in_break:
                self.window_open = False
        k_vent = 1 / 600 if self.window_open else p["k_vent"]

        # CO2: ~5 мл/с на людину в кімнаті ~180 м³  =>  0.0278 ppm/с на людину
        self.co2 += (occ * 0.0278 - k_vent * (self.co2 - 420)) * dt
        # Температура: тепло людей і ламп, опалення, втрати назовні
        lamps = 300 if p["lamps"] and occ > 0 else 0
        heater = 0.0016 if p["heating"] and self.temp < 21.0 else 0.0
        k_t = 1 / 4200 if self.window_open else 1 / 9000
        self.temp += ((occ * 80 + lamps) / 2.2e6 + heater - k_t * (self.temp - p["t_out"])) * dt
        # Вологість
        k_h = 1 / 900 if self.window_open else 1 / 10800
        self.hum += (occ * 0.00008 - k_h * (self.hum - 50)) * dt
        self.hum = max(15.0, min(95.0, self.hum))
        # Світло: денне (змінна хмарність) + лампи
        self.cloud = max(0.5, min(1.0, self.cloud + self.rng.uniform(-0.01, 0.01)))
        day = max(0.0, math.sin(math.pi * (h - 6) / 14)) * 650 * self.cloud * p["daylight"]
        self.lux = day + (350 if p["lamps"] and occ > 0 else 0) + (40 if p["lamps"] and occ == 0 and day < 5 else 0)
        # Шум: фон + люди + випадкові сплески, що згасають
        if occ > 0 and self.rng.random() < 0.02 * dt / 10:
            self.noise_burst = self.rng.uniform(8, 22)
        self.noise_burst *= math.exp(-dt / 25)
        base = 34 + (14 + 0.35 * occ if occ > 0 else 0) + p["noise"]
        self.noise = base + self.noise_burst
        self.hour += dt / 3600

    def read_sensors(self) -> dict:
        """Те, що повертає «залізо»: DHT11 — цілі числа, АЦП — u16 з шумом."""
        r = self.rng
        def adc(value, lo, hi):   # обернення формул backend: raw -> фізична величина
            raw = (value - lo) / (hi - lo) * RAW_MAX * (1 + r.gauss(0, 0.004))
            return int(max(0, min(RAW_MAX, round(raw))))
        return {
            "temperature": int(round(self.temp + r.gauss(0, 0.3))),
            "humidity": int(round(self.hum + r.gauss(0, 0.8))),
            "gas": adc(self.co2 + r.gauss(0, 12), 200, 10000),
            "sound": adc(self.noise + r.gauss(0, 1.2), 40, 120),
            "light": adc(self.lux * (1 + r.gauss(0, 0.01)), 0.1, 100000),
        }


# ═══════════════════════════════════ пристрій ═══════════════════════════════════
class Device(threading.Thread):
    def __init__(self, idx: int, device_id: str, scenario: str, args, state_dir: Path):
        super().__init__(daemon=True, name=f"dev{idx}")
        self.idx, self.id, self.args = idx, device_id, args
        self.rng = random.Random(f"{args.seed}-{idx}")
        self.room = Room(scenario, args.start_hour, self.rng)
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.offline = False
        self.client: mqtt.Client | None = None
        self.connected = threading.Event()
        self.buffer: list[dict] = []          # аналог ~measurement.json
        self.pending_config: dict | None = None   # аналог device.config_update
        self.settings_file = state_dir / f"{device_id}.settings.json"
        self.config = self._load_config()
        self.last_tick = time.monotonic()
        self.published = 0

    # ---------- конфіг / налаштування ----------
    def _load_config(self) -> dict:
        if self.settings_file.exists():
            try:
                return json.loads(self.settings_file.read_text())
            except ValueError:
                pass
        return {
            "user": {"login": "Boss", "password": "4444"},
            "mqtt": {"server": self.args.broker_host},
            "measurement_interval": self.args.interval_ms,
            "wifi": {"ssid": self.args.wifi_ssid, "password": self.args.wifi_password},
            "units": "standard",
            "ntp_host": "pool.ntp.org",
            "id": self.id,
        }

    @staticmethod
    def _has_all_keys(data, template) -> bool:       # lib/helpers.handle_settings_update
        for key, val in template.items():
            if key not in data:
                return False
            if isinstance(val, dict) and (not isinstance(data[key], dict) or not Device._has_all_keys(data[key], val)):
                return False
        return True

    def validate_settings(self, d: dict) -> str | None:
        """Повторює Settings.validate() з прошивки. Повертає текст помилки або None."""
        types = {"user": dict, "mqtt": dict, "measurement_interval": int, "wifi": dict,
                 "units": str, "ntp_host": str, "id": str}
        for key, t in types.items():
            if key not in d:
                return f"Missing key: {key}"
            if not isinstance(d[key], t) or isinstance(d[key], bool):
                return f"Invalid type for {key}: expected {t.__name__}"
        if "server" not in d["mqtt"]:
            return "MQTT config must contain server address"
        if d["measurement_interval"] < 1000:
            return "Measurement interval too short (min 1000ms)"
        if d["units"] not in ALLOWED_UNITS:
            return f"Invalid units. Allowed: {list(ALLOWED_UNITS)}"
        if d["id"] != self.id:
            return "Invalid device ID"
        for f in ("login", "password"):
            v = d["user"].get(f)
            if not isinstance(v, str) or not v.strip():
                return f"User {f} cannot be empty"
        if not all(k in d["wifi"] for k in ("ssid", "password")):
            return "Wi-Fi config must contain ssid and password"
        if not self.args.accept_any_wifi and (
                d["wifi"]["ssid"] != self.args.wifi_ssid or d["wifi"]["password"] != self.args.wifi_password):
            return "Incorrect Wi-Fi connection data"       # прошивка пробує реально підключитись
        if not HOST_RE.match(d["ntp_host"]):
            return "Unsuitable NTP host"
        return None

    def apply_pending_config(self):               # states/sleep.py
        cfg, self.pending_config = self.pending_config, None
        if not cfg or cfg == self.config:
            return
        err = self.validate_settings(cfg)
        if err:
            self.log(f"⛔ settings rejected: {err} (лишаються старі)")
            return
        self.config = cfg
        self.settings_file.write_text(json.dumps(cfg))
        self.log(f"⚙️  settings applied: interval={cfg['measurement_interval']}ms units={cfg['units']} "
                 f"broker={cfg['mqtt']['server'] or '-'}")

    # ---------- MQTT ----------
    def _topic(self, mode: str) -> str:
        return f"iot/device/{self.id}/{mode}"

    def connect(self) -> bool:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.id, clean_session=True)
        if self.args.broker_user:
            c.username_pw_set(self.args.broker_user, self.args.broker_password)
        c.will_set(self._topic("status"), json.dumps({"status": "offline"}), retain=True)
        c.on_connect = self._on_connect
        c.on_message = self._on_message
        c.on_disconnect = lambda *a, **k: self.connected.clear()
        self.connected.clear()
        try:
            c.connect(self.args.broker_host, self.args.broker_port, keepalive=60)
        except OSError as exc:
            self.log(f"❌ MQTT connect failed: {exc}")
            return False
        c.loop_start()
        self.client = c
        return self.connected.wait(5)

    def _on_connect(self, c, userdata, flags, rc, props):
        if rc.is_failure:
            self.log(f"❌ MQTT refused: {rc}")
            return
        c.publish(self._topic("status"), json.dumps({"status": "online"}), retain=True)
        c.subscribe(f"iot/backend/{self.id}/settings")
        c.subscribe(f"iot/backend/{self.id}/command")
        self.connected.set()

    def _on_message(self, c, userdata, msg):      # lib/mqtt_handler.py
        try:
            payload = json.loads(msg.payload.decode())
        except ValueError:
            self.log(f"⚠️ non-JSON message on {msg.topic}")
            return
        if not payload:
            return
        if "settings" in msg.topic:
            if self._has_all_keys(payload, DEFAULT_SETTINGS):
                self.pending_config = payload
                self.log(f"📥 settings received (retain={bool(msg.retain)})")
            else:
                self.log("⚠️ settings ignored: incomplete structure")
        elif "command" in msg.topic:
            self.log(f"📥 command: {payload}")

    def disconnect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            self.connected.clear()

    # ---------- один цикл (Measurement -> ConnectNetwork -> PublishData -> Sleep) ----------
    def measure(self):
        now = time.monotonic()
        self.room.advance((now - self.last_tick) * self.args.speed)
        self.last_tick = now
        m = self.room.read_sensors()
        m["dt"] = self._timestamp()
        self.buffer.append(m)

    def _timestamp(self):
        now = time.time()
        if self.args.ts_format == "epoch":
            return int(now)
        return datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def payload_for(self, m: dict) -> dict:       # states/publish_data.py
        return {"timestamp": m["dt"], "sensors": {
            "temperature": {"value": m["temperature"], "units": self.config["units"]},
            "humidity": {"value": m["humidity"], "units": "%"},
            "sound": {"value": m["sound"], "units": "dB"},
            "gas": {"value": m["gas"], "units": "ppm"},
            "light": {"value": m["light"], "units": "lx"},
        }}

    def publish_buffer(self):
        if self.offline or self.rng.random() < self.args.offline_prob:
            self.log(f"📴 Wi-Fi недоступний, у буфері {len(self.buffer)} вимір.")
            return
        if not (self.client and self.connected.is_set()) and not self.connect():
            return
        backlog = len(self.buffer)
        for m in self.buffer:
            self.client.publish(self._topic("telemetry"), json.dumps(self.payload_for(m)), qos=0)
            self.published += 1
        last = self.buffer[-1]
        self.buffer.clear()
        c = self.room
        self.log(f"📤 {'+%d backlog ' % (backlog - 1) if backlog > 1 else ''}"
                 f"T={last['temperature']}°C H={last['humidity']}% "
                 f"CO2≈{c.co2:4.0f}ppm lux≈{c.lux:4.0f} {c.noise:2.0f}dB "
                 f"[{c.name} {int(c.hour % 24):02d}:{int((c.hour % 1) * 60):02d}"
                 f"{' 🪟' if c.window_open else ''}] raw(g/s/l)={last['gas']}/{last['sound']}/{last['light']}")

    def run(self):
        self.log(f"▶ start, scenario={self.room.name}, interval={self.config['measurement_interval']}ms")
        while not self.stop_event.is_set():
            try:
                self.measure()
                self.publish_buffer()
                if self.args.firmware_cycle:
                    self.stop_event.wait(1.5)       # вікно для retained-налаштувань, потім «сон»
                    self.disconnect()
                self.apply_pending_config()
            except Exception as exc:                # прошивка йде в Error-стан; тут просто лог
                self.log(f"❌ cycle error: {exc!r}")
            self.wake.wait(self.config["measurement_interval"] / 1000)
            self.wake.clear()
        self.disconnect()

    def stop(self):
        self.stop_event.set()
        self.wake.set()

    def log(self, msg: str):
        print(f"{datetime.now():%H:%M:%S} {self.id[4:12]}… {msg}", flush=True)

    # ---------- інʼєкція несправностей ----------
    def send_bad(self):
        if not (self.client and self.connected.is_set()) and not self.connect():
            return
        t = self._topic("telemetry")
        good = self.payload_for({**self.room.read_sensors(), "dt": self._timestamp()})
        no_units = json.loads(json.dumps(good)); no_units["sensors"]["gas"].pop("units")
        missing = json.loads(json.dumps(good)); missing["sensors"].pop("light")
        for label, body in (("не JSON", "{oops"), ("без units", json.dumps(no_units)),
                            ("без датчика light", json.dumps(missing)),
                            ("текст замість значення", json.dumps({**good, "sensors": {**good["sensors"],
                             "humidity": {"value": "n/a", "units": "%"}}}))):
            self.client.publish(t, body)
            self.log(f"💥 надіслано некоректний payload ({label}) — backend має його проігнорувати")


# ═══════════════════════════════════════ CLI ═══════════════════════════════════════
def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--broker", default="localhost:1883", help="MQTT broker host[:port] (за замовч. localhost:1883)")
    ap.add_argument("--broker-user"); ap.add_argument("--broker-password", default="")
    ap.add_argument("--devices", type=int, default=3, help="кількість пристроїв/кімнат")
    ap.add_argument("--ids", help="явні id через кому (замість згенерованих com-…-fort)")
    ap.add_argument("--scenarios", default="school-day,comfortable,stuffy",
                    help=f"сценарії по колу для пристроїв: {', '.join(SCENARIOS)}")
    ap.add_argument("--interval-ms", type=int, default=10000, help="початковий measurement_interval")
    ap.add_argument("--speed", type=float, default=1.0, help="швидкість моделі (30 = 1 с реального часу ≈ 30 с моделі)")
    ap.add_argument("--start-hour", type=float, default=7.9, help="початок модельного дня (годин, 0–24)")
    ap.add_argument("--ts-format", choices=("iso", "epoch"), default="iso", help="iso — як прошивка; epoch — як у MQTT.md")
    ap.add_argument("--offline-prob", type=float, default=0.0, help="імовірність втрати Wi-Fi у циклі (0–1)")
    ap.add_argument("--firmware-cycle", action="store_true", help="підключатись/відключатись щоразу, як прошивка")
    ap.add_argument("--wifi-ssid", default="Komiki"); ap.add_argument("--wifi-password", default="Parol222")
    ap.add_argument("--accept-any-wifi", action="store_true", help="не відхиляти налаштування з іншим Wi-Fi")
    ap.add_argument("--seed", default="42"); ap.add_argument("--state-dir", default=".sim_state")
    a = ap.parse_args()
    host, _, port = a.broker.partition(":")
    a.broker_host, a.broker_port = host, int(port or 1883)
    return a


def main():
    args = parse_args()
    state_dir = Path(args.state_dir); state_dir.mkdir(exist_ok=True)
    scen = [s.strip() for s in args.scenarios.split(",")]
    bad = [s for s in scen if s not in SCENARIOS]
    if bad:
        sys.exit(f"Невідомі сценарії: {bad}. Доступні: {list(SCENARIOS)}")
    ids = args.ids.split(",") if args.ids else [device_id_for(i) for i in range(args.devices)]
    devices = [Device(i, did, scen[i % len(scen)], args, state_dir) for i, did in enumerate(ids)]

    print(f"Брокер {args.broker_host}:{args.broker_port}; Wi-Fi '{args.wifi_ssid}'/'{args.wifi_password}'; формат часу: {args.ts_format}")
    print("Пристрої (ці id вводьте у фронтенді при додаванні кімнати):")
    for d in devices:
        print(f"  [{d.idx}] {d.id}   сценарій: {d.room.name}")
    print("Команди: help | status | scenario <ім'я> [n] | offline [on|off] | bad | burst <N> | quit\n")
    for d in devices:
        d.start()

    def pick(parts, pos):
        return [devices[int(parts[pos])]] if len(parts) > pos and parts[pos].isdigit() and int(parts[pos]) < len(devices) else devices

    quit_requested = False
    try:
        for line in sys.stdin:
            parts = line.split()
            if not parts:
                continue
            cmd = parts[0].lower()
            if cmd in ("quit", "exit", "q"):
                quit_requested = True
                break
            elif cmd == "help":
                print(__doc__.split("Інтерактивні команди (stdin):")[1].strip())
            elif cmd == "status":
                for d in devices:
                    print(f"  [{d.idx}] {d.id} {d.room.name} offline={d.offline} buffer={len(d.buffer)} "
                          f"published={d.published} interval={d.config['measurement_interval']}ms units={d.config['units']}")
            elif cmd == "scenario" and len(parts) > 1 and parts[1] in SCENARIOS:
                for d in pick(parts, 2):
                    d.room.set_scenario(parts[1]); d.log(f"сценарій -> {parts[1]}")
            elif cmd == "offline":
                state = parts[1] if len(parts) > 1 else "on"
                for d in devices:
                    d.offline = state != "off"
                print(f"offline = {state != 'off'}")
            elif cmd == "bad":
                for d in devices[:1]:
                    d.send_bad()
            elif cmd == "burst" and len(parts) > 1 and parts[1].isdigit():
                for d in devices[:1]:
                    for _ in range(int(parts[1])):
                        d.room.advance(30); d.measure()
                    d.wake.set()
            else:
                print("невідома команда, див. help")
        while not quit_requested:       # stdin закрито (запуск у фоні/Docker) — працюємо до Ctrl+C
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for d in devices:
            d.stop()
        time.sleep(0.5)


if __name__ == "__main__":
    main()
