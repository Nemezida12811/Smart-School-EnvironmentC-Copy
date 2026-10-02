from states.state import AbstractState

import network
import utime
import machine
import lib.log as log

from states.commissioning import Commissioning

from lib.constants import SSID, PASSWORD, CPU_FREQ_HIGH
from web.server import start_webserver
from lib.colors import Color


class Configuration(AbstractState):
    def enter(self):
        super().enter()
        machine.freq(CPU_FREQ_HIGH)
        self.device.wlan = network.WLAN(network.AP_IF)
        self.device.wlan.active(True)
    
    
    def exec(self):
        self.device.wlan.config(essid=SSID, password=PASSWORD)

        log.info(f">> AP IP: {self.device.wlan.ifconfig()[0]}")
        
        self.device.blinker.start(Color.CYAN)
        for counter in range(1, 15 + 1):
            self.device.wdt.feed()
            clients = self.device.wlan.status('stations')
            log.info(f">> Clients: {clients}")
            if clients:
                break
            utime.sleep(3)
        else:
            log.error(": The clients waiting time has expired")
            #-------------------------
            self.device.wlan.active(False)
            utime.sleep_ms(5000)
            machine.reset()
            #-------------------------
        self.device.blinker.stop()
        
        try:
            start_webserver(self.device)
        except Exception:
            self.device.wlan.active(False)
            log.error(": Error with start webserver")
            #-------------------------
            self.device.wlan.active(False)
            utime.sleep_ms(5000)
            machine.reset()
            #-------------------------

        self.device.wlan.active(False)
        
        self.device.change_state(Commissioning(self.device, "Commissioning"))
