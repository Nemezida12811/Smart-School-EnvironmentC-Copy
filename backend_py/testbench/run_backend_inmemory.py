#!/usr/bin/env python3
"""Запускає backend БЕЗ MongoDB: дані зберігаються в памʼяті (mongomock) і зникають після зупинки.
Зручно для швидкої перевірки. MQTT-брокер усе одно потрібен (MQTT_URL).

  pip install mongomock
  MQTT_URL=mqtt://localhost:1883 PORT=3001 python testbench/run_backend_inmemory.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("JWT_SECRET", "dev-secret")
os.environ.setdefault("MONGO_URI", "in-memory")
os.environ.setdefault("MQTT_URL", "mqtt://localhost:1883")

import mongomock
import uvicorn

from app.config import settings
from app.db import database


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


async def _connect(uri, name):
    database.db = _FakeDb()
    print("✅ In-memory database (mongomock) — дані не зберігаються між запусками")

database.connect = _connect

if __name__ == "__main__":
    from app.main import app
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
