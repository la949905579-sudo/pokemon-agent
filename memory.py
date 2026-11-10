"""内存读写基础：UDP 连 RetroArch。"""
import socket, struct, time

HOST, PORT = "127.0.0.1", 55355

MAX_CHUNK = 0x1000   # 单次 UDP 读上限（hex 文本约 12KB < 16KB 缓冲）


def rd(addr, n, retries=2):
    if n > MAX_CHUNK:
        out = b""
        for off in range(0, n, MAX_CHUNK):
            m = min(MAX_CHUNK, n - off)
            d = rd(addr + off, m, retries)
            if len(d) != m:
                return out
            out += d
        return out
    for _ in range(retries + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0)); s.settimeout(0.7)
        s.sendto(f"READ_CORE_MEMORY {addr:x} {n}".encode(), (HOST, PORT))
        try:
            r = s.recvfrom(16384)[0].split()
        except Exception:
            s.close(); continue
        s.close()
        if len(r) > 2:
            try:
                return bytes(int(x, 16) for x in r[2:])
            except Exception:
                return b""
        return b""
    return b""
