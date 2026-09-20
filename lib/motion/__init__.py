# lib/motion/ — servos / legs (low level)
#
#   from motion.servo import Servo          # one motor
#   from motion.legs import Legs, LF, RF    # four-leg dog
#
# Files:
#   servo.py  — PWM pulse → angle (one pin)
#   legs.py   — LF/RF/LB/RB + mirror + soft poses/gaits

from motion.servo import Servo
from motion.legs import Legs, LF, RF, LB, RB, FORWARD, BACKWARD, LEFT, RIGHT

__all__ = [
    "Servo",
    "Legs",
    "LF",
    "RF",
    "LB",
    "RB",
    "FORWARD",
    "BACKWARD",
    "LEFT",
    "RIGHT",
]
