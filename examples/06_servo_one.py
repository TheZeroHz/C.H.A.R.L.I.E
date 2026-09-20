# examples/06_servo_one.py
# Lesson 6: one servo — see the pulse → angle mapping.
# Run: mpremote connect COMx run examples/06_servo_one.py
# WARNING: use external 5V for servos; common GND with ESP32.

from board import LEG_RB
from motion.servo import Servo
import time

s = Servo(LEG_RB)  # RB = GPIO 4 — change if you want another leg
print("sweeping pin", LEG_RB)

for angle in (0, 45, 90, 135, 180, 90):
    print("  ->", angle)
    s.move_to(angle, 400)
    time.sleep_ms(300)

s.detach()
print("detached")
