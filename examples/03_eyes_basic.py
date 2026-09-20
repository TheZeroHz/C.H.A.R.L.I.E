# examples/03_eyes_basic.py
# Lesson 3: RoboEyes on top of SH1106 — blink + look around.
# Run:  mpremote connect COMx run examples/03_eyes_basic.py

from machine import Pin, I2C
from board import OLED_SDA, OLED_SCL, OLED_ADDR, OLED_WIDTH, OLED_HEIGHT
from display.sh1106 import SH1106_I2C
from display.roboeyes import RoboEyes, ON

i2c = I2C(0, sda=Pin(OLED_SDA), scl=Pin(OLED_SCL), freq=400_000)
oled = SH1106_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, res=None, addr=OLED_ADDR)
oled.sleep(False)


def on_show(_):
    oled.show()


eyes = RoboEyes(oled, OLED_WIDTH, OLED_HEIGHT, frame_rate=50, on_show=on_show)
eyes.set_auto_blinker(ON, 3, 2)
eyes.set_idle_mode(ON, 2, 2)
eyes.open()

print("eyes running — Ctrl+C to stop")
while True:
    eyes.update()
