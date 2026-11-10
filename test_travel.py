"""离线测试：统一状态快照 + 寻路战斗/对话检测 + travel 组合。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import pathfind
import action
import auto_battle


def snap(battle=False, dialog=False, x=8, y=8, turn=4):
    return {"battle": battle, "dialog": dialog, "turn": turn,
            "x": x, "y": y, "mode": "map" if not battle else "battle"}


def test_goto_battle_at_start():
    with patch.object(pathfind, "snapshot", lambda: snap(battle=True)):
        r = pathfind.goto(10, 10)
    assert r == "battle", r
    print("A 开局即战斗 -> battle ok")


def test_goto_dialog_at_start():
    with patch.object(pathfind, "snapshot", lambda: snap(dialog=True)):
        r = pathfind.goto(10, 10)
    assert r == "dialog", r
    print("B 开局有对话 -> dialog ok")


def test_goto_battle_after_segment():
    calls = {"n": 0}

    def fake_snapshot():
        calls["n"] += 1
        return snap(battle=calls["n"] >= 2)

    with patch.object(pathfind, "snapshot", fake_snapshot), \
         patch.object(pathfind, "terrain") as terr, \
         patch.object(pathfind.nav, "bfs", lambda *a, **k: ["right"]), \
         patch.object(pathfind, "walk_segment", lambda d, n: 1), \
         patch.object(pathfind, "press", lambda *a, **k: None):
        terr.load.return_value = (0, 20, 20, [0] * 400)
        terr.is_grass.return_value = False
        terr.npc_tiles.return_value = set()
        r = pathfind.goto(14, 10)
    assert r == "battle", r
    print("C 段中遇敌 -> battle ok")


def test_walk_segment_stops_on_battle():
    """走 12 格，第一个检查点后发现战斗 -> 立即停，返回已走格数。"""
    seq = [snap(x=8, y=8), snap(battle=True, x=14, y=8)]
    it = iter(seq)
    seen = []

    def fake_press(name, dur=0.35):
        seen.append((name, dur))

    with patch.object(action, "snapshot", lambda: next(it, seq[-1])), \
         patch.object(pathfind.info, "facing", lambda: "right"), \
         patch.object(action, "press", fake_press):
        moved = pathfind.walk_segment("right", 12)
    assert seen and seen[0][0] == "right" and seen[0][1] > 0.5, seen  # 先长按
    print("D 行走途中遇战立即停 ok, moved =", moved)


def test_walk_segment_long_but_clear():
    """一路无战斗时能走完全程。"""
    seq = [snap(x=8, y=8), snap(x=32, y=8)]   # 长按直接走完 24 格
    it = iter(seq)
    with patch.object(action, "snapshot", lambda: next(it, snap(x=32, y=8))), \
         patch.object(pathfind.info, "facing", lambda: "right"), \
         patch.object(action, "press", lambda *a, **k: None):
        moved = pathfind.walk_segment("right", 24)
    assert moved == 24, moved
    print("E 无干扰走完全程 ok, moved =", moved)


def test_travel_auto_battle():
    st = {"battle": False, "fought": 0, "calls": 0}

    def fake_goto(x, y, avoid_grass=True):
        st["calls"] += 1
        if st["calls"] == 1:
            st["battle"] = True
            return "battle"
        return True

    def fake_battle():
        st["fought"] += 1
        st["battle"] = False

    with patch.object(pathfind, "in_battle", lambda: st["battle"]), \
         patch.object(pathfind.terrain, "_map_hdr", lambda: 0x1111), \
         patch.object(pathfind.terrain, "load", lambda: (0x1111, 20, 20, [0] * 400)), \
         patch.object(pathfind, "_leave_grass", lambda: None), \
         patch.object(pathfind, "goto", fake_goto), \
         patch.object(auto_battle, "battle_loop", fake_battle):
        r = pathfind.travel(10, 10, max_battles=2)
    assert r == "ok", r
    assert st["fought"] == 1, st
    print("F travel 遇敌自动战斗并继续 ok")


def test_travel_warped():
    st = {"hdr": 0x1111}

    def fake_goto(x, y, avoid_grass=True):
        st["hdr"] = 0x2222
        return False

    with patch.object(pathfind, "in_battle", lambda: False), \
         patch.object(pathfind.terrain, "_map_hdr", lambda: st["hdr"]), \
         patch.object(pathfind.terrain, "load", lambda: (0x1111, 20, 20, [0] * 400)), \
         patch.object(pathfind, "goto", fake_goto):
        r = pathfind.travel(10, 10)
    assert r == "warped", r
    print("G 换图 -> warped ok")


test_goto_battle_at_start()
test_goto_dialog_at_start()
test_goto_battle_after_segment()
test_walk_segment_stops_on_battle()
test_walk_segment_long_but_clear()
test_travel_auto_battle()
test_travel_warped()
print("全部通过")
