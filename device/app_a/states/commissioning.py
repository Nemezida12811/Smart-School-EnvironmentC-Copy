from states.state import AbstractState

import lib.log as log
import utime
import machine

from lib.models.settings_validator import Settings, ValidationError
from lib.helpers import set_checking
from lib.colors import Color


class Commissioning(AbstractState):
    def exec(self):
        from states.configuration import Configuration
        
        try:
            settings = Settings(self.device.config, self.device)
        except ValidationError as e:
            log.error(f": Settings validation failed ({e})")
            self.device.change_state(Configuration(self.device, "Configuration"))
            self.device.blinker.start(Color.CYAN, 100)
            utime.sleep(2)
            self.device.blinker.stop()
            return
        except Exception as e:
            log.error(f": Unexpected error in commissioning ({e})")
            self.device.change_state(Configuration(self.device, "Configuration"))
            self.device.blinker.start(Color.CYAN, 100)
            utime.sleep(2)
            self.device.blinker.stop()
            return
        
        utime.sleep_ms(5000)
        set_checking(True)
        machine.reset()
        