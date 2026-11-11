#!/usr/bin/env python3
"""用 NativeEmu 跑某个游戏的自动化。

用法：
    EMU_BACKEND=native python3 run_game.py pokemon_firered
    python3 run_game.py --list
"""
import sys

import emu_bridge
from framework import loader
from framework.runner import Runner


def push_status(status):
    """把插件状态推给下屏（status 命令）。"""
    import json
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", 55401), timeout=2)
        s.sendall(("status " + json.dumps(status, ensure_ascii=False) + "\n").encode())
        s.recv(64)
        s.close()
    except Exception:
        pass


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-l", "--list"):
        print("可用插件:", ", ".join(loader.available()) or "(无)")
        return
    game_id = args[0]
    plugin = loader.load(game_id)
    plugin.attach(emu_bridge)
    print("插件:", plugin.display_name, "(", plugin.game_id, ")")
    print("Ctrl-C 停止")
    runner = Runner(plugin, emu_bridge, push=push_status, interval=0.15)
    try:
        runner.run()
    except KeyboardInterrupt:
        pass
    print("停止，共 %d 轮" % runner.steps)


if __name__ == "__main__":
    main()
