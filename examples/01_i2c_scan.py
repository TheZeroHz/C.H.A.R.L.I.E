# examples/01_i2c_scan.py
# Lesson 1: find chips on the I2C wires (SDA/SCL).
# Run:  mpremote connect COMx run examples/01_i2c_scan.py

from machine import Pin, I2C
from board import OLED_SDA, OLED_SCL

i2c = I2C(0, sda=Pin(OLED_SDA), scl=Pin(OLED_SCL), freq=400_000)
found = i2c.scan()

print("SDA=GPIO%d  SCL=GPIO%d" % (OLED_SDA, OLED_SCL))
print("devices:", [hex(a) for a in found])
# CHARLIE OLED should print:  ['0x3c']
