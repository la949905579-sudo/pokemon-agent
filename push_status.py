#!/usr/bin/env python3
"""把游戏状态推送给 NativeEmu 的下屏（TCP 桥 status 命令）。

用法：
    EMU_BACKEND=native python3 push_status.py
"""
import json
import socket
import time

from framework import loader

HOST, PORT = "127.0.0.1", 55401

_plugin = None


def plugin():
    global _plugin
    if _plugin is None:
        _plugin = loader.load("pokemon_firered")
    return _plugin


def build_status():
    return plugin().status()


def _legacy_build_status():
    import info, state
    ctx = info.context()
    scene = str(ctx.get("scene", ""))
    battle = ""
    if "battle" in scene.lower():
        battle = scene
    team = []
    try:
        _, lvs = state.party()
        for i, (lv, hp, mhp) in enumerate(lvs or []):
            if lv > 0:
                team.append({"name": "#%d" % (i + 1), "lv": lv, "hp": hp, "max": mhp})
    except Exception:
        team = []
    return {
        "map": scene,
        "x": int(ctx.get("x", 0) or 0),
        "y": int(ctx.get("y", 0) or 0),
        "battle": battle,
        "team": team,
    }


def push(payload):
    s = socket.create_connection((HOST, PORT), timeout=3)
    try:
        s.sendall(("status " + json.dumps(payload, ensure_ascii=False) + "\n").encode())
        s.recv(64)
    finally:
        s.close()


def main():
    print("pushing status to %s:%d (Ctrl-C 停止)" % (HOST, PORT))
    while True:
        try:
            push(build_status())
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("push fail:", e)
        time.sleep(1)


if __name__ == "__main__":
    main()
