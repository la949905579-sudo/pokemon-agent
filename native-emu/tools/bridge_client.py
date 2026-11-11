#!/usr/bin/env python3
"""NativeEmu TCP 桥的 Python 客户端（默认 127.0.0.1:55401）。

用法：
    python3 bridge_client.py ping
    python3 bridge_client.py read 0202C000 4
    python3 bridge_client.py press 1 100      # 1 = A
    python3 bridge_client.py frame

键位（与 EmuCore 一致）：A=1<<0, B=1<<1, SELECT=1<<2, START=1<<3,
RIGHT=1<<4, LEFT=1<<5, UP=1<<6, DOWN=1<<7, R=1<<8, L=1<<9
"""
import socket
import sys


class Bridge:
    def __init__(self, host="127.0.0.1", port=55401, timeout=5):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.f = self.sock.makefile("rwb")

    def cmd(self, line):
        self.f.write((line + "\n").encode())
        self.f.flush()
        return self.f.readline().decode().strip()

    def read(self, addr, n):
        r = self.cmd(f"read {addr:x} {n}")
        if not r.startswith("ok "):
            raise RuntimeError(r)
        return bytes.fromhex(r[3:])

    def write(self, addr, data):
        return self.cmd(f"write {addr:x} {data.hex()}")

    def press(self, mask, ms=80):
        return self.cmd(f"press {mask} {ms}")

    def frame(self):
        return self.cmd("frame")

    def close(self):
        try:
            self.cmd("quit")
            self.sock.close()
        except Exception:
            pass


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    b = Bridge()
    try:
        print(b.cmd(" ".join(sys.argv[1:])))
    finally:
        b.close()


if __name__ == "__main__":
    main()
