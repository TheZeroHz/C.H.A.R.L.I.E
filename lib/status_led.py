# lib/status_led.py
# Onboard green blink on GPIO 48 (WS2812) when WiFi STA connects.

import time

try:
    from board import LED_PIN, LED_COUNT
except ImportError:
    LED_PIN = 48
    LED_COUNT = 1

# GRB order common on ESP32-S3 Dev boards; bright but not max
_GREEN = (0, 40, 0)
_OFF = (0, 0, 0)


def blink_green(times=10, on_ms=120, off_ms=120):
    """Blink green LED `times` times (WiFi connected signal)."""
    try:
        from machine import Pin
        from neopixel import NeoPixel

        np = NeoPixel(Pin(LED_PIN), LED_COUNT)
        for _ in range(times):
            np[0] = _GREEN
            np.write()
            time.sleep_ms(on_ms)
            np[0] = _OFF
            np.write()
            time.sleep_ms(off_ms)
        return True
    except Exception as e:
        # Fallback: plain GPIO toggle if no NeoPixel
        try:
            from machine import Pin

            led = Pin(LED_PIN, Pin.OUT)
            for _ in range(times):
                led.value(1)
                time.sleep_ms(on_ms)
                led.value(0)
                time.sleep_ms(off_ms)
            return True
        except Exception as e2:
            print("status_led:", e, e2)
            return False


def wifi_connected_blink():
    """Call after successful STA join."""
    print("status_led: WiFi OK — green blink x10 on GPIO%d" % LED_PIN)
    blink_green(10)
