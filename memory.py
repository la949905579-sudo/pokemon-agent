"""内存读写基础：UDP 连 RetroArch。"""
import socket, struct, time

HOST, PORT = "127.0.0.1", 55355

def rd(addr, n, retries=2):
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
