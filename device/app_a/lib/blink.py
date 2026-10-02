from machine import Timer

class Blink:
    def __init__(self, light):
        self.light = light
        self.timer = Timer(-1)
        self.current_color = None
        self.current_state = False

    def start(self, color, interval_ms=500):
        self.stop()
        
        self.current_color = color
        self.current_state = False
        
        self.light.set_color(self.current_color)
        
        self.timer.init(period=interval_ms, mode=Timer.PERIODIC, callback=self.tick)

    def stop(self):
        self.timer.deinit()

    def tick(self, t):
        if self.current_state:
            self.light.set_color(self.current_color)
        else:
            self.light.off()
        self.current_state = not self.current_state
        