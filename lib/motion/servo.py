# lib/motion/servo.py
# One servo = one PWM pin at 50 Hz.
# Pulse width tells the angle (not duty %).
#
#   500 µs  ≈ 0°
#  1500 µs  ≈ 90°
#  2500 µs  ≈ 180°
#
#   from motion.servo import Servo
#   s = Servo(4)
#   s.write(90)

from machine import Pin, PWM
import time


class Servo:
    """Low-level MG90S / SG90 driver for ESP32 MicroPython."""

    FREQ_HZ = 50
    MIN_US = 500
    MAX_US = 2500

    def __init__(self, pin, min_us=MIN_US, max_us=MAX_US, trim=0):
        self.pin_num = pin
        self.min_us = min_us
        self.max_us = max_us
        self.trim = trim          # calibration offset in degrees
        self._pwm = None
        self._angle = 90
        self._deg_per_sec = 240   # Otto-style soft limit; 0 = off
        self.attach()

    def attach(self):
        if self._pwm is not None:
            return
        self._pwm = PWM(Pin(self.pin_num), freq=self.FREQ_HZ)
        self.write_us(1500)

    def detach(self):
        """Stop PWM (saves hold current; leg goes soft)."""
        if self._pwm is not None:
            self._pwm.deinit()
            self._pwm = None

    def attached(self):
        return self._pwm is not None

    def set_trim(self, degrees):
        self.trim = degrees

    def set_rate_limit(self, deg_per_sec):
        """Max speed in degrees/second. 0 disables. Default 240."""
        self._deg_per_sec = max(0, int(deg_per_sec))

    def write_us(self, pulse_us):
        """Send raw pulse. Learners: this is what the servo actually measures."""
        if self._pwm is None:
            self.attach()
        pulse_us = int(pulse_us)
        if pulse_us < self.min_us:
            pulse_us = self.min_us
        if pulse_us > self.max_us:
            pulse_us = self.max_us
        # Prefer duty_ns (absolute pulse). Fall back to duty_u16.
        try:
            self._pwm.duty_ns(pulse_us * 1000)
        except (AttributeError, ValueError, OSError):
            # period at 50 Hz = 20_000 µs
            duty = pulse_us * 65535 // 20_000
            self._pwm.duty_u16(duty)

    def angle_to_us(self, angle):
        angle = 0 if angle < 0 else 180 if angle > 180 else angle
        span = self.max_us - self.min_us
        return self.min_us + (angle * span) // 180

    def write(self, angle):
        """Move toward angle with optional rate limit (one step)."""
        target = int(angle) + self.trim
        if target < 0:
            target = 0
        if target > 180:
            target = 180

        if self._deg_per_sec > 0:
            # Approximate one frame ≈ 20 ms (servo period)
            step = max(1, self._deg_per_sec * 20 // 1000)
            if abs(target - self._angle) > step:
                target = self._angle + (step if target > self._angle else -step)

        self._angle = target
        self.write_us(self.angle_to_us(self._angle))

    def write_immediate(self, angle):
        """Jump to angle (ignores rate limit). Use for testing only."""
        target = int(angle) + self.trim
        if target < 0:
            target = 0
        if target > 180:
            target = 180
        self._angle = target
        self.write_us(self.angle_to_us(self._angle))

    def read(self):
        return self._angle

    def move_to(self, angle, time_ms=300):
        """Soft move over time_ms (blocking). Lower peak current."""
        if self._pwm is None:
            self.attach()
        start = self._angle
        target = int(angle) + self.trim
        if target < 0:
            target = 0
        if target > 180:
            target = 180
        if time_ms < 20:
            self.write_immediate(target - self.trim)
            return
        steps = max(1, time_ms // 20)
        for i in range(1, steps + 1):
            a = start + (target - start) * i // steps
            self._angle = a
            self.write_us(self.angle_to_us(a))
            time.sleep_ms(20)
