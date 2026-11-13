"""离线逻辑测试：不碰游戏，mock 内存读取验证换人模块。"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

    with patch.object(action, "rd", fake_rd), \
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

    with patch.object(action, "rd", fake_rd), \
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



import struct


def _patched(species, sp):
    def fake_rd(addr, n):
        return struct.pack("<H", sp)

    def fake_my_mon(slot):
        return {"slot": slot, "species": species[slot]}

    return fake_rd, fake_my_mon


def test_ensure_active_from_field():
    species = {0: 25, 1: 15, 2: 22, 3: 8}
    fake_rd, fake_my_mon = _patched(species, 22)
    with patch.object(auto_battle, "_field", {"t": 0.0, "sp": None, "slot": None}), \
         patch.object(auto_battle, "rd", fake_rd), \
         patch.object(auto_battle, "my_mon", fake_my_mon):
        real = auto_battle.ensure_active()
    assert real == 2, real
    print("F ensure_active 用 species 校正 ok", real)


def test_ensure_active_keeps():
    species = {0: 22, 1: 15}
    fake_rd, fake_my_mon = _patched(species, 22)
    with patch.object(auto_battle, "_field", {"t": 0.0, "sp": None, "slot": None}), \
         patch.object(auto_battle, "rd", fake_rd), \
         patch.object(auto_battle, "my_mon", fake_my_mon):
        real = auto_battle.ensure_active()
    assert real == 0, real
    print("G ensure_active 同 species 返回首下标 ok")


def test_ensure_active_no_mem():
    with patch.object(auto_battle, "_field", {"t": 0.0, "sp": None, "slot": None}), \
         patch.object(auto_battle, "rd", lambda a, n: b""):
        assert auto_battle.ensure_active() is None
    print("H ensure_active 无内存安全 ok")


def test_active_slot_cached():
    species = {0: 25, 1: 15, 2: 22, 3: 8}
    calls = {"n": 0}

    def fake_rd(addr, n):
        calls["n"] += 1
        return struct.pack("<H", 8)

    def fake_my_mon(slot):
        return {"slot": slot, "species": species[slot]}

    with patch.object(auto_battle, "in_battle", lambda: True), \
         patch.object(auto_battle, "_field", {"t": 0.0, "sp": None, "slot": None}), \
         patch.object(auto_battle, "rd", fake_rd), \
         patch.object(auto_battle, "my_mon", fake_my_mon):
        s1 = auto_battle.active_slot()
        s2 = auto_battle.active_slot()
        n_after = calls["n"]
        auto_battle.invalidate_field()
        s3 = auto_battle.active_slot()
    assert s1 == 3 and s2 == 3 and s3 == 3, (s1, s2, s3)
    assert n_after == 1, n_after
    assert calls["n"] == 2, calls
    print("I active_slot 物种驱动+缓存 ok")


def test_active_slot_fallback_no_mem():
    with patch.object(auto_battle, "in_battle", lambda: True), \
         patch.object(auto_battle, "_field", {"t": 0.0, "sp": None, "slot": None}), \
         patch.object(auto_battle, "rd", lambda a, n: b""):
        assert auto_battle.active_slot() == 0
        auto_battle.invalidate_field()
    print("J active_slot 无内存兜底 ok")


test_ensure_active_from_field()
test_ensure_active_keeps()
test_ensure_active_no_mem()
test_active_slot_cached()
test_active_slot_fallback_no_mem()
print("全部通过")
