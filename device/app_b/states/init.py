from states.state import AbstractState

import lib.log as log
import utime

from states.diagnostics import Diagnostics
from states.factory_reset import FactoryReset
from states.configuration import Configuration

from dht import DHT11
from lib.led import LedRGB
from lib.blink import Blink
from lib.colors import Color
import lib.ds3231_gen as dsmod
from lib.helpers import read_settings, setup_new_version
from machine import ADC, Pin, I2C
from lib.umqtt.simple import MQTTClient
from lib.models.settings_validator import Settings, ValidationError
from lib.helpers import set_checking

from lib.constants import BTN_PIN, BLUE_PIN, GREEN_PIN, RED_PIN, SHORT_PRESS_DURATION, LONG_PRESS_DURATION, LIGHT_SEN_PIN, DO_GAS_SEN_PIN, AO_GAS_SEN_PIN, AO_SOUND_SEN_PIN, DO_SOUND_SEN_PIN, DHT11_SEN_PIN, DEFAULT_SETTINGS


class Init(AbstractState):
    def exec(self):
        set_checking(False)
        setup_new_version(self.device)
        
        #init
        self.device.light = LedRGB(RED_PIN, GREEN_PIN, BLUE_PIN)
        self.device.blinker = Blink(self.device.light)
        self.device.light.set_color(Color.GREEN)
        
        self.device.button = Pin(BTN_PIN, Pin.IN, Pin.PULL_UP)
        
        self.device.sensor_light = ADC(Pin(LIGHT_SEN_PIN))
        
        self.device.sensor_gas_do = Pin(DO_GAS_SEN_PIN, Pin.IN)
        self.device.sensor_gas_ao = ADC(Pin(AO_GAS_SEN_PIN))
        
        self.device.sensor_sound_do = Pin(DO_SOUND_SEN_PIN, Pin.IN)
        self.device.sensor_sound_ao = ADC(Pin(AO_SOUND_SEN_PIN))
        
        self.device.sensor_dht11 = DHT11(Pin(DHT11_SEN_PIN))
        
#         self.device.rtc =
        
        self.device.config = read_settings()
        
        utime.sleep_ms(1000) 
        
        try:
            settings = Settings(self.device.config, self.device)
        except ValidationError as e:
            log.error(f": Settings validation failed ({e})")
            self.device.light.set_color(Color.CYAN)
            self.device.config = DEFAULT_SETTINGS
            self.device.change_state(Configuration(self.device, "Configuration"))
            return
        except Exception as e:
            log.error(f": Unexpected error in init ({e})")
            self.device.light.set_color(Color.CYAN)
            self.device.config = DEFAULT_SETTINGS
            self.device.change_state(Configuration(self.device, "Configuration"))
            return
        
        device_id = self.device.config.get("id")
        mqtt_config = self.device.config.get("mqtt")
        mqtt_server = mqtt_config.get("server")
                
        self.device.mqtt_client = MQTTClient(device_id, server=mqtt_server)
        
        
        #button timer
        short_press = False
        long_press = False
        
        if not self.device.button.value():
            start_time = utime.ticks_ms()
            self.device.blinker.start(Color.GREEN, 250)
            
            while not self.device.button.value():
                holding_time = utime.ticks_ms() - start_time
                
                if not short_press and holding_time >= SHORT_PRESS_DURATION and holding_time < LONG_PRESS_DURATION:
                    short_press = True
                    self.device.blinker.start(Color.CYAN, 250)
                
                if not long_press and holding_time >= LONG_PRESS_DURATION:
                    short_press = False
                    long_press = True
                    self.device.blinker.start(Color.ORANGE, 250)
                    break
                    
                utime.sleep_ms(100)
                
            self.device.blinker.stop()  


        #checks
        if long_press:
            self.device.light.set_color(Color.ORANGE)
            self.device.change_state(FactoryReset(self.device, "Factory Reset"))
        elif short_press:
            self.device.light.set_color(Color.CYAN)
            self.device.change_state(Configuration(self.device, "Configuration"))
        else:
            self.device.change_state(Diagnostics(self.device, "Diagnostics"))
    