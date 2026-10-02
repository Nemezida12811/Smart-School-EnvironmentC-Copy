import json
import utime
import network
import machine

from lib.umqtt.simple import MQTTClient
from lib.constants import ID, CPU_FREQ_HIGH


class ValidationError(Exception):
    pass

class Settings:
    def __init__(self, data: dict, device):
        self.device = device
        self.validate(data)
        
        self.user = data['user']
        self.mqtt = data['mqtt']
        self.measurement_interval = data['measurement_interval']
        self.wifi = data['wifi']
        self.units = data['units']
        self.ntp_host = data['ntp_host']
        self.id = data['id']


    def validate(self, data):
        from lib.helpers import wifi_connector, validate_host_address, wifi_disconnect
        
        back_freq = machine.freq()
        machine.freq(CPU_FREQ_HIGH)
        
        required_keys = {
            "user": dict, 
            "mqtt": dict, 
            "measurement_interval": int, 
            "wifi": dict, 
            "units": str, 
            "ntp_host": str, 
            "id": str
        }
        
        try:
            for key, expected_type in required_keys.items():
                if key not in data:
                    raise ValidationError(f"Missing key: {key}")
                if not isinstance(data[key], expected_type):
                    raise ValidationError(f"Invalid type for {key}: expected {expected_type.__name__}")
                
            #mqtt
            if 'server' not in data['mqtt']:
                raise ValidationError("MQTT config must contain server address")
            #-------
            
            #other
            if data['measurement_interval'] < 1000:
                raise ValidationError("Measurement interval too short (min 1000ms)")
                
            allowed_units = ["standard", "metric", "imperial"]
            if data['units'] not in allowed_units:
                raise ValidationError(f"Invalid units. Allowed: {allowed_units}")

            if data['id'] != ID:
                raise ValidationError("Invalid device ID")
            #-------
            
            #user
            user_data = data['user']
            for field in ('login', 'password'):
                if field not in user_data:
                    raise ValidationError("User config must contain login and password")
                
                value = user_data[field]
                if not isinstance(value, str) or not value.strip():
                    raise ValidationError(f"User {field} cannot be empty")
            #-------
            
            #wifi
            if not all(i in data['wifi'] for i in ('ssid', 'password')):
                raise ValidationError("Wi-Fi config must contain ssid and password")
            
            error = False
            self.device.wlan = network.WLAN(network.STA_IF)
            self.device.wlan.active(True)
            
            wifi_data = data['wifi']
            if not wifi_connector(self.device, wifi_data['ssid'], wifi_data['password'], 15, False):
                error = True
            
            if error:
                wifi_disconnect(self.device)
                raise ValidationError("Incorrect Wi-Fi connection data")
            #-------
            
            self.device.wdt.feed()
            
            #ntp host
            if not validate_host_address(data['ntp_host']):
                wifi_disconnect(self.device)
                raise ValidationError("Unsuitable NTP host")
            wifi_disconnect(self.device)
            #-------
        finally:
            machine.freq(back_freq)


    def to_json(self):
        return json.dumps(self.__dict__)
