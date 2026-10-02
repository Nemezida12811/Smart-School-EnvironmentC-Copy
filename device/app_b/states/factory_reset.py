from states.state import AbstractState

import machine
import utime
import lib.log as log
import uos

from lib.constants import SETTINGS_FILE
from lib.helpers import set_checking


class FactoryReset(AbstractState): 
    def exec(self):
        try:
            uos.stat(SETTINGS_FILE)
            uos.remove(SETTINGS_FILE)
            log.warning("! Reset settings")
        except OSError:
            log.warning("! Settings file not exist")
        set_checking(True)

        
    def exit(self):
        super().exit()
        utime.sleep(2)
        self.device.light.off()
        utime.sleep(1)
        machine.reset()
