#!/usr/bin/env python3
"""
Наскрізна перевірка: пристрій(емулятор) -> MQTT -> backend -> MongoDB -> REST (те, що бачить frontend).
Запускайте, коли працюють broker, backend і device_simulator.py.

  python testbench/e2e_check.py --api http://localhost:3001 --broker localhost:1883
"""
import argparse
import json
import random
import string
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
from device_simulator import device_id_for  # noqa: E402

RESULTS: list[tuple[str, str, str]] = []


def record(status: str, name: str, detail: str = ""):
    RESULTS.append((status, name, detail))
    icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️ ", "SKIP": "⏭ "}[status]
    print(f"{icon} {name}" + (f" — {detail}" if detail else ""), flush=True)


def check(cond: bool, name: str, detail: str = "", warn_only: bool = False):
    record("PASS" if cond else ("WARN" if warn_only else "FAIL"), name, "" if cond else detail)
    return cond


class Api:
    def __init__(self, base: str): self.base = base.rstrip("/")

    def call(self, method: str, path: str, body=None, token: str | None = None):
        req = urllib.request.Request(self.base + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None)
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read() or b"{}")
            except ValueError:
                return e.code, {}


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:3001")
    ap.add_argument("--broker", default="localhost:1883")
    ap.add_argument("--devices", type=int, default=3)
    ap.add_argument("--ids", help="id пристроїв через кому (якщо не за замовчуванням)")
    ap.add_argument("--wait", type=int, default=60, help="скільки чекати першу телеметрію, с")
    ap.add_argument("--wifi-ssid", default="Komiki"); ap.add_argument("--wifi-password", default="Parol222")
    ap.add_argument("--keep", action="store_true", help="не видаляти створену локацію (щоб подивитись у frontend)")
    a = ap.parse_args()
    api = Api(a.api)
    ids = a.ids.split(",") if a.ids else [device_id_for(i) for i in range(a.devices)]
    rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

    print(f"\n== 1. Backend доступний ({a.api}) ==")
    for _ in range(20):
        try:
            st, body = api.call("GET", "/")
            break
        except OSError:
            time.sleep(1)
    else:
        record("FAIL", "GET /", "backend не відповідає"); return finish()
    check(st == 200 and body.get("message") == "Backend is running", "GET / відповідає")

    print("\n== 2. Телеметрія з емулятора дійшла до БД (device → MQTT → backend → MongoDB) ==")
    readings = {}
    deadline = time.time() + a.wait
    pending = set(ids)
    while pending and time.time() < deadline:
        for did in list(pending):
            st, body = api.call("GET", f"/api/comfort/{did}/sensors")
            if st == 200:
                readings[did] = body["data"]; pending.discard(did)
        time.sleep(1)
    for did in ids:
        if not check(did in readings, f"телеметрія пристрою {did[4:12]}… збережена", f"немає даних за {a.wait} с — чи запущено device_simulator.py і той самий broker?"):
            continue
        d = readings[did]; r = d["latestReading"]
        check(set(r["units"]) == {"temperature", "humidity", "gas", "light", "sound"} and all(r["units"].values()),
              "  units для 5 датчиків", str(r["units"]))
        check(-10 <= r["temperature"] <= 50 and 0 <= r["humidity"] <= 100, "  температура/вологість правдоподібні", f"{r['temperature']}°C {r['humidity']}%")
        check(200 <= r["gas"] <= 10000 and 40 <= r["sound"] <= 120 and 0.1 <= r["light"] <= 100000,
              "  gas/sound/light у діапазонах конвертації backend", f"gas={r['gas']} sound={r['sound']} light={r['light']}")
        age = (datetime.now(timezone.utc) - parse_iso(d["timestamp"])).total_seconds()
        check(-5 <= age <= 120, "  timestamp свіжий і розпізнаний (ISO від прошивки)", f"вік {age:.0f} с, timestamp={d['timestamp']}")
        st, c = api.call("GET", f"/api/comfort/{did}")
        check(st == 200 and isinstance(c["data"]["comfortPercentage"], int) and 0 <= c["data"]["comfortPercentage"] <= 100,
              "  відсоток комфорту 0..100", f"{st} {c}")
    live_ids = [d for d in ids if d in readings]

    print("\n== 3. Auth ==")
    email, pw = f"e2e-{rnd}@test.local", "secret123"
    st, b = api.call("POST", "/api/auth/register", {"username": f"e2e-{rnd}", "email": email, "password": pw})
    check(st == 201 and b["data"]["token"], "реєстрація → 201 + token", f"{st} {b}")
    st, b2 = api.call("POST", "/api/auth/register", {"username": "x", "email": email, "password": pw})
    check(st == 400, "дубль email → 400", f"{st}")
    st, b2 = api.call("POST", "/api/auth/login", {"email": email, "password": "wrong-pass"})
    check(st == 401, "невірний пароль → 401", f"{st}")
    st, lg = api.call("POST", "/api/auth/login", {"email": email, "password": pw})
    token = lg["data"]["token"]
    check(st == 200 and lg["data"]["user"]["email"] == email, "логін")
    st, me = api.call("GET", "/api/auth/me", token=token)
    check(st == 200 and me["data"]["username"] == f"e2e-{rnd}", "GET /me з токеном")
    check(api.call("GET", "/api/auth/me")[0] == 401, "GET /me без токена → 401")

    print("\n== 4. Локації та кімнати (сценарій фронтенда) ==")
    st, loc = api.call("POST", "/api/locations", {"name": f"E2E School {rnd}"}, token)
    check(st == 201, "створення локації", f"{st} {loc}")
    lid = loc["data"]["id"]
    check(api.call("POST", f"/api/locations/{lid}/devices", {"deviceId": "com-ffffffffffffffff-fort"}, token)[0] == 404,
          "додати неіснуючий пристрій → 404")
    for i, did in enumerate(live_ids):
        st, _ = api.call("POST", f"/api/locations/{lid}/devices", {"deviceId": did, "name": f"Кабінет {i + 1}"}, token)
        check(st == 200, f"додати пристрій {did[4:12]}… як «Кабінет {i + 1}»", f"{st}")
    st, lst = api.call("GET", "/api/locations", token=token)
    mine = [x for x in lst["data"]["created"] if x["id"] == lid]
    check(bool(mine) and sorted(mine[0]["deviceIds"]) == sorted(live_ids), "список локацій містить усі пристрої")
    if live_ids:
        d0 = live_ids[0]
        st, s = api.call("GET", f"/api/comfort/{d0}/sensors")
        check(s["data"]["name"] == "Кабінет 1" and s["data"]["hidden"] is False, "ім'я кімнати збережено", str(s))
        check(api.call("PATCH", f"/api/locations/{lid}/devices/{d0}/hide", token=token)[0] == 200
              and api.call("GET", f"/api/comfort/{d0}/sensors")[1]["data"]["hidden"] is True, "приховати кімнату")
        check(api.call("PATCH", f"/api/locations/{lid}/devices/{d0}/show", token=token)[0] == 200
              and api.call("GET", f"/api/comfort/{d0}/sensors")[1]["data"]["hidden"] is False, "показати кімнату")
        st, rec = api.call("GET", f"/api/comfort/{d0}/recommendations")
        tips = rec.get("data", {}).get("recommendations")
        check(st == 200 and isinstance(tips, list), "рекомендації: 200 і список", f"{st} {rec}")
        check(bool(tips), "  AI повернув поради (потрібен OPENAI_API_KEY)", "порожній список", warn_only=True)
        if tips:
            check(all({"priority", "type", "message", "reason"} <= set(t) for t in tips), "  структура порад")

    print("\n== 5. Другий користувач і права ==")
    st, ub = api.call("POST", "/api/auth/register", {"username": f"guest-{rnd}", "email": f"guest-{rnd}@test.local", "password": pw})
    tok2, uid2 = ub["data"]["token"], ub["data"]["user"]["id"]
    check(api.call("PATCH", f"/api/locations/{lid}", {"name": "hack"}, tok2)[0] == 403, "не-адмін не може перейменувати локацію → 403")
    check(api.call("POST", f"/api/locations/{lid}/users", {"targetUserId": uid2}, token)[0] == 200, "адмін додає користувача")
    st, l2 = api.call("GET", "/api/locations", token=tok2)
    check(any(x["id"] == lid for x in l2["data"]["joined"]), "локація з'являється у 'joined' гостя")
    if live_ids:
        check(api.call("PATCH", f"/api/locations/{lid}/devices/{live_ids[0]}/hide", token=tok2)[0] == 403, "гість не може ховати кімнату → 403")
    check(api.call("DELETE", f"/api/locations/{lid}/users/{uid2}", token=token)[0] == 200, "адмін видаляє користувача")

    print("\n== 6. Налаштування пристрою: backend → MQTT → пристрій → нові дані ==")
    if live_ids:
        d0 = live_ids[0]
        body = {"name": "Кабінет 1 (перейм.)", "units": "metric", "interval": 3000, "ntpHost": "pool.ntp.org",
                "brokerAddress": a.broker.split(":")[0], "wifiSsid": a.wifi_ssid, "wifiPassword": a.wifi_password}
        st, r = api.call("PATCH", f"/api/locations/{lid}/devices/{d0}/settings", body, token)
        check(st == 200 and r["data"]["topic"] == f"iot/backend/{d0}/settings", "PATCH settings опубліковано в MQTT", f"{st} {r}")
        print("   чекаю, поки пристрій застосує налаштування (інтервал 3 с, units=metric)…")
        stamps, units, t_end = set(), None, time.time() + 45
        while time.time() < t_end:
            s = api.call("GET", f"/api/comfort/{d0}/sensors")[1]["data"]
            units = s["latestReading"]["units"]["temperature"]
            stamps.add(s["timestamp"])
            if units == "metric":
                break
            time.sleep(1)
        check(units == "metric", "пристрій застосував units=metric (видно в REST)", f"units={units} — чи запущено емулятор з тим самим Wi-Fi?")
        seen, t_end = {}, time.time() + 12
        while time.time() < t_end:
            seen[api.call("GET", f"/api/comfort/{d0}/sensors")[1]["data"]["timestamp"]] = 1
            time.sleep(0.5)
        check(len(seen) >= 3, "частота оновлень зросла (≥3 нових timestamp за 12 с при інтервалі 3 с)", f"було {len(seen)}")
        check(api.call("GET", f"/api/comfort/{d0}/sensors")[1]["data"]["name"] == "Кабінет 1 (перейм.)", "нове ім'я кімнати збережено")

        # Прошивка відхиляє налаштування з неправильним Wi-Fi — частота не має змінитись на 20 с
        bad = dict(body, interval=20000, wifiPassword="WRONG-PASSWORD")
        api.call("PATCH", f"/api/locations/{lid}/devices/{d0}/settings", bad, token)
        time.sleep(5)
        seen, t_end = {}, time.time() + 10
        while time.time() < t_end:
            seen[api.call("GET", f"/api/comfort/{d0}/sensors")[1]["data"]["timestamp"]] = 1
            time.sleep(0.5)
        check(len(seen) >= 2, "налаштування з хибним Wi-Fi відхилено пристроєм (частота лишилась ~3 с)", f"{len(seen)} оновл. за 10 с",
              warn_only=True)
        api.call("PATCH", f"/api/locations/{lid}/devices/{d0}/settings", dict(body, interval=10000), token)

    print("\n== 7. Стійкість до некоректної телеметрії та формати часу ==")
    try:
        import paho.mqtt.client as mqtt
        host, _, port = a.broker.partition(":")
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"e2e-{rnd}")
        c.connect(host, int(port or 1883)); c.loop_start()
        def sensors(ts):
            return {"timestamp": ts, "sensors": {
                "temperature": {"value": 22, "units": "standard"}, "humidity": {"value": 45, "units": "%"},
                "sound": {"value": 6000, "units": "dB"}, "gas": {"value": 2000, "units": "ppm"}, "light": {"value": 300, "units": "lx"}}}
        base = f"com-e2e{rnd}"
        pubs = {
            f"{base}bad-fort": ["{not json", json.dumps({"sensors": {}}),
                                json.dumps({"timestamp": 1, "sensors": {**sensors(1)["sensors"], "gas": {"value": 5}}})],
            f"{base}iso-fort": [json.dumps(sensors("2025-12-17T13:33:07Z"))],
            f"{base}epoch-fort": [json.dumps(sensors(1765978387))],
        }
        for dev, msgs in pubs.items():
            for m in msgs:
                c.publish(f"iot/device/{dev}/telemetry", m, qos=1).wait_for_publish(3)
        time.sleep(2)
        st, _ = api.call("GET", f"/api/comfort/{base}bad-fort/sensors")
        check(st == 404, "некоректні payload (не JSON / без датчиків / без units) відкинуто", f"статус {st}")
        for kind in ("iso", "epoch"):
            st, r = api.call("GET", f"/api/comfort/{base}{kind}-fort/sensors")
            ok = st == 200 and r["data"]["timestamp"] == "2025-12-17T13:33:07.000Z"
            check(ok, f"timestamp у форматі {kind.upper()} розпізнано коректно", f"{st} {r.get('data', {}).get('timestamp')}")
        c.loop_stop(); c.disconnect()
    except OSError as exc:
        record("SKIP", "перевірка некоректної телеметрії", f"broker недоступний: {exc}")

    print("\n== 8. Прибирання ==")
    if a.keep:
        record("SKIP", "видалення локації", f"залишено для перегляду у frontend: {email} / {pw}")
    else:
        check(api.call("DELETE", f"/api/locations/{lid}", token=token)[0] == 200, "видалення локації")
        check(api.call("GET", f"/api/locations/{lid}")[0] == 404, "локація зникла")
    finish()


def finish():
    n = {k: sum(1 for r in RESULTS if r[0] == k) for k in ("PASS", "FAIL", "WARN", "SKIP")}
    print(f"\n{'=' * 60}\nПідсумок: ✅ {n['PASS']}  ❌ {n['FAIL']}  ⚠️  {n['WARN']}  ⏭ {n['SKIP']}")
    for s, name, detail in RESULTS:
        if s in ("FAIL", "WARN"):
            print(f"  {s}: {name} {detail}")
    sys.exit(1 if n["FAIL"] else 0)


if __name__ == "__main__":
    main()
