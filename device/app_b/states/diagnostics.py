from states.state import AbstractState

import lib.log as log
import utime

from states.measurement import Measurement
from states.error import Error

from lib.colors import Color


class Diagnostics(AbstractState):
    def exec(self):
        errors = False
        self.device.blinker.start(Color.MAGENTA, 1000)
        log.info(">> The sensors are warming up...")
        for i in range(3):
            self.device.wdt.feed()
            utime.sleep(5)
            
        self.device.blinker.stop()
        self.device.wdt.feed()
        
        try:
            light = self.device.sensor_light.read_u16()
            if not (10 <= light <= 65525):
                log.error(f": LDR light out of range ({light})")
                errors = True
            else:
                log.info(">> LDR passed diagnostics successfully.")
        except Exception as e:
            log.critical(f": LDR measure error: {str(e)}!")
            errors = True
        
        
        try:
            gas = self.device.sensor_gas_ao.read_u16()
            if not (300 <= gas <= 65200):
                log.error(f": MQ-5 gas out of range ({gas})")
                errors = True
            else:
                log.info(">> MQ-5 passed diagnostics successfully.")
        except Exception as e:
            log.critical(f": MQ-5 measure error: {str(e)}!")
            errors = True
        
        
        try:
            sound = self.device.sensor_sound_ao.read_u16()
            if not (300 <= sound <= 65200):
                log.error(f": KY-037 sound out of range ({sound})")
                errors = True
            else:
                log.info(">> KY-037 passed diagnostics successfully.")
        except Exception as e:
            log.critical(f": KY-037 measure error: {str(e)}!")
            errors = True
            
        
        try:
            self.device.sensor_dht11.measure()
            temperature = self.device.sensor_dht11.temperature()
            humidity = self.device.sensor_dht11.humidity()
            
            if not (-20 <= temperature <= 60):
                log.error(f": DHT11 temperature out of range ({temperature}C)")
                errors = True
            else:
                log.info(">> DHT11 temperature passed diagnostics successfully.")
            if not (5 <= humidity <= 99):
                log.error(f": DHT11 humidity out of range ({humidity}%)")
                errors = True
            else:
                log.info(">> DHT11 humidity passed diagnostics successfully.")
        except Exception as e:
            log.critical(f": DHT11 measure error: {str(e)}!")
            errors = True
        
        
        if errors:
            self.device.errcode = 8
            self.device.change_state(Error(self.device, "Error"))
        else:
            self.device.light.set_color(Color.BLUE)
            log.info(">> The device has successfully passed diagnostics.")
            self.device.change_state(Measurement(self.device, "Measurement"))
