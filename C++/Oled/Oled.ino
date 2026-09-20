// CHARLIE OLED eyes — FluxGarage RoboEyes
// https://github.com/FluxGarage/RoboEyes
//
// Libraries (Arduino Library Manager):
//   - Adafruit GFX Library
//   - Adafruit SH110X
//   - FluxGarage RoboEyes

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <FluxGarage_RoboEyes.h>

static const int I2C_SDA_PIN = 10;
static const int I2C_SCL_PIN = 11;
static const uint8_t OLED_ADDR = 0x3C;

static const int SCREEN_WIDTH = 128;
static const int SCREEN_HEIGHT = 64;

Adafruit_SH1106G display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
RoboEyes<Adafruit_SH1106G> eyes(display);

// Cycle moods so CHARLIE feels alive without sensors yet.
enum AnimStep : uint8_t {
  STEP_WAKE,
  STEP_LOOK,
  STEP_HAPPY,
  STEP_LAUGH,
  STEP_CURIOUS,
  STEP_CONFUSED,
  STEP_TIRED,
  STEP_ANGRY,
  STEP_SLEEP,
  STEP_COUNT
};

unsigned long stepStartedAt = 0;
uint8_t step = STEP_WAKE;

static void startStep(uint8_t next) {
  step = next;
  stepStartedAt = millis();

  eyes.setCuriosity(OFF);
  eyes.setSweat(OFF);
  eyes.setHFlicker(OFF);
  eyes.setVFlicker(OFF);

  switch (step) {
    case STEP_WAKE:
      eyes.setMood(DEFAULT);
      eyes.setPosition(DEFAULT);
      eyes.open();
      break;

    case STEP_LOOK:
      eyes.setMood(DEFAULT);
      eyes.setIdleMode(ON, 1, 1);
      eyes.setAutoblinker(ON, 2, 1);
      break;

    case STEP_HAPPY:
      eyes.setIdleMode(OFF);
      eyes.setMood(HAPPY);
      eyes.setPosition(DEFAULT);
      break;

    case STEP_LAUGH:
      eyes.setMood(HAPPY);
      eyes.anim_laugh();
      break;

    case STEP_CURIOUS:
      eyes.setMood(DEFAULT);
      eyes.setCuriosity(ON);
      eyes.setPosition(E);
      break;

    case STEP_CONFUSED:
      eyes.setCuriosity(OFF);
      eyes.setMood(DEFAULT);
      eyes.anim_confused();
      break;

    case STEP_TIRED:
      eyes.setMood(TIRED);
      eyes.setPosition(S);
      break;

    case STEP_ANGRY:
      eyes.setMood(ANGRY);
      eyes.setPosition(DEFAULT);
      eyes.setHFlicker(ON, 2);
      break;

    case STEP_SLEEP:
      eyes.setHFlicker(OFF);
      eyes.setMood(TIRED);
      eyes.close();
      break;
  }
}

static unsigned long stepDurationMs() {
  switch (step) {
    case STEP_WAKE:     return 1500;
    case STEP_LOOK:     return 5000;
    case STEP_HAPPY:    return 2500;
    case STEP_LAUGH:    return 2000;
    case STEP_CURIOUS:  return 2500;
    case STEP_CONFUSED: return 2000;
    case STEP_TIRED:    return 2500;
    case STEP_ANGRY:    return 2500;
    case STEP_SLEEP:    return 2000;
    default:            return 2000;
  }
}

void setup() {
  Serial.begin(115200);
  delay(250);

  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  Wire.setClock(400000);

  if (!display.begin(OLED_ADDR, true)) {
    Serial.println("SH1106 init failed");
    while (true) {
      delay(1000);
    }
  }

  eyes.begin(SCREEN_WIDTH, SCREEN_HEIGHT, 60);
  eyes.setAutoblinker(ON, 3, 2);
  eyes.close();

  startStep(STEP_WAKE);
  Serial.println("CHARLIE RoboEyes ready");
}

void loop() {
  eyes.update();  // never use delay() here

  if (millis() - stepStartedAt >= stepDurationMs()) {
    uint8_t next = step + 1;
    if (next >= STEP_COUNT) {
      next = STEP_WAKE;
    }
    startStep(next);
  }
}
