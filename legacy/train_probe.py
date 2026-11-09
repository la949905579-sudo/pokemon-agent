"""练级 + 出招采样：记录每回合「决策 idx / 实际招式 / PP 变化 / 敌方出招」。

用 monkeypatch 包住 battle_loop 的三处：
  decision.choose_move  -> 记录决策
  action.use_move       -> 记录出招瞬间内存 0x02023D4C
  battle_loop.wait_round_end -> 期间高频采样 0x02023D4C/0x02023DC4，抓敌方出招

用法：
  python3 train_probe.py 30 2      # 最多 30 秒/场？（N 秒是总时长）场次 2
  python3 train_probe.py 120 3     # 练级 3 场，120 秒上限
产物：logs/move_trace-<时间>.jsonl（每回合一行）+ 控制台汇总
"""
import json
import os
import struct
import sys
import threading
import time

import battle_loop
import decision
import action
import encounter
import info
import state
from bdata import my_mon, enemy_info
import memory

D4C = 0x02023D4C
DC4 = 0x02023DC4
EN_BASE = 0x02023C3C
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

records = []
_trace_path = os.path.join(LOG_DIR, time.strftime("move_trace-%Y%m%d-%H%M%S.jsonl"))


def _u16(addr):
    d = memory.rd(addr, 2)
    return struct.unpack("<H", d)[0] if len(d) == 2 else None


def enemy_moves():
    d = memory.rd(EN_BASE + 0x0C, 8)
    return list(struct.unpack("<4H", d)) if len(d) == 8 else []


def _sampler(seq, stop):
    while not stop.is_set():
        seq.append((_u16(D4C), _u16(DC4), state.turn_state()))
        time.sleep(0.08)


_o_choose = decision.choose_move
_o_use = action.use_move
_o_wait = battle_loop.wait_round_end


def _choose(m, types):
    # 上一条记录补 pp_after（此时已回到玩家回合，PP 已写回）
    if records and "pp_after" not in records[-1]:
        cur = my_mon(records[-1]["slot"]) if records[-1].get("slot") is not None else None
        records[-1]["pp_after"] = (cur or {}).get("pp")
    idx, why = _o_choose(m, types)
    field_sp = _u16(0x02023BE4)
    records.append({
        "t": round(time.time(), 3), "slot": m.get("slot"), "lv": m.get("lv"),
        "moves": list(m.get("moves") or []), "pp_before": list(m.get("pp") or []),
        "idx": idx, "why": why,
        "slot_species": m.get("species"), "field_species": field_sp,
        "slot_ok": field_sp == m.get("species"),
        "foe": {k: (enemy_info() or {}).get(k) for k in ("species", "lv", "hp", "mhp")},
        "foe_moves": enemy_moves(),
    })
    return idx, why


def _use(i):
    r = _o_use(i)
    if records:
        records[-1]["fired"] = r
        records[-1]["d4c_after"] = _u16(D4C)
        records[-1]["dc4_after"] = _u16(DC4)
    return r


def _wait(*a, **k):
    seq = []
    stop = threading.Event()
    th = threading.Thread(target=_sampler, args=(seq, stop), daemon=True)
    th.start()
    try:
        r = _o_wait(*a, **k)
    finally:
        stop.set()
        th.join(0.5)
    if records:
        records[-1]["seq"] = seq
        records[-1]["wait"] = r
    return r


def _install():
    decision.choose_move = _choose
    action.use_move = _use
    battle_loop.wait_round_end = _wait


def _uninstall():
    decision.choose_move = _o_choose
    action.use_move = _o_use
    battle_loop.wait_round_end = _o_wait


def farm(seconds=90, battles=2):
    t_end = time.time() + seconds
    n = 0
    while n < battles and time.time() < t_end:
        if not state.in_battle():
            if not encounter.find_encounter():
                print("找不到草丛", flush=True)
                break
        res = battle_loop.battle_loop(max_rounds=25)
        n += 1
        print(f"  第{n}场结束: {res}", flush=True)
        if state.in_battle():
            break
    return n


def analyze():
    ok = bad = no_pp = 0
    enemy_seen = {}
    for rec in records:
        moves = rec.get("moves") or []
        idx = rec.get("idx")
        ppb, ppa = rec.get("pp_before"), rec.get("pp_after")
        act_pp = None
        if ppb and ppa and len(ppb) == len(ppa):
            diffs = [j for j in range(len(ppb)) if ppb[j] - ppa[j] == 1]
            if len(diffs) == 1:
                act_pp = diffs[0]
        d4c = rec.get("d4c_after")
        act_d4c = moves.index(d4c) if d4c in moves else None
        if act_pp is None:
            no_pp += 1
        if act_pp is not None and act_pp == idx and (act_d4c is None or act_d4c == idx):
            ok += 1
        elif act_pp is not None and act_pp != idx:
            bad += 1
        # 敌方出招：采样序列里 D4C（最近行动招式）不属于我方招式表的 id
        for v, _dc4, _t in rec.get("seq") or []:
            if v and v not in moves:
                enemy_seen[v] = enemy_seen.get(v, 0) + 1
        rec["_act_pp"] = act_pp
        rec["_act_d4c"] = act_d4c
    print(f"回合 {len(records)}：一致 {ok}，不一致 {bad}，PP 无法判定 {no_pp}", flush=True)
    print("槽位不同步回合:", sum(1 for r in records if r.get("slot_ok") is False), flush=True)
    print("敌方实际出招 id:", enemy_seen, flush=True)
    for rec in records:
        print(json.dumps(rec, ensure_ascii=False), flush=True)


def main():
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    battles = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    print("trace ->", _trace_path, flush=True)
    _install()
    try:
        farm(secs, battles)
    finally:
        _uninstall()
        if records and "pp_after" not in records[-1]:
            cur = my_mon(records[-1]["slot"]) if records[-1].get("slot") is not None else None
            records[-1]["pp_after"] = (cur or {}).get("pp")
    analyze()
    with open(_trace_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("saved", _trace_path, flush=True)


if __name__ == "__main__":
    main()
