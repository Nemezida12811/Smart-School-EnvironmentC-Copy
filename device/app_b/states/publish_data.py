from states.state import AbstractState

import time
import json
import lib.log as log

from states.ota import OTA
from states.error import Error

from lib.constants import MEASUREMENT_FILE
from lib.helpers import create_topiс, to_iso8601
from lib.colors import Color


class PublishData(AbstractState):   
    def exec(self):
        self.device.light.set_color(Color.BROWN)
        topic = create_topiс(self.device.config, "telemetry")
        
        
        try:
            with open(MEASUREMENT_FILE, 'r') as f:
                content = json.load(f)
            
            if not content:
                log.info("No data to publish")
                self.device.change_state(OTA(self.device, "OTA"))
                return

            for item in content:
                measurement = item[0]
                
                payload = {
                    "timestamp": measurement.get('dt'),
                    "sensors": {
                        "temperature": {"value": measurement.get('temperature'), "units": self.device.config.get("units")},
                        "humidity": {"value": measurement.get('humidity'), "units": "%"},
                        "sound": {"value": measurement.get('sound'), "units": "dB"},
                        "gas": {"value": measurement.get('gas'), "units": "ppm"},
                        "light": {"value": measurement.get('light'), "units": "lx"}
                    }
                }
                
                self.device.mqtt_client.publish(topic, json.dumps(payload))
            
            
            with open(MEASUREMENT_FILE, 'w') as file:
                json.dump([], file)
            
            log.info(">> All data published and file cleared")
            self.device.change_state(OTA(self.device, "OTA"))

        except Exception as e:
            log.error(f": Publish error ({e})")
            self.device.change_state(Error(self.device, "Error"))
