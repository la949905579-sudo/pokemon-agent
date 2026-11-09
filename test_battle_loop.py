"""离线测试：battle_loop 的场景分派（不碰游戏）。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import auto_battle
import battle_loop as bl
import switch
import info
import action


def run(scenes, extra=None):
    """按给定场景序列跑 battle_loop，返回 action 调用记录。"""
    seq = iter(scenes)
    calls = []
    rec = lambda name: (lambda *a, **k: calls.append((name,) + a))

    with patch.object(info, "scene", lambda: next(seq, info.MAP)), \
         patch.object(bl, "in_battle", lambda: True), \
         patch.object(action, "choose_option", rec("choose_option")), \
         patch.object(action, "tap_a", lambda: calls.append(("a",))), \
         patch.object(action, "tap_b", lambda: calls.append(("b",))), \
         patch.object(action, "advance_dialog", rec("advance_dialog")), \
         patch.object(action, "open_move_menu", lambda: (calls.append(("open_move",)) or True)), \
         patch.object(action, "use_move", rec("use_move")), \
         patch.object(action, "wait_until", lambda p, t=4.0, s=0.25: True), \
         patch.object(switch, "_pick_and_switch", rec("pick_switch")), \
         patch.object(switch, "active_slot", lambda: 0), \
         patch.object(bl, "my_mon", lambda i: {"slot": 0, "lv": 12, "hp": 31, "mhp": 31,
                                                        "species": 25, "types": ("电",),
                                                        "moves": [98, 0, 0, 0], "pp": [10, 0, 0, 0]}), \
         patch.object(bl, "enemy_info", lambda: {"lv": 10, "hp": 20, "types": ("草",)}), \
         patch.object(bl.decision, "choose_switch", lambda p, e: 2):
        r = auto_battle.battle_loop(max_rounds=len(scenes) + 1, verbose=False)
    return r, calls


r, calls = run([info.BATTLE_INTRO, info.CHOICE, info.MAP])
assert ("choose_option", 0) in calls, calls
print("A choice 场景走「选是」ok", calls)

r, calls = run([info.BATTLE_INTRO, info.PARTY, info.MAP])
assert any(c[0] == "pick_switch" for c in calls), calls
print("B party 场景走换人 ok", calls)

r, calls = run([info.BATTLE_INTRO, info.BATTLE_MAIN, info.ANIM, info.MAP])
assert ("open_move",) in calls, calls
assert any(c[0] == "use_move" for c in calls), calls
print("C 主菜单走「打开招式+出招」ok", calls)

r, calls = run([info.BATTLE_INTRO, info.BATTLE_INTRO, info.MAP])
assert any(c[0] == "advance_dialog" for c in calls), calls
print("D 开场走推进对话 ok", calls)
print("全部通过")
