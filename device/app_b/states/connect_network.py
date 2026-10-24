from states.state import AbstractState

import machine
import network
import ujson
import lib.log as log

from states.error import Error
from states.publish_data import PublishData

from lib.helpers import get_wifi_data, wifi_connector, validate_host_address, ntp_setup, create_topiс
from lib.constants import CPU_FREQ_HIGH
from lib.mqtt_handler import MQTTHandler


class ConnectNetwork(AbstractState):
    def enter(self):
        super().enter()
        machine.freq(CPU_FREQ_HIGH)
        self.device.wlan = network.WLAN(network.STA_IF)
        self.device.wlan.active(True)
    
    
    def exec(self):
        ssid, key, ntp_host, error = get_wifi_data(self.device.config)
        
        if error:
            self.device.errcode = 4  # TODO: maybe better to have separate error code for each state
            self.device.change_state(Error(self.device, "Error"))
            return
        
        if not wifi_connector(self.device, ssid, key):
            self.device.errcode = 5
            self.device.change_state(Error(self.device, "Error"))
            return
                
        log.info(f">> Network config: {self.device.wlan.ipconfig('addr4')}")
        
        if not validate_host_address(ntp_host):
            self.device.errcode = 6
            self.device.change_state(Error(self.device, "Error"))
            return
        
        if not ntp_setup(ntp_host):
            self.device.errcode = 7
            self.device.change_state(Error(self.device, "Error"))
            return
        
        
        self.device.wdt.feed()
        topic = create_topiс(self.device.config, "status")
        
        last_will_msg = ujson.dumps({"status": "offline"})
        self.device.mqtt_client.set_last_will(topic=topic, msg=last_will_msg, retain=True)
        log.debug("> Set last will for mqtt")
        
        handler = MQTTHandler(self.device)
        self.device.mqtt_client.set_callback(handler.callback)
        log.debug("> Set callback for mqtt")
        
        try:
            self.device.mqtt_client.connect()
            self.device.mqtt_status = True
        except Exception as e:
            self.device.errcode = 8
            log.error(f": Error mqtt client connection ({e})")
            self.device.mqtt_status = False
            self.device.change_state(Error(self.device, "Error"))
            return
        log.debug(">> Successful mqtt connection")
        
        my_msg_online = {"status": "online"}

        try:
            self.device.mqtt_client.publish(topic, ujson.dumps(my_msg_online), retain=True)
        except Exception as e:
            self.device.errcode = 8
            log.error(f": Online status pablish error ({e})")
            self.device.change_state(Error(self.device, "Error"))
            return
        log.debug(">> Online status successfully published")
        
        self.device.change_state(PublishData(self.device, "Publish Data"))
        