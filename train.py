"""练级 + 回合观测：走 battle_loop 的 on_round 回调，不再 monkeypatch。

用法：
  python3 train.py 2 240      # 最多 2 场 / 240 秒
  python3 train.py 3          # 3 场，默认 360 秒
产物：logs/rounds-<时间>.jsonl；控制台打印一致性汇总
"""
import sys
import time

import battle_loop
import encounter
import state
from probe import Recorder


def farm(battles=3, seconds=360, verbose=True):
    import intent
    intent.use_file_store()

    rec = Recorder()
    print("rounds ->", rec.path, flush=True)
    n = 0
    t_end = time.time() + seconds
    try:
        while n < battles and time.time() < t_end:
            if not state.in_battle():
                if not encounter.find_encounter():
                    print("找不到草丛，停", flush=True)
                    break
            res = battle_loop.battle_loop(max_rounds=25, verbose=verbose, on_round=rec)
            n += 1
            print(f"  第{n}场: {res}", flush=True)
            if state.in_battle():
                break
    finally:
        rec.close()
    print("汇总:", rec.summary(), flush=True)
    return rec


if __name__ == "__main__":
    b = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 360
    farm(b, s)
