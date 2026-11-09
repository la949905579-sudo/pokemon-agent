"""离线逻辑测试：不碰游戏，mock 内存读取验证换人模块。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import switch as auto_battle, state, action


def test_move_party_cursor_stepwise():
    """光标 0 -> 1：每一步按完 +1，最终命中。"""
    pos = {"c": 0}
    pressed = []

    def fake_rd(addr, n):
        if addr == 0x0203B0A9:
            return bytes([pos["c"]])
        return b"\0"

    def fake_press(name, dur=0.35):
        pressed.append((name, dur))
        if name == "down":
            pos["c"] += 1
        elif name == "up":
            pos["c"] -= 1

    with patch.object(auto_battle, "_order", [0, 1, 2, 3, 4, 5]), \
         patch.object(action, "rd", fake_rd), \
         patch.object(action, "press", fake_press):
        ok = auto_battle._move_party_cursor(1)
    assert ok and pos["c"] == 1, (ok, pos)
    assert pressed == [("down", 0.08)], pressed
    print("A 单步移动 ok", pressed)


def test_move_party_cursor_overshoot():
    """连发一次跳 2 格（0 -> 2），函数应回退到 1。"""
    pos = {"c": 0}
    pressed = []

    def fake_rd(addr, n):
        return bytes([pos["c"]]) if addr == 0x0203B0A9 else b"\0"

    def fake_press(name, dur=0.35):
        pressed.append(name)
        if name == "down":
            pos["c"] += 2      # 模拟连发
        elif name == "up":
            pos["c"] -= 1

    with patch.object(auto_battle, "_order", [0, 1, 2, 3, 4, 5]), \
         patch.object(action, "rd", fake_rd), \
         patch.object(action, "press", fake_press):
        ok = auto_battle._move_party_cursor(1)
    assert ok and pos["c"] == 1, (ok, pos, pressed)
    print("B 跳格回退 ok", pressed)


def test_move_main_cursor():
    """主菜单 0 -> 2 应按下，2x2 布局。"""
    pos = {"c": 0}
    pressed = []

    def fake_rd(addr, n):
        return bytes([pos["c"]]) if addr == 0x02023FF8 else b"\0"

    def fake_press(name, dur=0.35):
        pressed.append(name)
        if name == "down":
            pos["c"] += 2
        elif name == "up":
            pos["c"] -= 2
        elif name == "right":
            pos["c"] += 1
        elif name == "left":
            pos["c"] -= 1

    with patch.object(action, "rd", fake_rd), \
         patch.object(action, "press", fake_press):
        ok = auto_battle._move_main_cursor(2)
    assert ok and pos["c"] == 2, (ok, pos, pressed)
    print("C 主菜单移动 ok", pressed)


def test_menu_kind_main_with_stale_party_cursor():
    """主菜单 B0A9 残留 1、FF8=0 -> 必须是 main 而不是 party。"""
    mem = {0x0203B0A9: 1, 0x02023FF8: 0}

    def fake_rd(addr, n):
        return bytes([mem.get(addr, 0)])

    with patch.object(state, "in_battle", lambda: True), \
         patch.object(state, "turn_state", lambda: 1), \
         patch.object(state, "rd", fake_rd):
        assert state.menu_kind() == "main", "残留光标导致误判"
    print("D 主菜单不再误判 ok")


def test_menu_kind_party():
    """队伍列表：B0A9=1 且 FF8=2 -> party。"""
    mem = {0x0203B0A9: 1, 0x02023FF8: 2}

    def fake_rd(addr, n):
        return bytes([mem.get(addr, 0)])

    with patch.object(state, "in_battle", lambda: True), \
         patch.object(state, "turn_state", lambda: 1), \
         patch.object(state, "rd", fake_rd):
        assert state.menu_kind() == "party"
    print("E 队伍列表识别 ok")


test_move_party_cursor_stepwise()
test_move_party_cursor_overshoot()
test_move_main_cursor()
test_menu_kind_main_with_stale_party_cursor()
test_menu_kind_party()
print("全部通过")
