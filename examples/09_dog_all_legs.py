# examples/09_dog_all_legs.py
# Control ALL 4 dog servos (LF, RF, LB, RB).
#
#   LF=7 ---- RF=6
#   LB=5 ---- RB=4
#
# Run:
#   mpremote connect COMx run examples/09_dog_all_legs.py
#
# Power: 5V for servos + common GND with ESP32.

from motion.legs import Legs, LF, RF, LB, RB
import time


def pause(ms=600):
    time.sleep_ms(ms)


dog = Legs()
dog.status()
print("--- all 4 legs demo ---")

# 1) Neutral stand (all four at logical 90°)
print("1) stand")
dog.stand(500)
pause()

# 2) Move each leg alone so you can see which horn is which
print("2) each leg forward then back")
for leg, name in ((LF, "LF"), (RF, "RF"), (LB, "LB"), (RB, "RB")):
    print("   ", name, "forward")
    pose = [90, 90, 90, 90]
    pose[leg] = 60
    dog.move(pose[0], pose[1], pose[2], pose[3], 350)
    pause(400)
    print("   ", name, "back")
    pose[leg] = 120
    dog.move(pose[0], pose[1], pose[2], pose[3], 350)
    pause(400)
    dog.stand(250)

# 3) All four together — same logical angle
print("3) all four → 70°, then 110°, then stand")
dog.move(70, 70, 70, 70, 400)
pause()
dog.move(110, 110, 110, 110, 400)
pause()
dog.stand(400)

# 4) Poses that use all four
print("4) sit")
dog.sit(600)
pause(800)
print("   stand")
dog.stand(500)
pause(400)

print("5) bow")
dog.bow(500)
pause(400)

print("6) wag (all four sway)")
dog.wag(cycles=5, step_ms=160)

print("7) trot (diagonal pairs)")
dog.trot(steps=4, step_ms=280)

print("8) home + detach (saves hold current)")
dog.home(500)
print("done — good boy")
