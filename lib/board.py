# lib/board.py
# CHARLIE pin map — change pins HERE, then every example follows.
#
#   OLED (SH1106 1.3")     Buzzer (passive)     Legs (MG90S)
#   SDA ── GPIO 10         Signal ── GPIO 13      LF 7 ---- RF 6
#   SCL ── GPIO 11                                 LB 5 ---- RB 4
#   ADDR ── 0x3C
#
# Power servos from 5V (external preferred). Share GND with ESP32.

# I2C OLED
OLED_SDA = 10
OLED_SCL = 11
OLED_ADDR = 0x3C
OLED_WIDTH = 128
OLED_HEIGHT = 64

# Audio
BUZZER_PIN = 13

# Status LED (ESP32-S3 onboard WS2812 / NeoPixel)
LED_PIN = 48
LED_COUNT = 1

# Legs — top view LF RF / LB RB (one servo per leg)
LEG_LF = 7
LEG_RF = 6
LEG_LB = 5
LEG_RB = 4

# Dog bark RTTTL (same as Arduino Buzzer sketch)
BARK = (
    "Bark:d=16,o=5,b=200:"
    "c6,e5,g5,p,c6,e5,g5,p,d6,f5,a5,p,c6,e5,g5"
)
