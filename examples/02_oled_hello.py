# examples/02_oled_hello.py
# Lesson 2: draw text with the raw SH1106 driver (no eyes yet).
# Run:  mpremote connect COMx run examples/02_oled_hello.py

from machine import Pin, I2C
from board import OLED_SDA, OLED_SCL, OLED_ADDR, OLED_WIDTH, OLED_HEIGHT
from display.sh1106 import SH1106_I2C

i2c = I2C(0, sda=Pin(OLED_SDA), scl=Pin(OLED_SCL), freq=400_000)
oled = SH1106_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, res=None, addr=OLED_ADDR)

oled.sleep(False)
oled.fill(0)                          # clear (0 = black)
oled.text("CHARLIE", 40, 20, 1)        # 1 = white pixels
oled.text("hello", 48, 36, 1)
oled.show()                            # push buffer to the glass
print("look at the OLED")
