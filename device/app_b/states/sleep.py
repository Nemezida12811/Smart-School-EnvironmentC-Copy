from states.state import AbstractState

import lib.log as log
import ujson
import utime
import machine

from lib.helpers import wifi_disconnect, save_settings, remove_all, wakeup, save_system
from lib.models.settings_validator import Settings, ValidationError


class Sleep(AbstractState):
    def enter(self):
        super().enter()
        self.device.light.off()
        self.device.button.irq(trigger=machine.Pin.IRQ_FALLING, handler=wakeup)
    
    
    def exec(self):
        if self.device.mqtt_client:
            if self.device.wlan.isconnected():
                if self.device.mqtt_status:
                    self.device.mqtt_client.disconnect()
                    log.info(">> MQTT disconnect")
            
        wifi_disconnect(self.device)
        
        
        #----------
        error = False
        try:
            settings = Settings(self.device.config_update, self.device)
        except ValidationError as e:
            error = True
            log.error(f": Settings validation failed ({e})")
        except Exception as e:
            error = True
            log.error(f": Unexpected error in update settings ({e})")
            
        if not error:
            save_settings(self.device.config_update)
        
        
        #----------
        self.device.wdt.feed()
        state = None
        saves = False
        
        with open("/system.json") as f:
            state = ujson.load(f)
        
        active = state["active"]
        inactive = "b" if active == "a" else "a"
        stability_key = f"{active}_stability"
        inactive_stability_key = f"{inactive}_stability"
        
        if self.device.errcode == 2:
            if not state.get(stability_key):
                state[stability_key] = True
                saves = True
                log.info(">> New update is stable.")
                
                remove_all(f"/app_{inactive}")
                state[inactive_stability_key] = False
                
        elif not state.get(stability_key):
            state["rollback"] = True
            saves = True
            log.warning("! New update is NOT stable!")
            

        if saves:
            save_system(state)
        #----------
        
        sleep_time = self.device.config.get("measurement_interval")
        chunk = 5000

        start_ms = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), start_ms) < sleep_time:
            remaining = sleep_time - utime.ticks_diff(utime.ticks_ms(), start_ms)
            self.device.wdt.feed()
            machine.lightsleep(min(remaining, chunk))

        self.device.wdt.feed()
        machine.reset()