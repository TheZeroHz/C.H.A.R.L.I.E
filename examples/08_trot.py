# examples/08_trot.py
# Lesson 8: diagonal trot gait (LF+RB / RF+LB).
# Run: mpremote connect COMx run examples/08_trot.py

from motion.legs import Legs

dog = Legs()
print("trot…")
dog.trot(steps=4)
print("wag…")
dog.wag(cycles=4)
dog.home()
print("done")
