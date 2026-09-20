# boot.py — try saved WiFi; OLED shows AP/STA status. Portal in main.py.

import gc
import network

gc.collect()

try:
    from secrets import MDNS_HOSTNAME, WEBREPL_PASSWORD
except ImportError:
    MDNS_HOSTNAME = "charlie"
    WEBREPL_PASSWORD = "charlie"

try:
    network.hostname(MDNS_HOSTNAME)
except Exception:
    pass

WIFI_OK = False

try:
    from oled_status import show, show_msg
except Exception:
    show = None
    show_msg = None

try:
    from wifi import connect, ip
    from wifi_cfg import load
    import webrepl

    cfg = load()
    if cfg:
        if show_msg:
            show_msg("STA connecting", cfg["ssid"])
        print("boot: trying saved WiFi %r" % cfg["ssid"])
        WIFI_OK = connect(cfg["ssid"], cfg["password"], timeout_ms=18000)

    if WIFI_OK:
        webrepl.start(password=WEBREPL_PASSWORD)
        print("STA ok ip=%s  mDNS=%s.local" % (ip(), MDNS_HOSTNAME))
        print("WebREPL ws://%s:8266/  pass=%s" % (ip(), WEBREPL_PASSWORD))
        if show:
            show(msg="linked")
    else:
        print("boot: no WiFi - portal starts in main.py")
        if show_msg:
            show_msg("No STA", "Starting AP", "portal...")
except Exception as e:
    print("boot network error:", e)
    if show_msg:
        show_msg("boot error", str(e)[:16])

gc.collect()
