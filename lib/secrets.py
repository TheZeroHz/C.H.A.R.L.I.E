# lib/secrets.py
# SoftAP / WebREPL defaults only.
# STA SSID+password come from the captive portal → /wifi.json (not here).

# Cleared on purpose — first boot opens AP config portal
WIFI_NETWORKS = ()

# SoftAP for WiFi Manager (open = easiest phone join). Set 8+ chars for WPA2.
AP_SSID = "charlie"
AP_PASSWORD = ""  # open SoftAP

# mDNS name → http://charlie.local/  (and SoftAP captive redirect)
MDNS_HOSTNAME = "charlie"

# WebREPL login at http://micropython.org/webrepl/
WEBREPL_PASSWORD = "charlie"
