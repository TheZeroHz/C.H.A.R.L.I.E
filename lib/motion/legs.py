# lib/motion/legs.py
# CHARLIE dog — 4 legs, 1 servo each.
#
# Top view:
#   LF ---- RF
#   LB ---- RB
#
# Right-side shafts face outward → we MIRROR RF/RB
#   physical = 180 - logical
#
# Logical 90 = stand.  >90 back   <90 forward  (tune after horns)

from motion.servo import Servo
from board import LEG_LF, LEG_RF, LEG_LB, LEG_RB
import time

LF = 0
RF = 1
LB = 2
RB = 3
NAMES = ("LF", "RF", "LB", "RB")

FORWARD = 1
BACKWARD = -1
LEFT = 1
RIGHT = -1


class Legs:
    def __init__(self, pins=None, amp=25):
        # pins order must be LF, RF, LB, RB
        if pins is None:
            pins = (LEG_LF, LEG_RF, LEG_LB, LEG_RB)
        self.pins = pins
        self.amp = amp
        self.servos = [Servo(p) for p in pins]
        self.logical = [90, 90, 90, 90]
        self._resting = False

    def _to_physical(self, leg, logical):
        a = 0 if logical < 0 else 180 if logical > 180 else int(logical)
        if leg in (RF, RB):
            return 180 - a
        return a

    def attach(self):
        for s in self.servos:
            s.attach()
        self._resting = False

    def detach(self):
        for s in self.servos:
            s.detach()
        self._resting = True

    def set_rate_limit(self, deg_per_sec):
        for s in self.servos:
            s.set_rate_limit(deg_per_sec)

    def set_trims(self, lf=0, rf=0, lb=0, rb=0):
        for s, t in zip(self.servos, (lf, rf, lb, rb)):
            s.set_trim(t)

    def write_leg(self, leg, logical_angle):
        """Set one leg (logical degrees)."""
        if self._resting:
            self.attach()
        self.logical[leg] = int(logical_angle)
        self.servos[leg].write_immediate(self._to_physical(leg, logical_angle))

    def move(self, lf, rf, lb, rb, time_ms=400):
        """Soft-move all four legs to logical angles."""
        if self._resting:
            self.attach()
        targets = [lf, rf, lb, rb]
        phys = [self._to_physical(i, targets[i]) for i in range(4)]
        starts = [s.read() for s in self.servos]
        if time_ms < 20:
            for i, s in enumerate(self.servos):
                s.write_immediate(phys[i])
                self.logical[i] = targets[i]
            return
        steps = max(1, time_ms // 20)
        for step in range(1, steps + 1):
            for i, s in enumerate(self.servos):
                a = starts[i] + (phys[i] - starts[i]) * step // steps
                s.write_immediate(a)
            time.sleep_ms(20)
        self.logical = list(targets)

    def pose(self, lf, rf, lb, rb, time_ms=400):
        self.move(lf, rf, lb, rb, time_ms)

    # --- poses ---
    def stand(self, time_ms=500):
        self.pose(90, 90, 90, 90, time_ms)

    def sit(self, time_ms=600):
        self.pose(80, 80, 125, 125, time_ms)

    def lie(self, time_ms=700):
        self.pose(130, 130, 130, 130, time_ms)

    def bow(self, time_ms=500):
        self.pose(125, 125, 70, 70, time_ms)
        time.sleep_ms(250)
        self.stand(time_ms)

    def beg(self, time_ms=500):
        self.pose(55, 55, 120, 120, time_ms)

    def home(self, time_ms=500):
        self.stand(time_ms)
        self.detach()

    # --- gaits ---
    def crawl(self, steps=4, step_ms=350, direction=FORWARD):
        a = self.amp
        f = -a if direction == FORWARD else a
        b = a if direction == FORWARD else -a
        order = (LF, RF, LB, RB)
        for _ in range(steps):
            for leg in order:
                pose = [90, 90, 90, 90]
                pose[leg] = 90 + (f if leg in (LF, RF) else b)
                self.move(pose[0], pose[1], pose[2], pose[3], step_ms)
                self.stand(step_ms // 2)
        self.stand(300)

    def trot(self, steps=6, step_ms=280, direction=FORWARD):
        a = self.amp
        f = -a if direction == FORWARD else a
        b = a if direction == FORWARD else -a
        for _ in range(steps):
            self.move(90 + f, 90, 90, 90 + b, step_ms)  # LF+RB
            self.move(90, 90 + f, 90 + b, 90, step_ms)  # RF+LB
        self.stand(300)

    def walk(self, steps=4, step_ms=350, direction=FORWARD):
        self.crawl(steps, step_ms, direction)

    def turn(self, steps=4, step_ms=320, direction=LEFT):
        a = self.amp
        for _ in range(steps):
            if direction == LEFT:
                self.move(90 + a, 90 - a, 90 + a, 90 - a, step_ms)
                self.move(90 - a, 90 + a, 90 - a, 90 + a, step_ms)
            else:
                self.move(90 - a, 90 + a, 90 - a, 90 + a, step_ms)
                self.move(90 + a, 90 - a, 90 + a, 90 - a, step_ms)
        self.stand(300)

    def wag(self, cycles=6, step_ms=180):
        a = self.amp
        for _ in range(cycles):
            self.move(90 + a, 90 - a, 90 + a, 90 - a, step_ms)
            self.move(90 - a, 90 + a, 90 - a, 90 + a, step_ms)
        self.stand(250)

    def happy(self, cycles=5, step_ms=160):
        a = max(5, self.amp - 5)
        for _ in range(cycles):
            self.move(90 - a, 90 - a, 90 - a, 90 - a, step_ms)
            self.move(90 + a, 90 + a, 90 + a, 90 + a, step_ms)
        self.stand(250)

    def status(self):
        print("CHARLIE legs  LF%d RF%d" % (self.pins[LF], self.pins[RF]))
        print("              LB%d RB%d" % (self.pins[LB], self.pins[RB]))
        for i, name in enumerate(NAMES):
            print(
                "%s pin%d logical=%d phys=%d%s"
                % (
                    name,
                    self.pins[i],
                    self.logical[i],
                    self.servos[i].read(),
                    "" if self.servos[i].attached() else " (detached)",
                )
            )
