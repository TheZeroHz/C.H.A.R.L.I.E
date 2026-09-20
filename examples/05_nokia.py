# examples/05_nokia.py
# Lesson 5: play a built-in ringtone from the RTTTL melody list.
# Run:  mpremote connect COMx run examples/05_nokia.py

from board import BUZZER_PIN
from sound.rtttl import PlayRtttl
from sound.rtttl.melodies import RTTTL_MELODIES_TINY

player = PlayRtttl(pin=BUZZER_PIN)
# TINY list is small — good for learning without filling RAM
print("playing a tiny melody…")
player.play_random_blocking(RTTTL_MELODIES_TINY)
print("done")
