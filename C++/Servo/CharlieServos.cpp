#include "CharlieServos.h"

static const char *const LEG_NAME[CharlieServos::COUNT] = {
    "LF", "RF", "LB", "RB"};

void CharlieServos::begin(const int pins[COUNT]) {
  for (int i = 0; i < COUNT; i++) {
    _pins[i] = pins[i];
  }

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  enableServoLimit(SERVO_LIMIT_DEFAULT);
  attachServos();
  _resting = false;
  stand(500);
}

void CharlieServos::attachServos() {
  // Attach ascending GPIO order (4→5→6→7). On ESP32-S3, later LEDC
  // channels from ESP32Servo often fail — give RB/pin4 the first channel.
  static const int order[COUNT] = {RB, LB, RF, LF};  // pins 4,5,6,7
  for (int i = 0; i < COUNT; i++) {
    const int leg = order[i];
    const int ch = _servo[leg].attach(_pins[leg]);
    if (ch < 0) {
      Serial.print("ATTACH FAIL leg=");
      Serial.print(LEG_NAME[leg]);
      Serial.print(" pin=");
      Serial.println(_pins[leg]);
    }
  }
}

void CharlieServos::detachServos() {
  for (int i = 0; i < COUNT; i++) {
    _servo[i].detach();
  }
}

bool CharlieServos::attached() const {
  for (int i = 0; i < COUNT; i++) {
    if (_servo[i].attached()) return true;
  }
  return false;
}

void CharlieServos::setTrims(int lf, int rf, int lb, int rb) {
  _servo[LF].SetTrim(lf);
  _servo[RF].SetTrim(rf);
  _servo[LB].SetTrim(lb);
  _servo[RB].SetTrim(rb);
}

void CharlieServos::enableServoLimit(int degPerSec) {
  for (int i = 0; i < COUNT; i++) {
    _servo[i].SetLimiter(degPerSec);
  }
}

void CharlieServos::disableServoLimit() {
  for (int i = 0; i < COUNT; i++) {
    _servo[i].DisableLimiter();
  }
}

// Right legs mirrored: same logical "forward" → opposite PWM
int CharlieServos::toPhysical(int leg, int logical) const {
  if (logical < 0) logical = 0;
  if (logical > 180) logical = 180;
  if (leg == RF || leg == RB) {
    return 180 - logical;
  }
  return logical;
}

int CharlieServos::fromPhysical(int leg, int physical) const {
  if (leg == RF || leg == RB) {
    return 180 - physical;
  }
  return physical;
}

void CharlieServos::writePhysical(int leg, int physical) {
  if (physical < 0) physical = 0;
  if (physical > 180) physical = 180;
  _servo[leg].SetPosition(physical);
  _logical[leg] = fromPhysical(leg, physical);
}

void CharlieServos::wakeFromRest() {
  attachServos();
  _resting = false;
}

void CharlieServos::setLeg(int leg, int logicalAngle) {
  if (leg < 0 || leg >= COUNT) return;
  wakeFromRest();
  _logical[leg] = constrain(logicalAngle, 0, 180);
  writePhysical(leg, toPhysical(leg, _logical[leg]));
}

void CharlieServos::moveServos(int timeMs, const int logical[COUNT]) {
  wakeFromRest();

  int targetsPhys[COUNT];
  for (int i = 0; i < COUNT; i++) {
    _logical[i] = constrain(logical[i], 0, 180);
    targetsPhys[i] = toPhysical(i, _logical[i]);
  }

  const unsigned long finalTime = millis() + (unsigned long)max(timeMs, 1);
  float increment[COUNT];

  if (timeMs > 10) {
    for (int i = 0; i < COUNT; i++) {
      increment[i] =
          (targetsPhys[i] - _servo[i].getPosition()) / (timeMs / 10.0f);
    }
    for (; millis() < finalTime;) {
      const unsigned long sliceEnd = millis() + 10;
      for (int i = 0; i < COUNT; i++) {
        _servo[i].SetPosition(
            (int)(_servo[i].getPosition() + increment[i]));
      }
      while (millis() < sliceEnd) {
      }
    }
  } else {
    for (int i = 0; i < COUNT; i++) {
      _servo[i].SetPosition(targetsPhys[i]);
    }
    while (millis() < finalTime) {
    }
  }

  bool moving = true;
  while (moving) {
    moving = false;
    for (int i = 0; i < COUNT; i++) {
      if (_servo[i].getPosition() != targetsPhys[i]) {
        moving = true;
        break;
      }
    }
    if (moving) {
      for (int i = 0; i < COUNT; i++) {
        _servo[i].SetPosition(targetsPhys[i]);
      }
      const unsigned long sliceEnd = millis() + 10;
      while (millis() < sliceEnd) {
      }
    }
  }
}

void CharlieServos::moveSingle(int leg, int logicalAngle, int timeMs) {
  int t[COUNT] = {_logical[LF], _logical[RF], _logical[LB], _logical[RB]};
  if (leg >= 0 && leg < COUNT) {
    t[leg] = logicalAngle;
  }
  moveServos(timeMs, t);
}

void CharlieServos::pose(int timeMs, int lf, int rf, int lb, int rb) {
  const int t[COUNT] = {lf, rf, lb, rb};
  moveServos(timeMs, t);
}

void CharlieServos::stepPose(int timeMs, int lf, int rf, int lb, int rb) {
  pose(timeMs, lf, rf, lb, rb);
}

void CharlieServos::home(int timeMs) {
  if (_resting) return;
  stand(timeMs);
  detachServos();
  _resting = true;
}

// ---- Poses ----------------------------------------------------
// Convention (logical): 90 = stand
//   >90 = swing "back"   <90 = swing "forward"
// Tune _amp / these numbers after horns are centered at 90.

void CharlieServos::stand(int timeMs) {
  pose(timeMs, 90, 90, 90, 90);
}

void CharlieServos::sit(int timeMs) {
  // Rear tuck back, front slight forward
  pose(timeMs, 80, 80, 125, 125);
}

void CharlieServos::lieDown(int timeMs) {
  pose(timeMs, 130, 130, 130, 130);
}

void CharlieServos::playBow(int timeMs) {
  // Front back/down, rear forward/up
  pose(timeMs, 125, 125, 70, 70);
  delay(250);
  stand(timeMs);
}

void CharlieServos::beg(int timeMs) {
  // Front up/forward, rear planted back
  pose(timeMs, 55, 55, 120, 120);
}

void CharlieServos::stretch(int timeMs) {
  // Diagonal stretch
  pose(timeMs, 115, 70, 70, 115);
  delay(300);
  pose(timeMs, 70, 115, 115, 70);
  delay(300);
  stand(timeMs);
}

// ---- Gaits ----------------------------------------------------
// Crawl / creep: one leg swings while others plant (most stable, mePed-style)
// Trot: diagonal pairs LF+RB / RF+LB (classic simple 4-servo walk)

void CharlieServos::crawl(int steps, int stepMs, int dir) {
  const int a = _amp;
  const int f = (dir == FORWARD) ? -a : a;  // front swing direction
  const int b = (dir == FORWARD) ? a : -a;  // rear swing (opposite push)

  // Order: LF → RF → LB → RB (quad creep)
  const int order[4] = {LF, RF, LB, RB};

  for (int s = 0; s < steps; s++) {
    for (int k = 0; k < 4; k++) {
      int legs[COUNT] = {90, 90, 90, 90};
      const int leg = order[k];
      const int swing = (leg == LF || leg == RF) ? (90 + f) : (90 + b);
      legs[leg] = swing;
      // slight plant bias on opposite support
      stepPose(stepMs, legs[LF], legs[RF], legs[LB], legs[RB]);
      stepPose(stepMs / 2, 90, 90, 90, 90);
    }
  }
  stand(300);
}

void CharlieServos::trot(int steps, int stepMs, int dir) {
  const int a = _amp;
  const int f = (dir == FORWARD) ? -a : a;
  const int b = (dir == FORWARD) ? a : -a;

  for (int s = 0; s < steps; s++) {
    // Diagonal 1: LF + RB swing, RF + LB plant/push
    stepPose(stepMs,
             90 + f, 90,
             90, 90 + b);
    // Diagonal 2: RF + LB swing
    stepPose(stepMs,
             90, 90 + f,
             90 + b, 90);
  }
  stand(300);
}

void CharlieServos::walk(int steps, int stepMs, int dir) {
  crawl(steps, stepMs, dir);
}

void CharlieServos::turn(int steps, int stepMs, int dir) {
  const int a = _amp;
  // Left turn: left legs back, right legs forward (and vice versa)
  for (int s = 0; s < steps; s++) {
    if (dir == LEFT) {
      stepPose(stepMs, 90 + a, 90 - a, 90 + a, 90 - a);
      stepPose(stepMs, 90 - a, 90 + a, 90 - a, 90 + a);
    } else {
      stepPose(stepMs, 90 - a, 90 + a, 90 - a, 90 + a);
      stepPose(stepMs, 90 + a, 90 - a, 90 + a, 90 - a);
    }
  }
  stand(300);
}

void CharlieServos::sidestep(int steps, int stepMs, int dir) {
  // Limited with 1DOF — approximate with asymmetric diagonal
  const int a = _amp;
  for (int s = 0; s < steps; s++) {
    if (dir == LEFT) {
      stepPose(stepMs, 90 - a, 90, 90, 90 + a);
      stepPose(stepMs, 90, 90 + a, 90 - a, 90);
    } else {
      stepPose(stepMs, 90, 90 - a, 90 + a, 90);
      stepPose(stepMs, 90 + a, 90, 90, 90 - a);
    }
  }
  stand(300);
}

// ---- Expressions ----------------------------------------------

void CharlieServos::wag(int cycles, int stepMs) {
  const int a = _amp;
  for (int i = 0; i < cycles; i++) {
    stepPose(stepMs, 90 + a, 90 - a, 90 + a, 90 - a);
    stepPose(stepMs, 90 - a, 90 + a, 90 - a, 90 + a);
  }
  stand(250);
}

void CharlieServos::happy(int cycles, int stepMs) {
  const int a = _amp - 5;
  for (int i = 0; i < cycles; i++) {
    stepPose(stepMs, 90 - a, 90 - a, 90 - a, 90 - a);
    stepPose(stepMs, 90 + a, 90 + a, 90 + a, 90 + a);
  }
  stand(250);
}

void CharlieServos::sniff(int swings) {
  stand(200);
  for (int i = 0; i < swings; i++) {
    pose(220, 75, 90, 90, 90);
    pose(220, 90, 75, 90, 90);
  }
  stand(250);
}

void CharlieServos::howl(int timeMs) {
  pose(timeMs, 60, 60, 110, 110);
  delay(450);
  stand(timeMs);
}

void CharlieServos::shakePaw(int side, int taps) {
  sit(400);
  const int paw = (side == RIGHT) ? RF : LF;
  for (int i = 0; i < taps; i++) {
    int t[COUNT] = {_logical[LF], _logical[RF], _logical[LB], _logical[RB]};
    t[paw] = 45;
    moveServos(220, t);
    t[paw] = 90;
    moveServos(220, t);
  }
  stand(400);
}

void CharlieServos::pee(int side) {
  sit(350);
  if (side == LEFT) {
    pose(450, 90, 85, 45, 120);
  } else {
    pose(450, 85, 90, 120, 45);
  }
  delay(500);
  stand(450);
}

void CharlieServos::scared(int timeMs) {
  pose(timeMs, 140, 140, 140, 140);
  delay(200);
  stand(timeMs);
}

void CharlieServos::dance(int cycles) {
  for (int i = 0; i < cycles; i++) {
    wag(2, 150);
    happy(2, 140);
    pose(300, 70, 110, 110, 70);
    pose(300, 110, 70, 70, 110);
  }
  stand(300);
}

void CharlieServos::sleep() {
  lieDown(700);
  delay(150);
  detachServos();
  _resting = true;
}

void CharlieServos::demo() {
  stand(400);
  wag(4, 160);
  trot(4, 260, FORWARD);
  sit(500);
  delay(250);
  shakePaw(RIGHT, 2);
  playBow(400);
  happy(4, 150);
  sniff(3);
  howl(600);
  crawl(2, 320, FORWARD);
  stand(400);
}

int CharlieServos::getPosition(int leg) const {
  if (leg < 0 || leg >= COUNT) return -1;
  return _logical[leg];
}

void CharlieServos::status(Stream &out) const {
  out.println("CHARLIE dog  |  LF7  RF6");
  out.println("             |  LB5  RB4");
  out.print("resting=");
  out.println(_resting ? "yes" : "no");
  out.print("amp=");
  out.println(_amp);
  for (int i = 0; i < COUNT; i++) {
    out.print(LEG_NAME[i]);
    out.print(" pin");
    out.print(_pins[i]);
    out.print(" ch=");
    out.print(_servo[i].channel());
    out.print(" logical=");
    out.print(_logical[i]);
    out.print(" phys=");
    out.print(_servo[i].getPosition());
    out.println(_servo[i].attached() ? "" : " (DETACHED/FAIL)");
  }
}
