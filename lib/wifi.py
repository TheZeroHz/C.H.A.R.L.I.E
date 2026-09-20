# lib/wifi.py
# STA = join home WiFi (docs: network.WLAN.IF_STA + connect + isconnected)
# AP  = CHARLIE SoftAP fallback for WebREPL
#
#   from wifi import connect, start_ap, ensure_network, ip

import network
import time
import binascii

try:
    from secrets import WIFI_NETWORKS, AP_SSID, AP_PASSWORD
except ImportError:
    WIFI_NETWORKS = ()
    AP_SSID = ""
    AP_PASSWORD = ""

AP_IP = "192.168.4.1"


def _sta_networks():
    """[(ssid, password), ...] — saved portal cfg first, then secrets.WIFI_NETWORKS."""
    nets = []
    try:
        from wifi_cfg import networks as _saved

        for ssid, password in _saved():
            if ssid:
                nets.append((ssid, password if password is not None else ""))
    except ImportError:
        pass
    for entry in WIFI_NETWORKS or ():
        if not entry:
            continue
        if isinstance(entry, (tuple, list)) and len(entry) >= 2:
            ssid, password = entry[0], entry[1]
        else:
            ssid, password = entry, ""
        if ssid and ssid not in [n[0] for n in nets]:
            nets.append((ssid, password if password is not None else ""))
    return nets

_STAT = {
    network.STAT_IDLE: "idle",
    network.STAT_CONNECTING: "connecting",
    network.STAT_WRONG_PASSWORD: "WRONG_PASSWORD",
    network.STAT_NO_AP_FOUND: "no_ap",
    network.STAT_CONNECT_FAIL: "connect_fail",
    network.STAT_GOT_IP: "got_ip",
    # ESP-IDF disconnect reasons sometimes surface as raw ints:
    2: "auth_expire",
    15: "4way_handshake_timeout",
    204: "handshake_timeout",
}


def _sta():
    # Prefer new constant; fall back for older firmware names
    try:
        return network.WLAN(network.WLAN.IF_STA)
    except AttributeError:
        return network.WLAN(network.STA_IF)


def _ap():
    try:
        return network.WLAN(network.WLAN.IF_AP)
    except AttributeError:
        return network.WLAN(network.AP_IF)


def _status_name(st):
    return _STAT.get(st, "?")


def _ensure_sta_up():
    """Docs pattern: activate STA, disable power-save, no thrashing."""
    # SoftAP can steal the radio — turn it off while joining home WiFi
    ap = _ap()
    if ap.active():
        try:
            ap.active(False)
            time.sleep_ms(200)
        except OSError:
            pass

    wlan = _sta()
    if not wlan.active():
        wlan.active(True)
        time.sleep_ms(200)

    try:
        wlan.config(pm=network.WLAN.PM_NONE)
    except Exception:
        try:
            wlan.config(pm=wlan.PM_NONE)
        except Exception:
            pass

    # A few retries help flaky auth; still bounded by our timeout loop
    try:
        wlan.config(reconnects=3)
    except Exception:
        pass

    return wlan


def scan_for(ssid=None):
    """
    Scan 2.4 GHz APs. Returns list of (ssid, bssid, channel, rssi, security)
    sorted strongest-first. If ssid given, only that name.
    """
    wlan = _ensure_sta_up()
    try:
        raw = wlan.scan()
    except OSError as e:
        print("wifi: scan error", e)
        return []

    out = []
    want = None if ssid is None else ssid.encode() if isinstance(ssid, str) else ssid
    for row in raw:
        # (ssid, bssid, channel, RSSI, security, hidden)
        s, bssid, ch, rssi, sec, hid = row[0], row[1], row[2], row[3], row[4], row[5]
        if want is not None and s != want:
            continue
        # ESP32 STA is 2.4 GHz only — ignore 5 GHz channels if ever reported
        if ch > 14:
            continue
        name = s.decode() if isinstance(s, (bytes, bytearray)) else str(s)
        out.append((name, bssid, ch, rssi, sec))

    out.sort(key=lambda r: r[3], reverse=True)
    return out


def connect(ssid=None, password=None, timeout_ms=20000):
    """
    Join home WiFi the MicroPython-docs way:
      wlan.active(True); wlan.connect(ssid, key, bssid=...); wait isconnected()

    Scans first and locks onto the strongest matching BSSID (avoids Smart Connect
    sending us at a 5 GHz AP the ESP cannot use).

    Credentials come from secrets.WIFI_NETWORKS (or ssid/password args).
    """
    if ssid is not None:
        pwd = "" if password is None else password
        candidates = [(ssid, pwd)]
    else:
        candidates = _sta_networks()

    if not candidates:
        print("wifi: set WIFI_NETWORKS in lib/secrets.py")
        return False

    # ssid -> password for lookup when scanning hits
    pwd_by_ssid = {}
    for name, pwd in candidates:
        if name not in pwd_by_ssid:
            pwd_by_ssid[name] = pwd

    wlan = _ensure_sta_up()

    # Drop any half-open session without full radio reset
    try:
        if wlan.isconnected():
            wlan.disconnect()
            time.sleep_ms(200)
    except OSError:
        pass

    print("wifi: scanning...")
    hits = []
    primary = candidates[0][0]
    for name, _pwd in candidates:
        found = scan_for(name)
        for row in found:
            hits.append(row)
        print("wifi: scan %r -> %d AP(s)" % (name, len(found)))
        for name2, bssid, ch, rssi, sec in found[:3]:
            print(
                "  %s  ch=%d  rssi=%d  sec=%d  bssid=%s"
                % (name2, ch, rssi, sec, binascii.hexlify(bssid).decode())
            )
        # Prefer primary SSID only when it is visible (don't try other APs with wrong key)
        if name == primary and found:
            hits = list(found)
            break

    if not hits:
        print("wifi: no matching 2.4GHz SSID in scan — STA cannot join")
        return False

    # Strongest first
    hits.sort(key=lambda r: r[3], reverse=True)

    for name, bssid, ch, rssi, sec in hits:
        password = pwd_by_ssid.get(name, "")
        # Open AP (security 0): no key. Secured: use password.
        if sec == 0 or not password:
            key = None
            key_note = "open"
        else:
            key = password
            key_note = "psk"

        print(
            "wifi: STA connect %r ch=%d rssi=%d sec=%d (%s) bssid=%s"
            % (name, ch, rssi, sec, key_note, binascii.hexlify(bssid).decode())
        )
        try:
            if key is None:
                try:
                    wlan.connect(name, None, bssid=bssid)
                except TypeError:
                    wlan.connect(name, bssid=bssid)
            else:
                wlan.connect(name, key, bssid=bssid)
        except TypeError:
            wlan.connect(name, key)
        except OSError as e:
            print("wifi: connect() error", e)
            continue

        t0 = time.ticks_ms()
        last = None
        while not wlan.isconnected():
            st = wlan.status()
            if st != last:
                print("wifi: status", st, _status_name(st))
                last = st
            # Terminal failures — try next BSSID/SSID
            if st in (
                network.STAT_WRONG_PASSWORD,
                network.STAT_NO_AP_FOUND,
                network.STAT_CONNECT_FAIL,
            ):
                break
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_ms:
                print("wifi: timeout last=", st, _status_name(st))
                break
            time.sleep_ms(150)

        if wlan.isconnected():
            print("wifi: STA ok", wlan.ifconfig())
            try:
                from oled_status import show

                show(msg="linked")
            except Exception:
                pass
            try:
                from status_led import wifi_connected_blink

                wifi_connected_blink()
            except Exception as e:
                print("wifi: led blink skip", e)
            return True

        try:
            wlan.disconnect()
        except OSError:
            pass
        time.sleep_ms(300)

    print("wifi: STA failed all candidates")
    return False


def stop_ap():
    """Fully disable SoftAP so STA can own the radio."""
    ap = _ap()
    if ap.active():
        try:
            ap.active(False)
            time.sleep_ms(400)
        except Exception as e:
            print("wifi: stop_ap", e)
    return not ap.active()


def start_ap(ssid=None, password=None, channel=6):
    """Start CHARLIE SoftAP (2.4 GHz). Open if password empty; else WPA2 (>=8)."""
    ssid = AP_SSID if ssid is None else ssid
    if password is None:
        password = AP_PASSWORD

    open_ap = not password
    if not open_ap and len(password) < 8:
        print("wifi: AP password must be >= 8 chars for WPA2 (or empty for open)")
        return False

    sta = _sta()
    ap = _ap()

    try:
        if sta.isconnected():
            sta.disconnect()
    except OSError:
        pass
    try:
        sta.active(False)
    except Exception as e:
        print("wifi: sta off skip", e)

    if not ap.active():
        try:
            ap.active(True)
        except Exception as e:
            print("wifi: ap on failed", e)
            return False
        time.sleep_ms(400)

    try:
        ap.config(essid=ssid)
        if open_ap:
            ap.config(authmode=network.AUTH_OPEN)
        else:
            ap.config(password=password, authmode=network.AUTH_WPA_WPA2_PSK)
        try:
            ap.config(channel=int(channel))
        except Exception:
            pass
    except Exception as e:
        print("wifi: ap config error", e)
        return False

    time.sleep_ms(800)
    try:
        # gateway + DNS = SoftAP IP so phones hit our captive DNS/HTTP
        ap.ifconfig((AP_IP, "255.255.255.0", AP_IP, AP_IP))
    except Exception as e:
        print("wifi: ap ifconfig skip", e)
    print("wifi: AP active=", ap.active(), ("open" if open_ap else "wpa2"))
    print("wifi: SSID=%s  ch=%s" % (ssid, ap.config("channel")))
    print("wifi: mac=%s  ip=%s" % (bytes(ap.config("mac")).hex(), ap.ifconfig()[0]))
    return ap.active()


def ensure_network(prefer_sta=True):
    """Try home WiFi first; SoftAP if STA fails. Returns ('sta'|'ap'|None, ip)."""
    if prefer_sta and _sta_networks():
        if connect():
            return ("sta", ip())
    if start_ap():
        return ("ap", ip())
    return (None, None)


def ip():
    sta = _sta()
    if sta.active() and sta.isconnected():
        cfg = sta.ifconfig()
        if cfg and cfg[0] != "0.0.0.0":
            return cfg[0]
    ap = _ap()
    if ap.active():
        cfg = ap.ifconfig()
        if cfg and cfg[0] != "0.0.0.0":
            return cfg[0]
    return None


def ifconfig():
    addr = ip()
    if not addr:
        return None
    for iface in (_sta(), _ap()):
        if iface.active():
            cfg = iface.ifconfig()
            if cfg and cfg[0] == addr:
                return cfg
    return None
