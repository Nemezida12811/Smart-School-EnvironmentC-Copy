import lib.log as log
import ujson

from lib.helpers import handle_settings_update
from lib.constants import DEFAULT_SETTINGS


class MQTTHandler:
    def __init__(self, device):
        self.device = device

    def callback(self, topic, message):
        try:
            data = message.decode('utf-8')
            topic_str = topic.decode('utf-8')
            payload = None
            try:
                payload = ujson.loads(data)
            except (ValueError, SyntaxError):
                log.warning(f"Received non-JSON message on topic {topic_str}")
                return
            
            if payload:
                log.info(f">> MQTT message received:\nTopic: {topic_str}\nMessage: {payload}")
                
                if "settings" in topic_str:
                    if handle_settings_update(payload, DEFAULT_SETTINGS):
                        self.device.config_update = payload
                elif "command" in topic_str:
                    print("Command")
                    pass
        except Exception as e:
            log.error(f": Error in mqtt callback ({e})")
