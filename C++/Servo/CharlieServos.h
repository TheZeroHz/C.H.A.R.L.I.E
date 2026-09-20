//--------------------------------------------------------------
// CharlieServos — 4-leg DOG (1 servo per leg)
//
// Top view (your chassis):
//   LF pin7 ---- RF pin6
//   LB pin5 ---- RB pin4
//
// Shafts face OUTWARD → right side is mirrored (180 - angle)
// Soft moves + rate limit (Otto-style current care)
//--------------------------------------------------------------
#ifndef CharlieServos_h
#define CharlieServos_h

#include "CharlieOscillator.h"

#ifndef SERVO_LIMIT_DEFAULT
#define SERVO_LIMIT_DEFAULT 240
#endif

#define FORWARD  1
#define BACKWARD -1
#define LEFT     1
#define RIGHT   -1

class CharlieServos {
public:
  static const int COUNT = 4;
  // Logical indices (not pin order)
  static const int LF = 0;
  static const int RF = 1;
  static const int LB = 2;
  static const int RB = 3;

  void begin(const int pins[COUNT]);  // pins[LF,RF,LB,RB]

  void attachServos();
  void detachServos();
  bool attached() const;

  void setTrims(int lf, int rf, int lb, int rb);
  void enableServoLimit(int degPerSec = SERVO_LIMIT_DEFAULT);
  void disableServoLimit();

  // Logical angles 0..180 (90 = neutral stand). Mirroring applied inside.
  void moveServos(int timeMs, const int logical[COUNT]);
  void moveSingle(int leg, int logicalAngle, int timeMs = 300);
  void setLeg(int leg, int logicalAngle);  // immediate soft-limited write

  void home(int timeMs = 500);
  bool getRestState() const { return _resting; }
  void setRestState(bool state) { _resting = state; }

  // --- Dog poses ---
  void stand(int timeMs = 500);
  void sit(int timeMs = 600);
  void lieDown(int timeMs = 700);
  void playBow(int timeMs = 500);
  void beg(int timeMs = 500);
  void stretch(int timeMs = 500);

  // --- Gaits (1DOF/leg community patterns) ---
  void crawl(int steps = 4, int stepMs = 350, int dir = FORWARD);
  void trot(int steps = 6, int stepMs = 280, int dir = FORWARD);
  void walk(int steps = 4, int stepMs = 350, int dir = FORWARD);  // alias crawl
  void turn(int steps = 4, int stepMs = 320, int dir = LEFT);
  void sidestep(int steps = 3, int stepMs = 300, int dir = LEFT);

  // --- Expressions ---
  void wag(int cycles = 6, int stepMs = 180);
  void happy(int cycles = 5, int stepMs = 160);
  void sniff(int swings = 4);
  void howl(int timeMs = 700);
  void shakePaw(int side = RIGHT, int taps = 3);
  void pee(int side = LEFT);
  void scared(int timeMs = 400);
  void dance(int cycles = 2);
  void sleep();
  void demo();

  int getPosition(int leg) const;  // logical
  void status(Stream &out) const;

private:
  void wakeFromRest();
  int toPhysical(int leg, int logical) const;
  int fromPhysical(int leg, int physical) const;
  void writePhysical(int leg, int physical);
  void pose(int timeMs, int lf, int rf, int lb, int rb);
  void stepPose(int timeMs, int lf, int rf, int lb, int rb);

  CharlieOscillator _servo[COUNT];
  int _pins[COUNT] = {7, 6, 5, 4};  // LF, RF, LB, RB
  int _logical[COUNT] = {90, 90, 90, 90};
  bool _resting = true;

  // Gait amplitude (deg from neutral). Tune after leg horns are fitted.
  int _amp = 25;
};

#endif
