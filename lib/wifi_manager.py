# lib/wifi_manager.py
# SoftAP captive portal — blocking accept.
# On Save: write wifi.json, stop AP, join STA (leave SoftAP mode).

import gc
import socket
import time

from wifi import start_ap, stop_ap, scan_for, connect, AP_IP, ip
from wifi_cfg import save

try:
    from secrets import AP_SSID, AP_PASSWORD, MDNS_HOSTNAME
except ImportError:
    AP_SSID = "charlie"
    AP_PASSWORD = ""
    MDNS_HOSTNAME = "charlie"

_AP_IP_BYTES = bytes(int(x) for x in AP_IP.split("."))


def _b2s(b):
    try:
        return b.decode()
    except Exception:
        try:
            return b.decode("utf-8")
        except Exception:
            return str(b)


def _urldecode(s):
    if not s:
        return ""
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "+":
            out.append(" ")
            i += 1
        elif c == "%" and i + 2 < n:
            try:
                out.append(chr(int(s[i + 1 : i + 3], 16)))
            except ValueError:
                out.append(c)
            i += 3
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _parse_form(body):
    fields = {}
    for part in body.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            fields[_urldecode(k)] = _urldecode(v)
    return fields


def _dns_reply(req):
    if len(req) < 12:
        return None
    tid = req[0:2]
    i = 12
    while i < len(req):
        length = req[i]
        if length == 0:
            i += 1
            break
        if (length & 0xC0) == 0xC0:
            i += 2
            break
        i += 1 + length
        if i > len(req):
            return None
    i += 4
    if i > len(req):
        return None
    question = req[12:i]
    hdr = tid + b"\x81\x80" + b"\x00\x01\x00\x01\x00\x00\x00\x00"
    ans = b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04" + _AP_IP_BYTES
    return hdr + question + ans


def _scan_options():
    rows = scan_for()
    opts = []
    seen = set()
    for name, _b, _ch, rssi, sec in rows[:24]:
        if not name or name in seen:
            continue
        seen.add(name)
        lock = "" if sec == 0 else " *"
        opts.append((name, "%s (%ddBm)%s" % (name, rssi, lock)))
    return opts


def _page(msg="", selected="", options=None):
    if options is None:
        options = []
    opts_html = ['<option value="">-- type SSID below --</option>']
    for val, label in options:
        sel = " selected" if val == selected else ""
        safe = val.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
        lab = label.replace("&", "&amp;").replace("<", "&lt;")
        opts_html.append('<option value="%s"%s>%s</option>' % (safe, sel, lab))
    banner = ('<p class="msg">%s</p>' % msg) if msg else ""
    return """<!DOCTYPE html>
<html><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>CHARLIE WiFi</title>
<style>
body{font-family:system-ui,sans-serif;margin:1.5rem;background:#0f1419;color:#e7ecf1}
h1{font-size:1.4rem;margin:0 0 .25rem}
.sub{opacity:.7;margin:0 0 1.25rem;font-size:.9rem}
label{display:block;margin:.75rem 0 .25rem;font-size:.85rem;opacity:.85}
input,select,button{width:100%%;box-sizing:border-box;padding:.65rem;border-radius:8px;
border:1px solid #334;background:#1a222c;color:#e7ecf1;font-size:1rem}
button{margin-top:1.1rem;background:#3d8bfd;border:none;font-weight:600}
.msg{background:#1e3a2f;padding:.6rem .8rem;border-radius:8px}
</style></head><body>
<h1>CHARLIE WiFi Setup</h1>
<p class="sub">SoftAP <b>charlie</b> · http://192.168.4.1/</p>
%s
<form method="POST" action="/save">
<label>Network (scanned)</label>
<select name="ssid_sel" id="ssid_sel">%s</select>
<label>Or type SSID</label>
<input name="ssid" id="ssid" placeholder="WiFi name" value="%s"/>
<label>Password</label>
<input name="password" type="password" placeholder="leave blank if open"/>
<button type="submit">Save &amp; Connect</button>
</form>
<script>
document.getElementById('ssid_sel').onchange=function(){
  if(this.value) document.getElementById('ssid').value=this.value;
};
</script>
</body></html>
""" % (
        banner,
        "\n".join(opts_html),
        selected.replace("&", "&amp;").replace('"', "&quot;"),
    )


def _http_response(status, body):
    if isinstance(body, str):
        body = body.encode()
    return (
        "HTTP/1.0 %s\r\nContent-Type: text/html; charset=utf-8\r\n"
        "Content-Length: %d\r\nConnection: close\r\nCache-Control: no-cache\r\n\r\n"
        % (status, len(body))
    ).encode() + body


def _redirect():
    loc = "http://%s/" % AP_IP
    body = b"<a href='%s'>CHARLIE</a>" % loc.encode()
    return (
        "HTTP/1.0 302 Found\r\nLocation: %s\r\nContent-Length: %d\r\n"
        "Connection: close\r\n\r\n" % (loc, len(body))
    ).encode() + body


def _clip16(s):
    s = str(s or "")
    return s if len(s) <= 16 else s[:15] + "~"


def _leave_portal_and_connect(ssid, password, servers):
    """Close portal, stop SoftAP, join STA. Returns 'ok' or 'fail'."""
    import webrepl

    try:
        from oled_status import show, show_msg
    except Exception:
        show = None
        show_msg = None

    if show_msg:
        show_msg("Leaving AP", "Joining", _clip16(ssid))

    if servers:
        for s in servers:
            if s:
                try:
                    s.close()
                except OSError:
                    pass
        time.sleep_ms(200)

    stop_ap()
    time.sleep_ms(500)

    print("wifi_manager: STA connect %r" % ssid)
    ok = connect(ssid, password, timeout_ms=22000)
    if ok:
        try:
            from secrets import WEBREPL_PASSWORD
        except ImportError:
            WEBREPL_PASSWORD = "charlie"
        try:
            webrepl.start(password=WEBREPL_PASSWORD)
        except Exception as e:
            print("wifi_manager: webrepl", e)
        if show:
            show(msg="linked")
        print("wifi_manager: STA ok — SoftAP off")
        while True:
            time.sleep(8)
            if show:
                show(msg="linked")
    if show_msg:
        show_msg("STA failed", _clip16(ssid), "retry portal")
    print("wifi_manager: STA failed")
    return "fail"


def _handle_http(conn, options, servers=None):
    """Returns None | 'ok' | 'fail'."""
    try:
        conn.settimeout(3)
        req = b""
        while b"\r\n\r\n" not in req and len(req) < 4096:
            chunk = conn.recv(512)
            if not chunk:
                break
            req += chunk
        if not req:
            return None

        line = _b2s(req.split(b"\r\n", 1)[0])
        parts = line.split(" ")
        method = parts[0] if parts else "GET"
        path = parts[1] if len(parts) > 1 else "/"
        print("wifi_manager: %s %s" % (method, path))

        if method == "GET" and path not in ("/", "/save"):
            conn.send(_redirect())
            return None

        if method == "POST" and path.startswith("/save"):
            header, _, body = req.partition(b"\r\n\r\n")
            cl = 0
            for hl in _b2s(header).split("\r\n"):
                if hl.lower().startswith("content-length:"):
                    try:
                        cl = int(hl.split(":", 1)[1].strip())
                    except ValueError:
                        cl = 0
            while len(body) < cl:
                body += conn.recv(512)
            fields = _parse_form(_b2s(body))
            ssid = (fields.get("ssid") or "").strip()
            if not ssid:
                ssid = (fields.get("ssid_sel") or "").strip()
            password = fields.get("password") or ""
            print("wifi_manager: form ssid=%r pass_len=%d keys=%s" % (ssid, len(password), list(fields.keys())))

            if not ssid:
                conn.send(
                    _http_response(
                        "400 Bad Request",
                        _page("Pick or type an SSID.", "", options),
                    )
                )
                return None
            if not save(ssid, password):
                conn.send(
                    _http_response(
                        "500 Error",
                        _page("Save failed — try again.", ssid, options),
                    )
                )
                return None

            conn.send(
                _http_response(
                    "200 OK",
                    _page(
                        "Saved <b>%s</b>. Connecting…" % ssid.replace("<", ""),
                        ssid,
                        options,
                    ),
                )
            )
            try:
                conn.close()
            except OSError:
                pass
            return _leave_portal_and_connect(ssid, password, servers)

        conn.send(_http_response("200 OK", _page("", "", options)))
        return None
    except Exception as e:
        print("wifi_manager: http", e)
        return None
    finally:
        try:
            conn.close()
        except OSError:
            pass


def _poll_dns(dns):
    if not dns:
        return
    try:
        data, addr_from = dns.recvfrom(512)
    except OSError:
        return
    reply = _dns_reply(data)
    if reply:
        try:
            dns.sendto(reply, addr_from)
        except OSError:
            pass


def run_portal(timeout_s=None):
    """SoftAP portal. On Save & Connect: stop AP and join STA."""
    import network

    try:
        network.hostname(MDNS_HOSTNAME)
    except Exception:
        pass

    print("wifi_manager: scanning...")
    try:
        from oled_status import show, show_msg

        show_msg("Scanning WiFi", "please wait")
    except Exception:
        show = None
        show_msg = None

    try:
        options = _scan_options()
    except Exception as e:
        print("wifi_manager: scan skip", e)
        options = []
    print("wifi_manager: %d SSIDs" % len(options))

    while True:
        if not start_ap(AP_SSID, AP_PASSWORD or None):
            print("wifi_manager: SoftAP failed")
            if show_msg:
                show_msg("AP failed")
            return False

        addr = ip() or AP_IP
        print("wifi_manager: SoftAP %r http://%s/" % (AP_SSID, addr))
        if show:
            show(msg="portal ready")

        dns = None
        try:
            dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            dns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            dns.bind(("0.0.0.0", 53))
            dns.settimeout(0.01)
        except Exception as e:
            print("wifi_manager: DNS skip", e)

        http = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        http.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        http.bind(("0.0.0.0", 80))
        http.listen(5)
        http.settimeout(0.5)
        print("wifi_manager: HTTP :80")

        t0 = time.ticks_ms()
        last_beat = time.ticks_ms()
        reopen = False
        try:
            while True:
                if timeout_s is not None:
                    if time.ticks_diff(time.ticks_ms(), t0) > int(timeout_s * 1000):
                        print("wifi_manager: timeout")
                        return False
                if time.ticks_diff(time.ticks_ms(), last_beat) > 5000:
                    print("wifi_manager: wait @ http://%s/" % addr)
                    if show:
                        show(msg="wait phone")
                    last_beat = time.ticks_ms()

                _poll_dns(dns)
                try:
                    conn, caddr = http.accept()
                except OSError:
                    continue
                print("wifi_manager: client", caddr)
                if show:
                    show(msg="phone ok")
                result = _handle_http(conn, options, servers=(http, dns))
                if result == "ok":
                    return True
                if result == "fail":
                    reopen = True
                    break
                gc.collect()
                if show:
                    show(msg="portal ready")
        finally:
            for s in (dns, http):
                if s:
                    try:
                        s.close()
                    except OSError:
                        pass

        if not reopen:
            return False
        if show_msg:
            show_msg("Retry portal", "join charlie")
        time.sleep_ms(800)
