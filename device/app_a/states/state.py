import lib.log as log

class AbstractState:
    def __init__(self, device, name):
        self.device = device
        self.name = name
        
    def enter(self):
        log.debug(f"> |={self.name} State...")
        self.device.wdt.feed()
        
    def exec(self):
        pass
        
        
    def exit(self):
        log.debug(f"> =|Exit from {self.name} state...")