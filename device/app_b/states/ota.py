from states.state import AbstractState

import lib.log as log
import urequests
import time

from states.sleep import Sleep
from states.error import Error

from lib.constants import VERSION_URL, GIT_HEADERS, VERSION_FILE
from lib.helpers import read_version
from lib.colors import Color


class OTA(AbstractState):
    def exec(self):
        self.device.light.set_color(Color.GOLD)
        error = False
#         id = self.device.config.get("id")
#         
#         topic_settings = f"iot/backend/{id}/settings"
#         topic_command = f"iot/backend/{id}/command"
#         
#         self.device.mqtt_client.subscribe(topic_settings)
#         log.debug("> Subscribed to settings")
#         self.device.mqtt_client.subscribe(topic_command)
#         log.debug("> Subscribed to command")
#         
#         
#         try:
#             self.device.wdt.feed()
#             self.device.mqtt_client.check_msg()
#             self.device.wdt.feed()
#         except Exception as e:
#             log.error(f": Error checking messages ({e})")
#             error = True
#         
#         
#         self.device.wdt.feed()
#         self.device.mqtt_client.unsubscribe(topic_settings)
#         log.debug("> Unsubscribed from settings")
#         self.device.mqtt_client.unsubscribe(topic_command)
#         log.debug("> Unsbscribed from command")
        
        
        self.device.wdt.feed()
        try:
            r = urequests.get(VERSION_URL, headers=GIT_HEADERS)
            if r.status_code != 200:
                response_text = r.text
                r.close()
                log.warning(f"Response body: {response_text}")
                raise Exception(f"Server returned {r.status_code}")
            
            data = r.json()
            r.close()
            
            latest_version = data['version']
            firmware_url = data['firmware_url']

            if latest_version > read_version():
                log.info(f">> Update to v.{latest_version} found!")
                
                log.info(">> Download...")
                updates = urequests.get(firmware_url, headers=GIT_HEADERS, stream=True)
                if updates.status_code == 200:
                    with open("/ota/update.zip", "wb") as f:
                        downloaded = 0
                        while True:
                            chunk = updates.raw.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                        log.info(f">> Downloaded {downloaded} bytes")
                        
                        f.flush()
                        try:
                            os.sync()
                        except:
                            pass
                        
                        import os
                        actual_size = os.stat("/ota/update.zip")[6]
                        log.info(f">> Saved to disk: {actual_size} bytes")
                    
                    updates.close()
                    log.info(">> Done!")
                    time.sleep(2)
                else:
                    errmsg = f"Download failed: {updates.status_code}"
                    updates.close()
                    raise Exception(errmsg)
            else:
                log.debug("> No update required")

        except Exception as e:
            error = True
            log.warning(f"! Error update ({e})")
        

        if error:
            self.device.errcode = 9
            self.device.change_state(Error(self.device, "Error"))
        else:
            self.device.change_state(Sleep(self.device, "Sleep"))
        