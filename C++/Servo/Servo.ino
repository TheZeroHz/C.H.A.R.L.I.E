// CHARLIE the dog — 4 legs, 1 servo each
//
//   LF pin7 ---- RF pin6
//   LB pin5 ---- RB pin4
//
// Right side mirrored. Soft moves + 240°/s limit.
// Library: ESP32Servo

#include "CharlieServos.h"

// Order must be LF, RF, LB, RB
static const int SERVO_PINS[CharlieServos::COUNT] = {7, 6, 5, 4};
CharlieServos charlie;

String line;

static int clampAngle(int a) {
  if (a < 0) return 0;
  if (a > 180) return 180;
  return a;
}

static void printHelp() {
  Serial.println();
  Serial.println("CHARLIE dog CLI");
  Serial.println("  LF=7  RF=6  LB=5  RB=4  (right mirrored)");
  Serial.println();
  Serial.println("Poses:  stand sit lie bow beg stretch sleep home");
  Serial.println("Gaits:  crawl trot walk walkback turnl turnr sideL sideR");
  Serial.println("Vibes:  wag happy sniff howl paw pawl pee scared dance demo");
  Serial.println("Manual: status | lf|rf|lb|rb <deg> [ms] | all <deg> [ms]");
  Serial.println("        testpin 4   raw sweep GPIO (bypass dog layer)");
  Serial.println("        limit on|off | attach");
  Serial.println();
}

static void handleCommand(String cmd) {
  cmd.trim();
  cmd.toLowerCase();
  if (cmd.length() == 0) return;

  if (cmd == "help" || cmd == "?") { printHelp(); return; }
  if (cmd == "status") { charlie.status(Serial); return; }

  if (cmd == "home") {
    if (charlie.getRestState()) {
      charlie.attachServos();
      charlie.setRestState(false);
    }
    charlie.home(500);
    Serial.println("home + detached");
    return;
  }
  if (cmd == "attach") {
    charlie.attachServos();
    charlie.setRestState(false);
    Serial.println("attached");
    charlie.status(Serial);
    return;
  }

  // Raw GPIO servo test — proves pin PWM independent of dog mapping
  if (cmd.startsWith("testpin ")) {
    int pin = cmd.substring(8).toInt();
    if (pin <= 0) {
      Serial.println("usage: testpin 4");
      return;
    }
    Serial.print("RAW test GPIO ");
    Serial.println(pin);
    charlie.detachServos();
    delay(50);

    Servo raw;
    ESP32PWM::allocateTimer(0);
    raw.setPeriodHertz(50);
    int ch = raw.attach(pin, 500, 2500);
    Serial.print("attach channel=");
    Serial.println(ch);
    if (ch < 0) {
      Serial.println("FAIL: no LEDC channel — update ESP32Servo library");
      charlie.attachServos();
      return;
    }

    for (int a = 0; a <= 180; a += 30) {
      Serial.print("  write ");
      Serial.println(a);
      raw.write(a);
      delay(400);
    }
    for (int a = 180; a >= 0; a -= 30) {
      Serial.print("  write ");
      Serial.println(a);
      raw.write(a);
      delay(400);
    }
    raw.write(90);
    delay(300);
    raw.detach();
    charlie.attachServos();
    charlie.setRestState(false);
    Serial.println("raw test done — reattached dog servos");
    return;
  }

  if (cmd == "testrb") {
    handleCommand("testpin 4");
    return;
  }
  if (cmd == "limit on") {
    charlie.enableServoLimit(SERVO_LIMIT_DEFAULT);
    Serial.println("limit on");
    return;
  }
  if (cmd == "limit off") {
    charlie.disableServoLimit();
    Serial.println("limit off");
    return;
  }

  if (cmd == "stand" || cmd == "center") { charlie.stand(); Serial.println("stand"); return; }
  if (cmd == "sit") { charlie.sit(); Serial.println("sit"); return; }
  if (cmd == "lie" || cmd == "liedown") { charlie.lieDown(); Serial.println("lie"); return; }
  if (cmd == "bow" || cmd == "playbow") { charlie.playBow(); Serial.println("bow"); return; }
  if (cmd == "beg") { charlie.beg(); Serial.println("beg"); return; }
  if (cmd == "stretch") { charlie.stretch(); Serial.println("stretch"); return; }
  if (cmd == "sleep") { charlie.sleep(); Serial.println("zzz"); return; }

  if (cmd == "crawl") { Serial.println("crawl..."); charlie.crawl(); Serial.println("done"); return; }
  if (cmd == "trot") { Serial.println("trot..."); charlie.trot(); Serial.println("done"); return; }
  if (cmd == "walk") { Serial.println("walk..."); charlie.walk(); Serial.println("done"); return; }
  if (cmd == "walkback") {
    Serial.println("walk back...");
    charlie.walk(4, 350, BACKWARD);
    Serial.println("done");
    return;
  }
  if (cmd == "turnl") { Serial.println("turn L..."); charlie.turn(4, 320, LEFT); Serial.println("done"); return; }
  if (cmd == "turnr") { Serial.println("turn R..."); charlie.turn(4, 320, RIGHT); Serial.println("done"); return; }
  if (cmd == "sidel") { Serial.println("side L..."); charlie.sidestep(3, 300, LEFT); Serial.println("done"); return; }
  if (cmd == "sider") { Serial.println("side R..."); charlie.sidestep(3, 300, RIGHT); Serial.println("done"); return; }

  if (cmd == "wag") { charlie.wag(); Serial.println("wag"); return; }
  if (cmd == "happy") { charlie.happy(); Serial.println("happy"); return; }
  if (cmd == "sniff") { charlie.sniff(); Serial.println("sniff"); return; }
  if (cmd == "howl") { charlie.howl(); Serial.println("howl"); return; }
  if (cmd == "paw" || cmd == "pawr") { charlie.shakePaw(RIGHT); Serial.println("paw R"); return; }
  if (cmd == "pawl") { charlie.shakePaw(LEFT); Serial.println("paw L"); return; }
  if (cmd == "pee") { charlie.pee(LEFT); Serial.println("pee"); return; }
  if (cmd == "scared") { charlie.scared(); Serial.println("scared"); return; }
  if (cmd == "dance") { charlie.dance(); Serial.println("dance"); return; }
  if (cmd == "demo") { Serial.println("demo..."); charlie.demo(); Serial.println("good boy"); return; }

  // all <deg> [ms]
  if (cmd.startsWith("all ")) {
    int space = cmd.indexOf(' ', 4);
    int angle = clampAngle(cmd.substring(4).toInt());
    int ms = 400;
    if (space > 0) {
      ms = cmd.substring(space + 1).toInt();
      if (ms <= 0) ms = 400;
    }
    int t[4] = {angle, angle, angle, angle};
    charlie.moveServos(ms, t);
    Serial.print("all logical=");
    Serial.println(angle);
    return;
  }

  // lf|rf|lb|rb <deg> [ms]
  int leg = -1;
  String rest;
  if (cmd.startsWith("lf ")) { leg = CharlieServos::LF; rest = cmd.substring(3); }
  else if (cmd.startsWith("rf ")) { leg = CharlieServos::RF; rest = cmd.substring(3); }
  else if (cmd.startsWith("lb ")) { leg = CharlieServos::LB; rest = cmd.substring(3); }
  else if (cmd.startsWith("rb ")) { leg = CharlieServos::RB; rest = cmd.substring(3); }

  if (leg >= 0) {
    rest.trim();
    int space = rest.indexOf(' ');
    int angle = clampAngle(rest.toInt());
    int ms = 300;
    if (space > 0) {
      ms = rest.substring(space + 1).toInt();
      if (ms <= 0) ms = 300;
    }
    charlie.moveSingle(leg, angle, ms);
    Serial.print("leg logical=");
    Serial.println(angle);
    return;
  }

  Serial.print("unknown: ");
  Serial.println(cmd);
  Serial.println("type help");
}

void setup() {
  Serial.begin(115200);
  delay(300);
  charlie.begin(SERVO_PINS);
  Serial.println("CHARLIE dog awake (quad map)");
  printHelp();
  charlie.status(Serial);
  Serial.print("> ");
}

void loop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      Serial.println();
      handleCommand(line);
      line = "";
      Serial.print("> ");
    } else {
      line += c;
    }
  }
}
