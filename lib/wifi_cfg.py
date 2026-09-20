# lib/wifi_cfg.py
# Persist STA credentials from the WiFi Manager portal (/wifi.json).

import json

CFG_PATH = "/wifi.json"


def load():
    """Return {"ssid": str, "password": str} or None."""
    try:
        with open(CFG_PATH) as f:
            data = json.load(f)
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    ssid = data.get("ssid") or ""
    if not ssid:
        return None
    return {"ssid": ssid, "password": data.get("password") or ""}


def save(ssid, password=""):
    """Write STA credentials and verify. Returns True on success."""
    if not ssid:
        return False
    try:
        with open(CFG_PATH, "w") as f:
            json.dump({"ssid": ssid, "password": password or ""}, f)
            try:
                f.flush()
            except Exception:
                pass
        try:
            import os

            if hasattr(os, "sync"):
                os.sync()
        except Exception:
            pass
        # Verify round-trip
        cfg = load()
        if not cfg or cfg.get("ssid") != ssid:
            print("wifi_cfg: verify failed", cfg)
            return False
        print("wifi_cfg: saved", cfg["ssid"])
        return True
    except OSError as e:
        print("wifi_cfg: save failed", e)
        return False


def clear():
    """Remove saved STA credentials."""
    try:
        import os

        os.remove(CFG_PATH)
        return True
    except OSError:
        return False


def networks():
    """[(ssid, password), ...] for wifi.connect — saved cfg first."""
    cfg = load()
    if cfg:
        return [(cfg["ssid"], cfg["password"])]
    return []
