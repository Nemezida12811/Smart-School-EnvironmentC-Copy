import machine, ubinascii, ujson

#pin config
BTN_PIN = 0
BLUE_PIN  = 6
GREEN_PIN = 8
RED_PIN = 9
LIGHT_SEN_PIN = 26
DO_GAS_SEN_PIN = 1
AO_GAS_SEN_PIN = 27
AO_SOUND_SEN_PIN = 28
DO_SOUND_SEN_PIN = 15
DHT11_SEN_PIN = 2

DS3231_ADDR = 0x68

#press time
SHORT_PRESS_DURATION = 3000
LONG_PRESS_DURATION = 6000

#units
TEMP_METRIC = 'metric'
TEMP_IMPERIAL = 'imperial'
TEMP_STANDARD = 'standard'

#access point
SSID = "Inspector-comforT"
PASSWORD = "NADteam100"

#device id
ID = f"com-{ubinascii.hexlify(machine.unique_id()).decode()}-fort"

#version
state = None
with open("/system.json") as f:
    state = ujson.load(f)

ACTIVE = state["active"]

VERSION_FILE = f"/app_{ACTIVE}/~version.txt"

#settings config
SETTINGS_FILE = f"/app_{ACTIVE}/~settings.json"
MEASUREMENT_FILE = f"/app_{ACTIVE}/~measurement.json"
DEFAULT_SETTINGS = {
    "user": {
        "login": "",
        "password": "",
    },
    "units": TEMP_STANDARD,
    "wifi": {
        "ssid": "",
        "password": "",   
    },
    "ntp_host": "pool.ntp.org",
    "mqtt": {
        "server": "broker.hivemq.com",
    },
    "id": ID,
    "measurement_interval" : 50000
}

#log
LOG_FILE = f"/app_{ACTIVE}/~log.txt"

#freq
CPU_FREQ_LOW = 70_000_000
CPU_FREQ_HIGH = 125_000_000

#git
PROJECT_ID = "77921201"
ACCESS_TOKEN = "glpat-oPwIxnXQKyW8mxGRP34QjG86MQp1OmpyYzV3Cw.01.121nei4qh"
GIT_URL = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/packages/generic/ota_comfort"
VERSION_URL = f"{GIT_URL}/latest/version.json"
GIT_HEADERS = {
    "PRIVATE-TOKEN": ACCESS_TOKEN,
    "User-Agent": "Updater" 
}
