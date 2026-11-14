"""离线测试：action 层的光标/按键动作。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
from unittest.mock import patch
import action


def snap(x=8, y=8, battle=False, dialog=False):
    return {"battle": battle, "dialog": dialog, "turn": 4, "x": x, "y": y,
            "choice": False, "mode": "map"}


def test_move_move_cursor():
    pos = {"c": 0}
    presses = []

    def fake_press(name, dur=0.35):
        presses.append(name)
        if name == "right":
            pos["c"] += 1
        elif name == "left":
            pos["c"] -= 1
        elif name == "down":
            pos["c"] += 2
        elif name == "up":
            pos["c"] -= 2

    with patch.object(action, "read_cursor", lambda a: pos["c"]), \
         patch.object(action, "press", fake_press), \
         patch("time.sleep", lambda s: None):
        ok = action.move_move_cursor(2)
    assert ok and pos["c"] == 2, (ok, pos, presses)
    print("A 招式光标 0->2 ok", presses)


def test_use_move():
    seq = [2, 4, 4]
    it = iter(seq)
    with patch.object(action, "move_move_cursor", lambda i: True), \
         patch.object(action, "read_cursor", lambda a: 1), \
         patch.object(action, "snapshot", lambda: {"turn": next(it, 4), "battle": True}), \
         patch.object(action, "tap_a", lambda: None), \
         patch("time.sleep", lambda s: None):
        assert action.use_move(1) is True
    print("B 出招 ok")


def test_choose_option():
    presses = []
    with patch.object(action, "press", lambda n, d=0.35: presses.append(n)), \
         patch.object(action, "tap_a", lambda: presses.append("a")), \
         patch("time.sleep", lambda s: None):
        action.choose_option(2)
    # 4 次 up 归零 + 2 次 down + 1 次 A
    assert presses.count("up") == 4 and presses.count("down") == 2, presses
    assert presses[-1] == "a"
    print("C 选项定位 ok", presses)


def test_walk_normal():
    presses = []

    def fake_press(name, dur=0.35):
        presses.append((name, dur))

    with patch.object(action, "snapshot", lambda: snap()), \
         patch.object(action, "press", fake_press), \
         patch("time.sleep", lambda s: None):
        moved = action.walk("right", 12)
    # 时长驱动：第一次是按 0.06+0.09*12 的长按；坐标不动时会补按几次
    assert presses[0][0] == "right" and presses[0][1] > 1.0, presses
    print("D 走路分检查点 ok", presses)


def test_walk_overshoot():
    calls = {"n": 0}

    def fake_snapshot():
        calls["n"] += 1
        # 走 1 格后直接报走了 3 格（串格）
        return snap(x=11 if calls["n"] > 1 else 8, y=8)

    presses = []

    def fake_press(name, dur=0.35):
        presses.append((name, dur))

    with patch.object(action, "snapshot", fake_snapshot), \
         patch.object(action, "press", fake_press), \
         patch("time.sleep", lambda s: None):
        moved = action.walk("right", 1)
    # 走多了应该反向按 left 修正（mock 坐标不动，只看有没有反向指令）
    assert any(n == "left" for n, d in presses), presses
    print("E 超走回退 ok", presses)


def test_walk_stop_on_dialog():
    calls = {"n": 0}

    def fake_snapshot():
        calls["n"] += 1
        if calls["n"] > 1:
            return snap(x=14, y=8, dialog=True)
        return snap(x=8, y=8)

    presses = []

    def fake_press(name, dur=0.35):
        presses.append((name, dur))

    with patch.object(action, "snapshot", fake_snapshot), \
         patch.object(action, "press", fake_press), \
         patch("time.sleep", lambda s: None):
        moved = action.walk("right", 12)
    assert moved == 6, moved
    print("F 遇对话立即停 ok", moved)


test_move_move_cursor()
test_use_move()
test_choose_option()
test_walk_normal()
test_walk_overshoot()
test_walk_stop_on_dialog()
print("全部通过")
