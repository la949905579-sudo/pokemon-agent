"""离线测试：info.scene() 的场景映射。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import info


def snap(battle=True, turn=1, choice=False, x=8, y=8):
    return {"mode": "x", "battle": battle, "dialog": battle,
            "choice": choice, "turn": turn, "x": x, "y": y}


def check(s, mk, expect):
    with patch.object(info, "snapshot", lambda: s), \
         patch.object(info, "menu_kind", lambda: mk):
        got = info.scene()
    assert got == expect, (s, mk, got, expect)
    return got


check(snap(battle=False, turn=4), "map", info.MAP)
print("A 地图 ok")
check(snap(turn=0), "start", info.BATTLE_INTRO)
print("B 战斗开场 ok")
check(snap(turn=4), "anim", info.ANIM)
print("C 动画 ok")
check(snap(turn=1, choice=True), "main", info.CHOICE)
print("D 是/否选项框 ok")
check(snap(turn=1, choice=False), "party", info.PARTY)
print("E 队伍列表 ok")
check(snap(turn=1, choice=False), "main", info.BATTLE_MAIN)
print("F 战斗主菜单 ok")
check(snap(turn=2, choice=False), "moves", info.BATTLE_MOVES)
print("G 招式菜单 ok")
check(snap(turn=2, choice=True), "party", info.PARTY_OPTION)
print("H 放出/概况菜单 ok")


def test_context():
    with patch.object(info, "snapshot", lambda: snap(turn=1)), \
         patch.object(info, "menu_kind", lambda: "main"), \
         patch.object(info, "cursor", lambda: 0), \
         patch.object(info, "party_cursor", lambda: 7):
        ctx = info.context()
    assert ctx["scene"] == info.BATTLE_MAIN
    assert ctx["main_cursor"] == 0 and ctx["party_cursor"] == 7
    print("I context 带光标 ok", ctx)


test_context()
print("全部通过")
