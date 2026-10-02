from states.state import AbstractState

import time
import json
import lib.log as log
import uos

from states.connect_network import ConnectNetwork
from states.error import Error

from lib.constants import MEASUREMENT_FILE
from lib.helpers import to_iso8601
from lib.colors import Color


class Measurement(AbstractState):
    def exec(self):
        try:
            light = self.device.sensor_light.read_u16()
            gas = self.device.sensor_gas_ao.read_u16()
            sound = self.device.sensor_sound_ao.read_u16()
            self.device.sensor_dht11.measure()
            temperature = self.device.sensor_dht11.temperature()
            humidity = self.device.sensor_dht11.humidity()
            
            measurements = []
            measurements.append({"dt": to_iso8601(time.time()),  # rtc!
                                 "light": light,
                                 "gas": gas,
                                 "sound": sound,
                                 "temperature": temperature,
                                 "humidity": humidity})
            
            try:
                uos.stat(MEASUREMENT_FILE)
                with open(MEASUREMENT_FILE, 'r') as file:
                    try:
                        json_data = json.load(file)
                    except json.JSONDecodeError:
                        json_data = []
            except OSError:
                json_data = []
                
            json_data.append(measurements)
            
            with open(MEASUREMENT_FILE, 'w') as file:
                json.dump(json_data, file)
        
            log.info(">> Data was written to the file")
            self.device.light.set_color(Color.WHITE)
            self.device.change_state(ConnectNetwork(self.device, "Connect Network"))
            
        except Exception as e:
            log.error(f": Measurements error:  {e}")
            self.device.errcode = 3
            self.device.change_state(Error(self.device, "Error"))
