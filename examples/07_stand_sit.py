# examples/07_stand_sit.py
# Lesson 7: four legs — stand and sit (logical angles + right-side mirror).
# Run: mpremote connect COMx run examples/07_stand_sit.py

from motion.legs import Legs
import time

dog = Legs()
dog.status()

print("stand")
dog.stand()
time.sleep_ms(800)

print("sit")
dog.sit()
time.sleep_ms(800)

print("stand + home (detach)")
dog.home()
print("done")
