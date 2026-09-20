# examples/11_wifi_webrepl.py
# Connect WiFi and print WebREPL URL (also done automatically in boot.py).
# Run: mpremote connect COMx run examples/11_wifi_webrepl.py

from wifi import connect, ip, ifconfig
import webrepl

if connect():
    webrepl.start()
    print("")
    print("Open:  http://micropython.org/webrepl/")
    print("URL:   ws://%s:8266/" % ip())
    print("Pass:  (WEBREPL_PASSWORD in lib/secrets.py)")
    print("ifconfig:", ifconfig())
else:
    print("failed — check SSID/password (2.4 GHz) in lib/secrets.py")
