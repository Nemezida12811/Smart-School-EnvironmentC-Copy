from typing import Any

from pydantic import BaseModel, ConfigDict


class _Body(BaseModel):
    # усі поля необов'язкові: перевірку робимо вручну, щоб повертати ті самі 400-повідомлення
    model_config = ConfigDict(extra="ignore")


class RegisterBody(_Body):
    username: str | None = None
    email: str | None = None
    password: str | None = None


class LoginBody(_Body):
    email: str | None = None
    password: str | None = None


class NameBody(_Body):
    name: str | None = None


class TargetUserBody(_Body):
    targetUserId: str | None = None


class AddDeviceBody(_Body):
    deviceId: str | None = None
    name: str | None = None


class DeviceSettingsBody(_Body):
    name: str | None = None
    units: str | None = None
    ntpHost: str | None = None
    brokerAddress: str | None = None
    wifiSsid: str | None = None
    wifiPassword: str | None = None
    interval: Any = None
