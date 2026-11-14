"""定向采集：连续使用非攻击招（聚气），逼敌方出招，抓 D4C 序列与敌方招式表。

只做「一场战斗内的手动回合」，不负责遇敌：
  1. 先在草地遇敌（encounter.find_encounter）
  2. 再调 run(rounds=3)

用法：
  python3 probe_enemy.py 3
产物：logs/enemy_trace-<时间>.jsonl
"""
import json
import os
import struct
import sys
import threading
import time

import action
import info
import state
import memory
from bdata import my_mon, enemy_info

D4C = 0x02023D4C
DC4 = 0x02023DC4
EN_BASE = 0x02023C3C
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


def _u16(a):
    d = memory.rd(a, 2)
    return struct.unpack("<H", d)[0] if len(d) == 2 else None


def _enemy_moves():
    d = memory.rd(EN_BASE + 0x0C, 8)
    return list(struct.unpack("<4H", d)) if len(d) == 8 else []


def _sampler(seq, stop):
    while not stop.is_set():
        seq.append((round(time.time(), 3), _u16(D4C), _u16(DC4), state.turn_state()))
        time.sleep(0.06)


def run(rounds=3, prefer=1):
    if not state.in_battle():
        print("不在战斗中", flush=True)
        return
    out = []
    for r in range(rounds):
        if not state.in_battle():
            break
        # 推进到玩家主菜单
        for _ in range(12):
            if info.scene() in (info.BATTLE_MAIN, info.BATTLE_MOVES):
                break
            action.tap_a()
            time.sleep(0.5)
        m = my_mon(1)
        foe = enemy_info()
        rec = {"t": round(time.time(), 3), "round": r, "turn": state.turn_state(),
               "me": {"lv": m and m.get("lv"), "hp": m and m.get("hp"),
                      "moves": m and m.get("moves"), "pp": m and m.get("pp")},
               "foe": foe, "foe_moves": _enemy_moves()}
        seq = []
        stop = threading.Event()
        th = threading.Thread(target=_sampler, args=(seq, stop), daemon=True)
        th.start()
        try:
            if info.scene() == info.BATTLE_MAIN:
                action.open_move_menu()
            idx = prefer
            pp = (m or {}).get("pp") or []
            if len(pp) > idx and pp[idx] <= 0:
                idx = 0
            ok = action.use_move(idx)
            rec["idx"] = idx
            rec["fired"] = ok
            for _ in range(80):
                if not state.in_battle() or state.turn_state() == 1:
                    break
                time.sleep(0.12)
        finally:
            stop.set()
            th.join(0.4)
        rec["seq"] = seq
        rec["pp_after"] = (my_mon(1) or {}).get("pp")
        rec["hp_after"] = (my_mon(1) or {}).get("hp")
        out.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
        if not state.in_battle():
            break
    path = os.path.join(LOG_DIR, time.strftime("enemy_trace-%Y%m%d-%H%M%S.jsonl"))
    with open(path, "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("saved", path, flush=True)
    return out


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    run(n)
