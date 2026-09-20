# CHARLIE MicroPython — learner layout
#
# Board: ESP32-S3 SuperMini · 4 MB flash
# Idea: import drivers yourself. One pin map. Short examples.

## Folder map

```text
esp32s3-micropython/
├── boot.py
├── main.py                      # default = OLED eyes demo
├── lib/
│   ├── board.py                 # ALL pins — start here
│   ├── display/                 # OLED
│   │   ├── sh1106.py
│   │   ├── fbutil.py
│   │   └── roboeyes.py
│   ├── sound/
│   │   └── rtttl/               # TheZeroHz RTTTL
│   └── motion/                  # servos
│       ├── servo.py             # one motor (PWM pulse)
│       └── legs.py              # 4-leg dog (mirror + gaits)
└── examples/
    ├── 01_i2c_scan.py
    ├── 02_oled_hello.py
    ├── 03_eyes_basic.py
    ├── 04_bark.py
    ├── 05_nokia.py
    ├── 06_servo_one.py
    ├── 07_stand_sit.py
    ├── 08_trot.py
    ├── 09_dog_all_legs.py
    └── 10_slow_leg_test.py  # slow per-leg angle sweep
```

## How to import (low level)

```python
from board import OLED_SDA, BUZZER_PIN, LEG_LF, LEG_RF, LEG_LB, LEG_RB

from display.sh1106 import SH1106_I2C
from display.roboeyes import RoboEyes, ON, HAPPY

from sound.rtttl import PlayRtttl

from motion.servo import Servo
from motion.legs import Legs
```

## Pin map (`lib/board.py`)

| Part | Pins |
|------|------|
| OLED SH1106 | SDA **10**, SCL **11**, **0x3C** |
| Buzzer | **13** |
| Legs | LF **7**, RF **6**, LB **5**, RB **4** |

Right legs are mirrored in software (shafts face out).

## WebREPL (browser over WiFi)

1. Edit `lib/secrets.py` (SSID / WiFi password).
2. Board boots → joins WiFi → starts WebREPL.
3. Open http://micropython.org/webrepl/
4. Connect to `ws://<board-ip>:8266/`
5. Password default: **`charlie`** (`webrepl_cfg.py`)

Needs **2.4 GHz** WiFi (ESP32-S3 has no 5 GHz).
