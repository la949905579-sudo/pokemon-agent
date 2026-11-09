"""自动练级：遇敌 -> battle_loop -> 记录，达到目标等级/场数/时间就停。

用法：
  python3 farm.py 10          # 最多 10 场
  python3 farm.py 10 20       # 最多 10 场，全队 Lv20 停
  python3 farm.py 10 20 1800  # 再加 1800 秒上限
"""
import sys
import time

import battle_loop
import encounter
import state
from bdata import my_mon
from probe import Recorder


def levels():
    return [m["lv"] for m in (my_mon(i) for i in range(6)) if m]


def low_hp(ratio=0.3):
    """全队没有一只能打的（都要低于 30%）才需要回中心。"""
    ms = [m for m in (my_mon(i) for i in range(6)) if m and m["hp"] > 0]
    if not ms:
        return True
    return max(m["hp"] / m["mhp"] for m in ms) < ratio


def farm(battles=10, target_lv=None, seconds=1800, verbose=True):
    import intent
    intent.use_file_store()

    rec = Recorder()
    start = levels()
    n = 0
    t_end = time.time() + seconds
    while n < battles and time.time() < t_end:
        if target_lv and min(levels()) >= target_lv:
            print("达到目标等级", levels(), flush=True)
            break
        if low_hp():
            print("全队血少，需要回精灵中心", levels(), flush=True)
            break
        if not state.in_battle():
            if not encounter.find_encounter():
                print("找不到草丛，停", flush=True)
                break
        res = battle_loop.battle_loop(max_rounds=25, verbose=verbose, on_round=rec)
        n += 1
        print(f"  第{n}场: {res}  等级 {levels()}", flush=True)
        if state.in_battle():
            break
    rec.close()
    print("汇总:", rec.summary(), flush=True)
    print("等级:", start, "->", levels(), flush=True)
    return rec


if __name__ == "__main__":
    b = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    lv = int(sys.argv[2]) if len(sys.argv) > 2 else None
    sec = int(sys.argv[3]) if len(sys.argv) > 3 else 1800
    farm(b, lv, sec)
