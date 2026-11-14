"""离线测试：battle_loop 场景分派与关键分支（不碰游戏）。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
from unittest.mock import patch
import auto_battle
import battle_loop as bl
import switch
import info
import action


def mon(slot=0, moves=(98, 0, 0, 0), pp=(10, 0, 0, 0), hp=31, species=25, lv=12):
    return {"slot": slot, "lv": lv, "hp": hp, "mhp": 31, "species": species,
            "types": ("电",), "moves": list(moves), "pp": list(pp)}


def run(scenes, my_mon=None, trapped=False, switch_ok=True, on_round=None, hp_zero=False, enemy_hp=None):
    """按给定场景序列跑 battle_loop，返回 (result, 调用记录)。"""
    seq = iter(scenes)
    calls = []

    def rec(name):
        def f(*a, **k):
            calls.append((name,) + a)
            return switch_ok
        return f

    my_mon = my_mon or (lambda i: mon(i) if i == 0 else None)
    hp = 0 if hp_zero else (20 if enemy_hp is None else enemy_hp)
    enemy = {"lv": 10, "hp": hp, "mhp": 20, "types": ("草",)}

    from contextlib import ExitStack
    with ExitStack() as st:
        st.enter_context(patch.object(info, "scene", lambda: next(seq, info.MAP)))
        st.enter_context(patch.object(bl, "in_battle", lambda: True))
        st.enter_context(patch.object(bl.state, "status_flags", lambda slot=0: {}))
        st.enter_context(patch.object(bl.state, "trapped", lambda: trapped))
        st.enter_context(patch.object(bl.state, "rd", lambda a, n: b"\x00" * n))
        st.enter_context(patch.object(action, "choose_option", lambda *a, **k: calls.append(("choose_option",) + a)))
        st.enter_context(patch.object(action, "tap_a", lambda: calls.append(("a",))))
        st.enter_context(patch.object(action, "tap_b", lambda: calls.append(("b",))))
        st.enter_context(patch.object(action, "advance_dialog", lambda *a, **k: calls.append(("advance_dialog",))))
        st.enter_context(patch.object(action, "open_move_menu", lambda: (calls.append(("open_move",)) or True)))
        st.enter_context(patch.object(action, "close_menu", lambda *a, **k: calls.append(("close_menu",))))
        st.enter_context(patch.object(action, "move_party_cursor", lambda *a, **k: calls.append(("move_party_cursor",) + a)))
        st.enter_context(patch.object(action, "use_move", lambda *a, **k: (calls.append(("use_move",) + a) or True)))
        st.enter_context(patch.object(action, "wait_until", lambda p, t=4.0, s=0.25: True))
        st.enter_context(patch.object(action, "run_away", lambda: calls.append(("run_away",))))
        st.enter_context(patch.object(switch, "_pick_and_switch", rec("pick_switch")))
        st.enter_context(patch.object(switch, "switch_from_main", rec("switch_from_main")))
        st.enter_context(patch.object(switch, "active_slot", lambda: 0))
        st.enter_context(patch.object(switch, "ensure_active", lambda: calls.append(("ensure_active",))))
        st.enter_context(patch.object(switch, "switch_blocked", lambda: False))
        st.enter_context(patch.object(bl, "my_mon", my_mon))
        st.enter_context(patch.object(bl, "enemy_info", lambda: dict(enemy)))
        st.enter_context(patch.object(bl, "wait_round_end", lambda *a, **k: "ready"))
        st.enter_context(patch.object(bl.decision, "choose_switch", lambda p, e, **k: (p[0]["slot"] if p else None)))
        st.enter_context(patch.object(bl.decision, "should_switch_opening", lambda *a, **k: None))
        st.enter_context(patch.object(bl.decision, "should_switch", lambda *a, **k: None))
        st.enter_context(patch.object(bl.decision, "should_flee", lambda *a, **k: False))
        r = auto_battle.battle_loop(max_rounds=len(scenes) + 1, verbose=False,
                                    on_round=on_round)
    return r, calls


# ---- A/B/C/D：场景分派 ----
r, calls = run([info.BATTLE_INTRO, info.CHOICE, info.MAP])
assert ("choose_option", 0) in calls, calls
print("A choice 场景走「选是」ok")

r, calls = run([info.BATTLE_INTRO, info.PARTY, info.MAP])
assert any(c[0] == "pick_switch" for c in calls), calls
print("B party 场景走换人 ok")

r, calls = run([info.BATTLE_INTRO, info.BATTLE_MAIN, info.ANIM, info.MAP])
assert ("open_move",) in calls and any(c[0] == "use_move" for c in calls), calls
print("C 主菜单走「打开招式+出招」ok")

r, calls = run([info.BATTLE_INTRO, info.BATTLE_INTRO, info.MAP])
assert any(c[0] == "advance_dialog" for c in calls), calls
print("D 开场走推进对话 ok")

# ---- E：无攻击招 -> 换人，不硬出招 ----
charizard = lambda i: mon(i, moves=(104, 45, 39, 86), pp=(10, 10, 10, 10)) if i == 0 \
    else (mon(i, moves=(98, 0, 0, 0), pp=(10, 0, 0, 0)) if i == 1 else None)
r, calls = run([info.BATTLE_INTRO, info.BATTLE_MAIN, info.MAP], my_mon=charizard)
assert any(c[0] == "switch_from_main" for c in calls), calls
assert not any(c[0] == "use_move" for c in calls), calls
print("E 无攻击招 -> 换人 ok")

# ---- F：束缚(bit8) -> 不换人 ----
r, calls = run([info.BATTLE_INTRO, info.BATTLE_MAIN, info.MAP], my_mon=charizard,
               trapped=True)
assert not any(c[0] == "switch_from_main" for c in calls), calls
print("F 束缚时不换人 ok")

# ---- G：濒死换人后 ensure_active ----
def faint_team(i):
    if i == 0:
        return mon(0, hp=0)
    if i == 1:
        return mon(1, hp=20)
    return None

r, calls = run([info.BATTLE_INTRO, info.PARTY_OPTION, info.MAP], my_mon=faint_team)
assert ("ensure_active",) in calls, calls
print("G 濒死换人后校正槽位 ok")

# ---- H：敌方 0 血推进有上限 ----
r, calls = run([info.BATTLE_MAIN] * 12, hp_zero=True)
assert r == "stuck", r
assert sum(1 for c in calls if c[0] == "a") >= 8, calls
print("H 敌方 0 血推进上限 ok", r)

# ---- I：on_round 回调收到本回合观测 ----
got = []
r, calls = run([info.BATTLE_INTRO, info.BATTLE_MAIN, info.MAP], on_round=got.append)
assert got and got[0]["idx"] == 0 and got[0]["pp_before"], got
print("I on_round 回调 ok", got[0]["moves"])

# ---- J：轮次用完 -> 退菜单/逃跑兜底 ----
r, calls = run([info.ANIM] * 8)
assert r == "timeout", r
assert ("close_menu",) in calls and ("run_away",) in calls, calls
print("J timeout 兜底恢复 ok", r)

# ---- K：flee 指令直接触发逃跑 ----
import intent as intent_mod
intent_mod.reset()
intent_mod.submit(intent_mod.Intent("flee", {"hp_floor": 0.0}))
r, calls = run([info.BATTLE_INTRO, info.BATTLE_MAIN, info.MAP])
assert any(c[0] == "run_away" for c in calls), calls
intent_mod.reset()
print("K flee 指令触发逃跑 ok")

# ---- L：prolong 指令选变化招 ----
intent_mod.reset()
intent_mod.submit(intent_mod.Intent("prolong", {"hp_floor": 0.0}))
r, calls = run([info.BATTLE_INTRO, info.BATTLE_MAIN, info.MAP],
               my_mon=lambda i: mon(i, moves=(104, 45, 39, 86), pp=(10, 10, 10, 10))
               if i == 0 else None)
um = [c for c in calls if c[0] == "use_move"]
assert um and um[0][1] == 0, calls
intent_mod.reset()
print("L prolong 指令选变化招 ok", um)

# ---- M：no_kill 低血 + 当前只有攻击招 -> 换有变化招的队友 ----
intent_mod.reset()
intent_mod.submit(intent_mod.Intent("no_kill", {"hp_floor": 0.5}))
def nk_team(i):
    if i == 0:
        return mon(0, moves=(98, 0, 0, 0), pp=(10, 0, 0, 0))
    if i == 1:
        return mon(1, moves=(104, 0, 0, 0), pp=(10, 0, 0, 0))
    return None
r, calls = run([info.BATTLE_INTRO, info.BATTLE_MAIN, info.MAP], my_mon=nk_team, enemy_hp=5)
assert any(c[0] == "switch_from_main" for c in calls), calls
intent_mod.reset()
print("M no_kill 无变化招 -> 换人 ok")

# ---- N：no_kill 低血但自己有变化招 -> 不换人，直接拖 ----
intent_mod.reset()
intent_mod.submit(intent_mod.Intent("no_kill", {"hp_floor": 0.5}))
r, calls = run([info.BATTLE_INTRO, info.BATTLE_MAIN, info.MAP], enemy_hp=5,
               my_mon=lambda i: mon(i, moves=(104, 0, 0, 0), pp=(10, 0, 0, 0))
               if i == 0 else None)
assert not any(c[0] == "switch_from_main" for c in calls), calls
assert any(c[0] == "use_move" for c in calls), calls
intent_mod.reset()
print("N no_kill 有变化招 -> 原地拖 ok")

print("全部通过")
