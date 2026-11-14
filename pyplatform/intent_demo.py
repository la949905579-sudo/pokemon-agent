"""实机演示：遇敌后注入指令，观察决策变化（默认 3 回合）。

用法：python3 intent_demo.py [prolong|no_kill|flee|only_class]
"""
import sys

import time

import action
import battle_loop
import encounter
import info
import intent
import state

kind = sys.argv[1] if len(sys.argv) > 1 else "prolong"
if not state.in_battle():
    if not encounter.find_encounter():
        print("找不到草丛")
        raise SystemExit(1)
# 先推进开场对话到主菜单，否则前几轮都在按 A
for _ in range(12):
    if info.scene() in (info.BATTLE_MAIN, info.BATTLE_MOVES):
        break
    action.tap_a()
    time.sleep(0.7)
intent.submit(intent.Intent(kind, {"hp_floor": 0.0}, ttl=3, source="demo"))
print("注入", kind, "->", [i.kind for i in intent.active()], flush=True)
r = battle_loop.battle_loop(max_rounds=15, verbose=True)
print("结果", r, flush=True)
print("audit:", intent.audit()[-6:], flush=True)
