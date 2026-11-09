"""战斗回合观测：订阅 battle_loop(on_round=...) 写 JSONL，并汇总一致性。"""
import json
import os
import time

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


class Recorder:
    """可调用对象：battle_loop 每回合把观测 dict 交进来。"""

    def __init__(self, path=None):
        self.path = path or os.path.join(
            LOG_DIR, time.strftime("rounds-%Y%m%d-%H%M%S.jsonl"))
        self.f = open(self.path, "w", encoding="utf-8")
        self.rows = []

    def __call__(self, rec):
        self.rows.append(rec)
        self.f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.f.flush()

    def close(self):
        try:
            self.f.close()
        except Exception:
            pass

    def summary(self):
        """PP 差反推实际出招，对比决策 idx；统计槽位不同步。"""
        ok = bad = nop = 0
        for r in self.rows:
            ppb, ppa = r.get("pp_before") or [], r.get("pp_after") or []
            act = None
            if ppb and ppa and len(ppb) == len(ppa):
                d = [i for i in range(len(ppb)) if ppb[i] - ppa[i] == 1]
                act = d[0] if len(d) == 1 else None
            if act is None:
                nop += 1
            elif act == r.get("idx"):
                ok += 1
            else:
                bad += 1
        return {
            "rounds": len(self.rows), "match": ok, "mismatch": bad,
            "no_pp": nop,
            "slot_mismatch": sum(1 for r in self.rows if r.get("slot_ok") is False),
        }
