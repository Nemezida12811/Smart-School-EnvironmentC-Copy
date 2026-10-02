from machine import Pin, PWM

class LedRGB:
    def __init__(self, r_pin, g_pin, b_pin, freq=1000):
        self.red = PWM(Pin(r_pin))
        self.green = PWM(Pin(g_pin))
        self.blue = PWM(Pin(b_pin))

        for pin in (self.red, self.green, self.blue):
            pin.freq(freq)

    def set_color(self, color):
        r, g, b = color
        self.red.duty_u16(r * 257)
        self.green.duty_u16(g * 257)
        self.blue.duty_u16(b * 257)

    def off(self):
        self.set_color((0, 0, 0))

