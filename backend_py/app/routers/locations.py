from fastapi import APIRouter, Depends

from ..config import settings
from ..errors import ApiError, failing_as, ok
from ..mqtt_client import mqtt_client
from ..repositories import Locations, SensorReadings, Users
from ..schemas import AddDeviceBody, DeviceSettingsBody, NameBody, TargetUserBody
from ..security import current_user_id

router = APIRouter(prefix="/api/locations")


async def _get_location(location_id: str) -> dict:
    location = await Locations.find_by_id(location_id)
    if not location:
        raise ApiError(404, "Location not found")
    return location


def _require_admin(location: dict, user_id: str, message: str) -> None:
    if str(location["adminId"]) != user_id:
        raise ApiError(403, message)


def _require_device_in(location: dict, device_id: str) -> None:
    if device_id not in location.get("deviceIds", []):
        raise ApiError(400, "Device is not in this location")


@router.post("")
async def create_location(body: NameBody = NameBody(), user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        if not body.name:
            raise ApiError(400, "Name is required")
        if not await Users.find_by_id(user_id):
            raise ApiError(404, "Admin user not found")

        location_id = await Locations.create(body.name, user_id)
        await Users.add_owned_location(user_id, location_id)
        await Users.add_accessible_location(user_id, location_id)
        return ok({"id": str(location_id), "name": body.name, "adminId": user_id}, 201)


@router.get("")
async def get_locations(user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        created, joined = [], []
        for loc in await Locations.find_by_user_id(user_id):
            (created if str(loc["adminId"]) == user_id else joined).append(Locations.to_json(loc))
        return ok({"created": created, "joined": joined})


@router.get("/{location_id}")
async def get_location(location_id: str):
    # as in original — without authorization
    with failing_as("Internal server error"):
        return ok(Locations.to_json(await _get_location(location_id)))


@router.patch("/{location_id}")
async def update_location(location_id: str, body: NameBody = NameBody(), user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        if not body.name:
            raise ApiError(400, "Name is required")
        location = await _get_location(location_id)
        _require_admin(location, user_id, "Only admin can update location")
        await Locations.update(location_id, {"name": body.name})
        return ok({"message": "Location updated", "name": body.name})


@router.delete("/{location_id}")
async def delete_location(location_id: str, user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        location = await _get_location(location_id)
        _require_admin(location, user_id, "Only admin can delete location")

        await Locations.delete(location_id)
        await Users.remove_owned_location(location["adminId"], location_id)
        for uid in location.get("userIds", []):
            await Users.remove_accessible_location(uid, location_id)
        return ok({"message": "Location deleted"})


# ───────────── users ─────────────
@router.post("/{location_id}/users")
async def add_user(location_id: str, body: TargetUserBody = TargetUserBody(),
                   user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        target = body.targetUserId
        if not target:
            raise ApiError(400, "targetUserId is required")
        location = await _get_location(location_id)

        # WARNING: in Node-version admin check here was commented out
        # (any authorized user can add anyone). Behavior preserved.
        # _require_admin(location, user_id, "Only admin can add users")

        if not await Users.find_by_id(target):
            raise ApiError(404, "User to add not found")
        if any(str(i) == target for i in location.get("userIds", [])):
            raise ApiError(400, "User already in location")

        await Locations.add_user(location_id, target)
        await Users.add_accessible_location(target, location_id)
        return ok({"message": "User added to location"})


@router.delete("/{location_id}/users/{target_user_id}")
async def remove_user(location_id: str, target_user_id: str, user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        location = await _get_location(location_id)
        _require_admin(location, user_id, "Only admin can remove users")
        if target_user_id == str(location["adminId"]):
            raise ApiError(400, "Cannot remove admin from location")

        await Locations.remove_user(location_id, target_user_id)
        await Users.remove_accessible_location(target_user_id, location_id)
        return ok({"message": "User removed from location"})


# ───────────── devices ─────────────
@router.post("/{location_id}/devices")
async def add_device(location_id: str, body: AddDeviceBody = AddDeviceBody(),
                     user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        if not body.deviceId:
            raise ApiError(400, "deviceId is required")
        if not await SensorReadings.exists(body.deviceId):
            raise ApiError(404, "Device not found (no sensor data received yet)")
        location = await _get_location(location_id)
        _require_admin(location, user_id, "Only admin can add devices")

        await Locations.add_device(location_id, body.deviceId)
        if body.name:
            await SensorReadings.update_metadata(body.deviceId, {"name": body.name})
        return ok({"message": "Device added to location"})


@router.delete("/{location_id}/devices/{device_id}")
async def remove_device(location_id: str, device_id: str, user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        location = await _get_location(location_id)
        _require_admin(location, user_id, "Only admin can remove devices")
        await Locations.remove_device(location_id, device_id)
        return ok({"message": "Device removed from location"})


@router.patch("/{location_id}/devices/{device_id}/hide")
async def hide_device(location_id: str, device_id: str, user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        location = await _get_location(location_id)
        _require_admin(location, user_id, "Only admin can hide devices")
        _require_device_in(location, device_id)
        await SensorReadings.update_metadata(device_id, {"hidden": True})
        return ok({"message": "Device hidden"})


@router.patch("/{location_id}/devices/{device_id}/show")
async def show_device(location_id: str, device_id: str, user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        location = await _get_location(location_id)
        _require_admin(location, user_id, "Only admin can show devices")
        _require_device_in(location, device_id)
        await SensorReadings.update_metadata(device_id, {"hidden": False})
        return ok({"message": "Device revealed"})


@router.patch("/{location_id}/devices/{device_id}/settings")
async def update_device_settings(location_id: str, device_id: str,
                                 body: DeviceSettingsBody = DeviceSettingsBody(),
                                 user_id: str = Depends(current_user_id)):
    with failing_as("Internal server error"):
        location = await _get_location(location_id)
        _require_admin(location, user_id, "Only admin can update device settings")
        _require_device_in(location, device_id)

        if body.name:
            await SensorReadings.update_metadata(device_id, {"name": body.name})

        mqtt_settings = {
            "user": {"login": settings.device_admin_login, "password": settings.device_admin_password},
            "mqtt": {"server": body.brokerAddress or ""},
            "measurement_interval": body.interval or 10000,
            "wifi": {"ssid": body.wifiSsid or "", "password": body.wifiPassword or ""},
            "units": body.units or "standard",
            "ntp_host": body.ntpHost or "pool.ntp.org",
            "id": device_id,
        }
        topic = f"iot/backend/{device_id}/settings"
        mqtt_client.publish(topic, mqtt_settings, qos=1, retain=True)

        return ok({
            "message": "Device settings updated and published",
            "topic": topic,
            "settings": mqtt_settings,
        })
