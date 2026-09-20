# main.py — WiFi Manager portal when not connected; OLED status when STA up

import time

try:
    import boot as _boot

    need_portal = not getattr(_boot, "WIFI_OK", False)
except Exception:
    need_portal = True

if need_portal:
    print("CHARLIE WiFi Manager")
    print("1) Join SoftAP 'charlie' (open)")
    print("2) Open http://192.168.4.1/")
    try:
        from wifi_manager import run_portal

        run_portal()
    except Exception as e:
        print("portal error:", e)
        try:
            from oled_status import show_msg

            show_msg("portal error", str(e)[:16])
        except Exception:
            pass
        while True:
            time.sleep(10)
else:
    print("CHARLIE ready — WiFi + WebREPL up")
    try:
        from oled_status import show

        while True:
            show(msg="linked")
            time.sleep(5)
    except Exception:
        while True:
            time.sleep(60)
