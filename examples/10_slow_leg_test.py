# examples/10_slow_leg_test.py
# Slow angle test — one leg at a time (easy to watch / calibrate).
#
#   LF=7 ---- RF=6
#   LB=5 ---- RB=4
#
# Logical angles (right side mirrored in software):
#   90  = stand / neutral
#   0   = one extreme
#  180  = other extreme
#
# Run:
#   mpremote connect COMx run examples/10_slow_leg_test.py

from motion.legs import Legs, LF, RF, LB, RB
import time

# --- tune these ---
MOVE_MS = 1200          # soft move duration per angle (slow)
HOLD_MS = 800           # pause so you can see the horn
ANGLES = (90, 60, 90, 120, 90)   # gentle sweep around center
# For full range later, try: ANGLES = (90, 45, 90, 135, 90)
# --------------------------

LEG_ORDER = (
    (LF, "LF front-left  pin7"),
    (RF, "RF front-right pin6"),
    (LB, "LB back-left   pin5"),
    (RB, "RB back-right  pin4"),
)


def hold(ms=HOLD_MS):
    time.sleep_ms(ms)


dog = Legs()
dog.set_rate_limit(120)  # extra-soft
dog.status()

print("SLOW LEG TEST")
print("move_ms=%d  hold_ms=%d  angles=%s" % (MOVE_MS, HOLD_MS, ANGLES))
print("Press Ctrl+C to stop")
print("")

print("all → stand 90")
dog.stand(MOVE_MS)
hold(1000)

try:
    for leg, label in LEG_ORDER:
        print("==== %s ====" % label)
        # keep others at 90 while this leg moves
        for angle in ANGLES:
            pose = [90, 90, 90, 90]
            pose[leg] = angle
            print("  %s → %d°" % (label[:2], angle))
            dog.move(pose[0], pose[1], pose[2], pose[3], MOVE_MS)
            hold()
        print("  return stand")
        dog.stand(MOVE_MS)
        hold(500)
        print("")

    print("final stand + detach")
    dog.home(MOVE_MS)
    print("done")
except KeyboardInterrupt:
    print("stopped — standing")
    dog.stand(800)
    dog.detach()
