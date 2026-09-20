# One-shot STA join test (run with mpremote)
from wifi import connect, ip

print("=== STA TEST ===")
ok = connect(timeout_ms=15000)
print("RESULT", ok, "ip", ip())
