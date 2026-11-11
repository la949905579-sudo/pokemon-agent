"""原生模拟器（NativeEmu）TCP 桥客户端。

替代 memory.py 的 UDP(55355) / ra.py 的 UDP(55400)，接口保持兼容：
    rd(addr, n) -> bytes
    wr(addr, data)
    press(name, dur=0.35)

协议见 native-emu/app/src/main/java/com/dsh/emu/BridgeServer.kt。
"""
import socket
import threading

HOST, PORT = "127.0.0.1", 55401

KEYS = {
    "A": 1 << 0, "B": 1 << 1, "SELECT": 1 << 2, "START": 1 << 3,
    "RIGHT": 1 << 4, "LEFT": 1 << 5, "UP": 1 << 6, "DOWN": 1 << 7,
    "R": 1 << 8, "L": 1 << 9,
}

_lock = threading.Lock()
_conn = None


def _connect():
    global _conn
    if _conn is None:
        _conn = socket.create_connection((HOST, PORT), timeout=5)
        _conn.settimeout(10)
    return _conn


def _cmd(line):
    global _conn
    with _lock:
        try:
            s = _connect()
            s.sendall((line + "\n").encode())
            buf = b""
            while not buf.endswith(b"\n"):
                chunk = s.recv(4096)
                if not chunk:
                    raise ConnectionError("bridge closed")
                buf += chunk
            return buf.decode().strip()
        except Exception:
            try:
                if _conn:
                    _conn.close()
            except Exception:
                pass
            _conn = None
            raise


def rd(addr, n, retries=2):
    last = None
    for _ in range(retries + 1):
        try:
            r = _cmd("read %x %d" % (addr, n))
            if not r.startswith("ok "):
                raise RuntimeError(r)
            data = bytes.fromhex(r[3:])
            if len(data) < n:
                raise RuntimeError("short read %d/%d" % (len(data), n))
            return data[:n]
        except Exception as e:
            last = e
    raise last


def wr(addr, data):
    r = _cmd("write %x %s" % (addr, bytes(data).hex()))
    if r != "ok":
        raise RuntimeError(r)


def press(name, dur=0.35):
    """name: 'A' / 'UP' 或它们的组合，如 'UP+A'。"""
    mask = 0
    for part in str(name).replace(" ", "").split("+"):
        if not part:
            continue
        key = part.upper()
        if key not in KEYS:
            raise ValueError("unknown key: %s" % part)
        mask |= KEYS[key]
    if not mask:
        raise ValueError("empty key")
    r = _cmd("press %d %d" % (mask, max(1, int(dur * 1000))))
    if r != "ok":
        raise RuntimeError(r)


def frame():
    r = _cmd("frame")
    return int(r[3:]) if r.startswith("ok ") else -1


def ping():
    return _cmd("ping") == "pong"
