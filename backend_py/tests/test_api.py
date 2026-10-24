"""Smoke test of entire API on mongomock (real MongoDB not needed)."""
import asyncio
import json
import os

os.environ["JWT_SECRET"] = "test-secret"

import mongomock
import pytest
from fastapi.testclient import TestClient

from app.comfort import calculate_manual_comfort
from app.db import database
from app.main import app
from app.telemetry import convert_units, handle_message, parse_telemetry, parse_timestamp


class _Cursor:
    def __init__(self, cur): self.cur = cur
    async def to_list(self, _=None): return list(self.cur)


class _AsyncCollection:
    def __init__(self, col): self.col = col
    def __getattr__(self, name):
        fn = getattr(self.col, name)
        if name == "find":
            return lambda *a, **k: _Cursor(fn(*a, **k))
        async def call(*a, **k): return fn(*a, **k)
        return call


class _FakeDb:
    def __init__(self): self.db = mongomock.MongoClient().db
    def __getitem__(self, name): return _AsyncCollection(self.db[name])


@pytest.fixture()
def client():
    database.db = _FakeDb()
    return TestClient(app)  # without `with` -> lifespan (real Mongo/MQTT) does not start


def hdr(token): return {"Authorization": f"Bearer {token}"}


def register(c, name, email):
    r = c.post("/api/auth/register", json={"username": name, "email": email, "password": "secret1"})
    assert r.status_code == 201, r.text
    return r.json()["data"]


def telemetry(device_id, raw=32768):
    payload = {"timestamp": 1765978387, "sensors": {
        "temperature": {"value": 22, "units": "C"}, "humidity": {"value": 45, "units": "%"},
        "gas": {"value": raw, "units": "ppm"}, "light": {"value": raw, "units": "lx"},
        "sound": {"value": raw, "units": "dB"}}}
    asyncio.run(handle_message(f"iot/device/{device_id}/telemetry", json.dumps(payload).encode()))


def test_auth(client):
    assert client.get("/").json() == {"message": "Backend is running"}
    assert client.post("/api/auth/register", json={"email": "a@b.c"}).json()["error"]["message"] == "All fields are required"
    assert client.post("/api/auth/register", json={"username": "u", "email": "bad", "password": "123456"}).status_code == 400
    d = register(client, "roma", "roma@x.sk")
    assert client.post("/api/auth/register", json={"username": "r", "email": "roma@x.sk", "password": "123456"}).status_code == 400
    assert client.post("/api/auth/login", json={"email": "roma@x.sk", "password": "wrong!!"}).status_code == 401
    login = client.post("/api/auth/login", json={"email": "roma@x.sk", "password": "secret1"}).json()["data"]
    assert login["user"]["id"] == d["user"]["id"] and login["user"]["createdAt"].endswith("Z")
    assert client.get("/api/auth/me", headers=hdr(login["token"])).json()["data"]["username"] == "roma"
    assert client.get("/api/auth/me").json()["error"]["message"] == "No token provided"
    assert client.get("/api/auth/me", headers=hdr("garbage")).status_code == 401


def test_locations_and_devices(client):
    admin, other = register(client, "a", "a@x.sk"), register(client, "o", "o@x.sk")
    A, O = hdr(admin["token"]), hdr(other["token"])

    loc = client.post("/api/locations", json={"name": "Lab"}, headers=A).json()["data"]
    lid = loc["id"]
    lst = client.get("/api/locations", headers=A).json()["data"]
    assert [l["id"] for l in lst["created"]] == [lid] and lst["joined"] == []

    assert client.patch(f"/api/locations/{lid}", json={"name": "X"}, headers=O).status_code == 403
    assert client.patch(f"/api/locations/{lid}", json={"name": "Lab2"}, headers=A).status_code == 200
    assert client.get("/api/locations/not-an-id").status_code == 404

    assert client.post(f"/api/locations/{lid}/devices", json={"deviceId": "dev1"}, headers=A).status_code == 404
    telemetry("dev1")
    assert client.post(f"/api/locations/{lid}/devices", json={"deviceId": "dev1", "name": "Room 1"}, headers=A).status_code == 200

    s = client.get("/api/comfort/dev1/sensors").json()["data"]
    assert s["name"] == "Room 1" and s["hidden"] is False
    assert s["latestReading"]["gas"] == 5100 and s["latestReading"]["sound"] == 80
    assert s["timestamp"] == "2025-12-17T13:33:07.000Z"
    assert client.get("/api/comfort/dev1").json()["data"]["comfortPercentage"] == 45

    assert client.patch(f"/api/locations/{lid}/devices/dev1/hide", headers=A).status_code == 200
    assert client.get("/api/comfort/dev1/sensors").json()["data"]["hidden"] is True
    assert client.patch(f"/api/locations/{lid}/devices/dev1/show", headers=A).status_code == 200
    r = client.patch(f"/api/locations/{lid}/devices/dev1/settings", json={"interval": 5000}, headers=A).json()["data"]
    assert r["topic"] == "iot/backend/dev1/settings" and r["settings"]["measurement_interval"] == 5000

    assert client.post(f"/api/locations/{lid}/users", json={"targetUserId": other["user"]["id"]}, headers=A).status_code == 200
    assert client.post(f"/api/locations/{lid}/users", json={"targetUserId": other["user"]["id"]}, headers=A).status_code == 400
    assert len(client.get("/api/locations", headers=O).json()["data"]["joined"]) == 1
    assert client.delete(f"/api/locations/{lid}/users/{admin['user']['id']}", headers=A).status_code == 400
    assert client.delete(f"/api/locations/{lid}/users/{other['user']['id']}", headers=A).status_code == 200
    assert client.delete(f"/api/locations/{lid}", headers=A).status_code == 200
    assert client.get("/api/auth/me", headers=A).json()["data"]["ownedLocationIds"] == []


def _fake_ai(create):
    """OpenAI client replacement: object with chat.completions.create(**kwargs)."""
    ns = lambda **kw: type("N", (), kw)  # noqa: E731
    return ns(chat=ns(completions=ns(create=staticmethod(create))))


def test_recommendations_openai_success(client, monkeypatch):
    telemetry("dev-8")
    from app import comfort
    seen = {}

    async def create(**kwargs):
        seen.update(kwargs)
        tips = [{"priority": "high", "type": "gas", "message": "Open a window", "reason": "CO2 is high"}]
        msg = type("M", (), {"content": json.dumps({"recommendations": tips})})
        return type("R", (), {"choices": [type("C", (), {"message": msg})]})

    monkeypatch.setattr(comfort, "_get_ai", lambda: _fake_ai(create))
    r = client.get("/api/comfort/dev-8/recommendations")
    assert r.status_code == 200
    assert r.json()["data"]["recommendations"][0]["message"] == "Open a window"
    assert seen["response_format"]["type"] == "json_schema" and seen["response_format"]["json_schema"]["strict"] is True
    assert "gas" in seen["messages"][1]["content"].lower() or "Gas" in seen["messages"][1]["content"]


def test_recommendations_empty_list_is_ok(client, monkeypatch):
    telemetry("dev-7")
    from app import comfort

    async def boom(**kwargs): raise RuntimeError("no key")

    monkeypatch.setattr(comfort, "_get_ai", lambda: _fake_ai(boom))
    r = client.get("/api/comfort/dev-7/recommendations")
    assert r.status_code == 200 and r.json()["data"]["recommendations"] == []
    assert r.json()["data"]["audienceId"] is None
    assert client.get("/api/comfort/missing/recommendations").status_code == 404


def test_telemetry_helpers():
    t = parse_telemetry({"sensors": {"temperature": {"value": "abc", "units": "C"}}})
    assert t["temperature"] != t["temperature"]  # NaN
    assert calculate_manual_comfort({"temperature": 22, "humidity": 45, "gas": 600, "light": 500, "sound": 30}) == 100
    assert calculate_manual_comfort({"temperature": 27, "humidity": 45, "gas": 600, "light": 500, "sound": 30}) == 88


def test_timestamp_formats():
    assert parse_timestamp(1765978387) == 1765978387000          # epoch, seconds (MQTT.md)
    assert parse_timestamp("1765978387") == 1765978387000
    assert parse_timestamp("2025-12-17T13:33:07Z") == 1765978387000   # ISO — firmware format
    assert parse_timestamp(1765978387000) == 1765978387000       # milliseconds
    import time
    assert abs(parse_timestamp(None) - time.time() * 1000) < 2000
    assert abs(parse_timestamp("garbage") - time.time() * 1000) < 2000


def test_openai_api_connection():
    """Checks real connection to OpenAI API."""
    from openai import OpenAI
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_MODEL")
    if not model:
        pytest.fail("OPENAI_MODEL is not configured in .env")

    with OpenAI(api_key=api_key) as client:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with exactly: OpenAI API works!",
                }
            ],
            max_completion_tokens=30,
        )

    assert response.choices[0].message.content.strip() == "OpenAI API works!"
