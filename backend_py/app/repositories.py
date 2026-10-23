"""Доступ до MongoDB. Структура колекцій і документів 1:1 з Node-версією."""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from .db import database
from .errors import iso


def to_oid(value) -> ObjectId | None:
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ───────────────────────────── users ─────────────────────────────
class Users:
    @staticmethod
    def _c():
        return database.collection("users")

    @classmethod
    async def create(cls, username: str, email: str, password_hash: str):
        res = await cls._c().insert_one({
            "username": username,
            "email": email,
            "password": password_hash,
            "role": "user",
            "ownedLocationIds": [],
            "accessibleLocationIds": [],
            "createdAt": _now(),
        })
        return res.inserted_id

    @classmethod
    async def find_by_email(cls, email: str):
        return await cls._c().find_one({"email": email})

    @classmethod
    async def find_by_id(cls, user_id):
        oid = to_oid(user_id)
        return await cls._c().find_one({"_id": oid}) if oid else None

    @classmethod
    async def _push(cls, user_id, field: str, location_id, op: str):
        await cls._c().update_one({"_id": to_oid(user_id)}, {op: {field: to_oid(location_id)}})

    @classmethod
    async def add_owned_location(cls, user_id, location_id):
        await cls._push(user_id, "ownedLocationIds", location_id, "$addToSet")

    @classmethod
    async def add_accessible_location(cls, user_id, location_id):
        await cls._push(user_id, "accessibleLocationIds", location_id, "$addToSet")

    @classmethod
    async def remove_owned_location(cls, user_id, location_id):
        await cls._push(user_id, "ownedLocationIds", location_id, "$pull")

    @classmethod
    async def remove_accessible_location(cls, user_id, location_id):
        await cls._push(user_id, "accessibleLocationIds", location_id, "$pull")

    @staticmethod
    def to_json(u: dict) -> dict:
        return {
            "id": str(u["_id"]),
            "username": u.get("username"),
            "email": u.get("email"),
            "role": u.get("role"),
            "ownedLocationIds": [str(i) for i in u.get("ownedLocationIds", [])],
            "accessibleLocationIds": [str(i) for i in u.get("accessibleLocationIds", [])],
            "createdAt": iso(u.get("createdAt")),
        }


# ─────────────────────────── locations ───────────────────────────
class Locations:
    @staticmethod
    def _c():
        return database.collection("locations")

    @classmethod
    async def create(cls, name: str, admin_id: str):
        admin = to_oid(admin_id)
        res = await cls._c().insert_one({
            "name": name,
            "adminId": admin,
            "userIds": [admin],  # адмін є також користувачем
            "deviceIds": [],
            "createdAt": _now(),
        })
        return res.inserted_id

    @classmethod
    async def find_by_id(cls, location_id):
        oid = to_oid(location_id)
        return await cls._c().find_one({"_id": oid}) if oid else None

    @classmethod
    async def find_by_user_id(cls, user_id):
        return await cls._c().find({"userIds": to_oid(user_id)}).to_list(None)

    @classmethod
    async def update(cls, location_id, data: dict):
        await cls._c().update_one({"_id": to_oid(location_id)}, {"$set": data})

    @classmethod
    async def delete(cls, location_id):
        await cls._c().delete_one({"_id": to_oid(location_id)})

    @classmethod
    async def add_user(cls, location_id, user_id):
        await cls._c().update_one({"_id": to_oid(location_id)}, {"$addToSet": {"userIds": to_oid(user_id)}})

    @classmethod
    async def remove_user(cls, location_id, user_id):
        await cls._c().update_one({"_id": to_oid(location_id)}, {"$pull": {"userIds": to_oid(user_id)}})

    @classmethod
    async def add_device(cls, location_id, device_id: str):
        await cls._c().update_one({"_id": to_oid(location_id)}, {"$addToSet": {"deviceIds": device_id}})

    @classmethod
    async def remove_device(cls, location_id, device_id: str):
        await cls._c().update_one({"_id": to_oid(location_id)}, {"$pull": {"deviceIds": device_id}})

    @staticmethod
    def to_json(loc: dict) -> dict:
        return {
            "id": str(loc["_id"]),
            "name": loc.get("name"),
            "adminId": str(loc["adminId"]),
            "userIds": [str(i) for i in loc.get("userIds", [])],
            "deviceIds": loc.get("deviceIds", []),
            "createdAt": iso(loc.get("createdAt")),
        }


# ──────────────────────── sensor_readings ────────────────────────
class SensorReadings:
    """Одна запис на пристрій: зберігається лише останнє вимірювання (upsert)."""

    @staticmethod
    def _c():
        return database.collection("sensor_readings")

    @classmethod
    async def save(cls, device_id: str, t: dict):
        await cls._c().update_one(
            {"deviceId": device_id},
            {
                "$set": {
                    "temperature": t["temperature"],
                    "humidity": t["humidity"],
                    "gas": t["gas"],
                    "light": t["light"],
                    "sound": t["sound"],
                    "units": t["units"],
                    "timestamp": t["timestamp"],
                    "updatedAt": _now(),
                },
                "$setOnInsert": {"deviceId": device_id, "name": "", "hidden": False},
            },
            upsert=True,
        )

    @classmethod
    async def find_latest(cls, device_id: str):
        return await cls._c().find_one({"deviceId": device_id}, sort=[("timestamp", -1)])

    @classmethod
    async def update_metadata(cls, device_id: str, metadata: dict):
        await cls._c().update_one({"deviceId": device_id}, {"$set": {**metadata, "updatedAt": _now()}})

    @classmethod
    async def exists(cls, device_id: str) -> bool:
        return await cls._c().count_documents({"deviceId": device_id}, limit=1) > 0
