from states.state import AbstractState

from states.init import Init

from machine import WDT


class Device:
    def __init__(self):
        self.state: AbstractState = Init(self, "Init")
        self.wdt = WDT(timeout=8 * 1000)
        self.mqtt_client = None
        self.mqtt_status = False
        self.errcode = 2
        self.blinker = None
        self.config: dict = None
        self.config_update: dict = None
        self.sensor_light = None
        self.sensor_gas_do = None
        self.sensor_gas_ao = None
        self.sensor_sound_do = None
        self.sensor_sound_ao = None
        self.sensor_dht11 = None
        self.rtc = None
        self.wlan = None
        self.button = None
        self.light = None
    
    
    def change_state(self, state: AbstractState):
        if state is not None:
            self.state = state
    
    
    def run(self):
        while True:
            state_sosud = self.state
            state_sosud.enter()
            state_sosud.exec()
            state_sosud.exit()
