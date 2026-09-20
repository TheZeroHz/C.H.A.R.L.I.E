# examples/04_bark.py
# Lesson 4: RTTTL on the passive buzzer (GPIO from board.py).
# Run:  mpremote connect COMx run examples/04_bark.py

from board import BUZZER_PIN, BARK
from sound.rtttl import PlayRtttl

player = PlayRtttl(pin=BUZZER_PIN)
print("bark on GPIO%d" % BUZZER_PIN)
player.play_blocking(BARK)
print("done")
