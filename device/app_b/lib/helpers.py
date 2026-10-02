# helpers.py
import os
import uos
import lib.log as log
import lib.uzipfile as uzipfile
import json
import time
import ujson
import utime
import socket
import ntptime

from machine import Pin
from lib.colors import Color 
from lib.constants import SETTINGS_FILE, TEMP_METRIC, TEMP_IMPERIAL, TEMP_STANDARD, BTN_PIN, LOG_FILE, VERSION_FILE, ACTIVE
from lib.models.settings_validator import Settings, ValidationError


def wait_point():
    button = Pin(BTN_PIN, Pin.IN, Pin.PULL_UP)
    log.info(f">> {ACTIVE} Click button to start")
    while button.value() == 1:
        utime.sleep(0.1)


def read_settings() -> dict:
    try:
        with open(SETTINGS_FILE, 'r') as file:
            return json.load(file)
    except OSError:
        log.error(": Settings file not found")
        
        
def read_log():
    try:
        uos.stat(LOG_FILE)
        with open(LOG_FILE, 'r') as f:
            content = f.read()
            return content
    except OSError:
        return "Log file is not found."
        

def read_version():
    try:
        with open(VERSION_FILE, "r") as f:
            content = f.read().strip()
            return int(content)
    except (OSError, ValueError):
        return 0

        
def save_settings(data):
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(data, file)
        

def save_system(state):
    try:
        with open("/system.json.tmp", "w") as f:
            ujson.dump(state, f)
        os.rename("/system.json.tmp", "/system.json")
    except Exception as e:
        log.error(f": Error system file save ({e})")
    log.debug("> System saved")

        
def get_wifi_data(config):
    error = False
    
    try:
        wifi_settings = config.get("wifi", {})
        ssid = wifi_settings.get("ssid")
        key = wifi_settings.get("password")
        ntp_host = config.get("ntp_host")
        
        if not ssid:  # ssid is None
            error = True
            log.error(": Invalid SSID for connecting to Wi-Fi")
        if not key:   # key is None
            error = True
            log.error(": Invalid password for connecting to Wi-Fi")
        if not ntp_host:
            error = True
            log.error(": Invalid NTP host")
            
        return ssid, key, ntp_host, error
            
    except Exception as e:
        error = True
        log.error("f: Error connecting to Wi-Fi({e}).")
        return ssid, key, ntp_host, error


def wifi_connector(device, ssid, key, attempts=20, use_blinker=True) -> bool:
    if not device.wlan.isconnected():
        log.info(">> Connecting to network...")
        if use_blinker:
            device.blinker.start(Color.WHITE, 500)
        device.wlan.connect(ssid, key)

        for counter in range(attempts):
            device.wdt.feed()
            utime.sleep(2)
            if device.wlan.isconnected():
                break
        
        device.wdt.feed()
        if use_blinker:
            device.blinker.stop()
            
        if device.wlan.isconnected():
            log.info(">> Successfully connected to the network!")
            return True
        else:
            log.error(": Failed to connect to the network. Ensure that the data for connecting to Wi-Fi is correct.")
            return False


def validate_host_address(host) -> bool:
    try:
        socket.getaddrinfo(host, 123)
        log.debug("> NTP host successfully passed verification")
        return True
    
    except OSError:
        log.error(": Invalid NTP host")
        return False


def to_iso8601(ts: int) -> str:
    dt = time.gmtime(ts)
    return f'{dt[0]:04}-{dt[1]:02}-{dt[2]:02}T{dt[3]:02}:{dt[4]:02}:{dt[5]:02}Z'


def ntp_setup(ntp_host) -> bool:
    try:
        ntptime.host = ntp_host
        ntptime.settime()
        log.info(f">> Time NTP: {to_iso8601(time.time())}")
        return True
        
    except Exception as e:
        log.error(f": Error in ntp setup ({e})")
        return False


def create_topiс(config, mode) -> str:  
    id = config.get("id")
    
    return f"iot/device/{id}/{mode}"


def handle_settings_update(data, inspector) -> bool:
    for key, val in inspector.items():
        if key not in data:
            return False

        if isinstance(val, dict):
            if not isinstance(data[key], dict):
                return False

            if not handle_settings_update(data[key], val):
                return False
    
    return True
     

def wakeup():
    print('Waking up!')


def wifi_disconnect(device):
    if device.wlan is not None:
        if device.wlan.isconnected():
            device.wlan.disconnect()
            log.info(">> Wi-Fi disconnect")
        device.wlan.active(False)
        log.info(">> Wi-Fi module off")


def remove_all(path):
    try:
        files = os.listdir(path)
    except OSError:
        return

    for file in files:
        full_path = path + "/" + file if path != "/" else "/" + file
        
        try:
            stat = os.stat(full_path)
            is_dir = stat[0] & 0x4000
            
            if is_dir:
                remove_all(full_path)
                os.rmdir(full_path)
            else:
                os.remove(full_path)
        except Exception as e:
            print("Error in delete", full_path, ":", e)
            return

def set_checking(mode: bool):
    state = None
    
    with open("/system.json") as f:
        state = ujson.load(f)
    
    active = state["active"]
    checking_key = f"{active}_checking"
    state[checking_key] = mode
    
    try:
        with open("/system.json.tmp", "w") as f:
            ujson.dump(state, f)
        os.rename("/system.json.tmp", "/system.json")
        log.debug("> Set checking")
    except Exception as e:
        log.error(f": Error system file save ({e})")


def setup_new_version(device):
    #----------
    device.wdt.feed()
    state = None
    saves = False
    
    with open("/system.json") as f:
        state = ujson.load(f)
    
    active = state["active"]
    inactive = "b" if active == "a" else "a"
    stability_key = f"{active}_stability"
    inactive_stability_key = f"{inactive}_stability"
    
    #----------
    device.wdt.feed()
    if state.get(stability_key):
        try:
            os.stat("/ota/update.zip")
            zip_exists = True
        except OSError:
            zip_exists = False
            
        if zip_exists:
            remove_all(f"/app_{inactive}")
            state[inactive_stability_key] = False
            
            log.debug("> Unpacking files...")
            device.wdt.feed()
            with uzipfile.ZipFile("/ota/update.zip", "r") as z:
                z.extractall(f"/app_{inactive}")
            device.wdt.feed()
            log.info("> Successful unzipping!")
            
            os.remove("/ota/update.zip")
            state["new"] = inactive
            log.debug("> NEW write")
            saves = True

    if saves:
        save_system(state)
    #----------
