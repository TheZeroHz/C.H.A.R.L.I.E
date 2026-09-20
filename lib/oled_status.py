# lib/oled_status.py
# Compact WiFi / WebREPL status on SH1106 (5x7 font, essentials only).

from machine import Pin, I2C

try:
    from board import OLED_SDA, OLED_SCL, OLED_ADDR, OLED_WIDTH, OLED_HEIGHT
except ImportError:
    OLED_SDA, OLED_SCL, OLED_ADDR = 10, 11, 0x3C
    OLED_WIDTH, OLED_HEIGHT = 128, 64

from display.font5x7 import draw_text, CHAR_DY, COLS

_oled = None


def _get_oled():
    global _oled
    if _oled is not None:
        return _oled
    try:
        from display.sh1106 import SH1106_I2C

        i2c = I2C(0, sda=Pin(OLED_SDA), scl=Pin(OLED_SCL), freq=400_000)
        oled = SH1106_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, res=None, addr=OLED_ADDR)
        oled.sleep(False)
        _oled = oled
        return oled
    except Exception as e:
        print("oled_status: init fail", e)
        return None


def _clip(s, n=COLS):
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[: n - 1] + "~"


def _paint(lines):
    """Draw packed lines with 5x7 font (up to 8 rows)."""
    oled = _get_oled()
    if not oled:
        return False
    try:
        oled.fill(0)
        y = 0
        for line in lines:
            if line is None:
                break
            if line != "":
                draw_text(oled, _clip(line), 0, y, 1)
            y += CHAR_DY
            if y > OLED_HEIGHT - CHAR_DY:
                break
        oled.show()
        return True
    except Exception as e:
        print("oled_status: paint fail", e)
        return False


def _webrepl_pass():
    try:
        from secrets import WEBREPL_PASSWORD

        return WEBREPL_PASSWORD
    except Exception:
        return "charlie"


def _sta_info():
    import network

    try:
        sta = network.WLAN(network.WLAN.IF_STA)
    except AttributeError:
        sta = network.WLAN(network.STA_IF)
    if not (sta.active() and sta.isconnected()):
        return False, "", ""
    try:
        ssid = sta.config("ssid")
    except Exception:
        ssid = "?"
    if isinstance(ssid, bytes):
        ssid = ssid.decode()
    return True, ssid, sta.ifconfig()[0]


def _ap_info():
    import network

    try:
        ap = network.WLAN(network.WLAN.IF_AP)
    except AttributeError:
        ap = network.WLAN(network.AP_IF)
    if not ap.active():
        return False, "", ""
    try:
        essid = ap.config("essid")
    except Exception:
        essid = "?"
    if isinstance(essid, bytes):
        essid = essid.decode()
    return True, essid, ap.ifconfig()[0]


def show(msg=None, title=None):
    """
    STA linked:
      <ssid>
      <ip>
      :8266
      <password>

    SoftAP portal:
      AP <essid>
      <ap-ip>
      setup

    Else progress via msg / defaults.
    """
    sta_ok, ssid, ip = _sta_info()
    if sta_ok:
        return _paint([ssid, ip, ":8266", _webrepl_pass()])

    ap_on, essid, ap_ip = _ap_info()
    if ap_on:
        return _paint(["AP " + essid, ap_ip, msg or "setup"])

    if msg:
        return _paint([msg])
    return _paint(["STA ..."])


def show_webrepl():
    return show()


def show_msg(line1, line2="", line3=""):
    lines = [line1]
    if line2:
        lines.append(line2)
    if line3:
        lines.append(line3)
    return _paint(lines)
