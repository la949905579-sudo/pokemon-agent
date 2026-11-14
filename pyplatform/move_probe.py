"""战斗出招采集器（只读）。

练级时后台按 10Hz 采样战斗结构，落盘 JSONL，供离线分析：
  - 我方/敌方 BattlePokemon 原始字节
  - turn / 光标 / 场景
  - 队伍 4 招 + PP（bdata.my_mon）

用法：
  python3 move_probe.py 60        # 采样 60 秒
  python3 move_probe.py           # 默认 90 秒
数据：logs/move_probe-<时间>.jsonl
"""
import json
import os
import sys
import threading
import time

import info
import state

MY_BASE = 0x02023BE4
EN_BASE = 0x02023C3C
RAW_N = 0x100
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


class Sampler(threading.Thread):
    def __init__(self, seconds=90, hz=10, path=None):
        super().__init__(daemon=True)
        self.seconds = seconds
        self.interval = 1.0 / hz
        self.path = path or os.path.join(
            LOG_DIR, time.strftime("move_probe-%Y%m%d-%H%M%S.jsonl"))
        self.running = True
        self.count = 0

    def run(self):
        import memory
        from bdata import my_mon
        t_end = time.time() + self.seconds
        prev_turn = None
        f = open(self.path, "w", encoding="utf-8")
        try:
            while self.running and time.time() < t_end:
                rec = {"t": round(time.time(), 3)}
                try:
                    rec["scene"] = info.scene()
                    rec["turn"] = state.turn_state()
                    rec["cur"] = state.cursor()
                    rec["my"] = memory.rd(MY_BASE, RAW_N).hex()
                    rec["en"] = memory.rd(EN_BASE, RAW_N).hex()
                    rec["party"] = [
                        {k: m.get(k) for k in ("slot", "lv", "hp", "mhp", "moves", "pp")}
                        for m in (my_mon(i) for i in range(6)) if m
                    ]
                except Exception as e:  # 采样失败不中断主流程
                    rec["err"] = str(e)
                rec["edge"] = rec.get("turn") != prev_turn
                prev_turn = rec.get("turn")
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                self.count += 1
                time.sleep(self.interval)
        finally:
            f.close()

    def stop(self):
        self.running = False


def main():
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    s = Sampler(secs)
    print("sampling ->", s.path, flush=True)
    s.start()
    s.join()
    print("samples", s.count, flush=True)


if __name__ == "__main__":
    main()
