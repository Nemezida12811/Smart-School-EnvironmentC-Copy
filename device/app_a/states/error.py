from states.state import AbstractState

import utime

from states.sleep import Sleep

from lib.colors import Color


class Error(AbstractState):   
    def exec(self):
        self.device.light.off()
        utime.sleep(0.5)
        
        self.device.blinker.start(Color.RED, 500)
        for i in range(self.device.errcode):
            self.device.wdt.feed()
            utime.sleep(1)
        self.device.blinker.stop()
        
        utime.sleep(0.5)
        self.device.change_state(Sleep(self.device, "Sleep"))
        