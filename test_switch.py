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



def test_ensure_active_resync():
    """濒死换人后 order[0] 指错：按场上 species 把真实槽位挪到最前。"""
    import struct
    species = {0: 25, 1: 15, 2: 22, 3: 8}

    def fake_rd(addr, n):
        return struct.pack("<H", 22)   # 场上是大嘴雀 species 22

    def fake_my_mon(slot):
        return {"slot": slot, "species": species[slot]}

    with patch.object(auto_battle, "_order", [1, 2, 3, 0]), \
         patch.object(auto_battle, "rd", fake_rd), \
         patch.object(auto_battle, "my_mon", fake_my_mon):
        real = auto_battle.ensure_active()
        head = auto_battle.active_slot()
    assert real == 2 and head == 2, (real, head)
    print("F ensure_active 校正 ok", real, head)


def test_ensure_active_keeps_when_ok():
    """场上 species 与 order[0] 一致时不动顺序。"""
    import struct
    species = {0: 25, 1: 15, 2: 22}

    def fake_rd(addr, n):
        return struct.pack("<H", 22)

    def fake_my_mon(slot):
        return {"slot": slot, "species": species[slot]}

    with patch.object(auto_battle, "_order", [2, 1, 0]), \
         patch.object(auto_battle, "rd", fake_rd), \
         patch.object(auto_battle, "my_mon", fake_my_mon):
        real = auto_battle.ensure_active()
        order = list(auto_battle.party_order())
    assert real == 2 and order == [2, 1, 0], (real, order)
    print("G ensure_active 一致不改 ok")


def test_ensure_active_no_mem():
    """读不到内存时返回 None，不改顺序。"""
    with patch.object(auto_battle, "_order", [1, 2]), \
         patch.object(auto_battle, "rd", lambda a, n: b""):
        assert auto_battle.ensure_active() is None
    print("H ensure_active 无内存安全 ok")


test_ensure_active_resync()
test_ensure_active_keeps_when_ok()
test_ensure_active_no_mem()


def test_active_slot_from_species_cached():
    """场上 species 是唯一依据；0.6s 内重复调用不重复读 UDP。"""
    import struct
    species = {0: 25, 1: 15, 2: 22, 3: 8}
    calls = {"n": 0}

    def fake_rd(addr, n):
        calls["n"] += 1
        return struct.pack("<H", 8)   # 卡咪龟

    def fake_my_mon(slot):
        return {"slot": slot, "species": species[slot]}

    with patch.object(auto_battle, "_order", [1, 2, 3]), \
         patch.object(auto_battle, "in_battle", lambda: True), \
         patch.object(auto_battle, "_field", {"t": 0.0, "sp": None, "slot": None}), \
         patch.object(auto_battle, "rd", fake_rd), \
         patch.object(auto_battle, "my_mon", fake_my_mon):
        s1 = auto_battle.active_slot()
        s2 = auto_battle.party_order()[0]
        n_after = calls["n"]
        auto_battle.invalidate_field()
        s3 = auto_battle.active_slot()
    assert s1 == 3 and s2 == 3 and s3 == 3, (s1, s2, s3)
    assert n_after == 1, n_after          # 第二次命中缓存
    assert calls["n"] == 2, calls         # invalidate 后强制重读
    print("I active_slot 物种驱动+缓存 ok")


def test_active_slot_fallback_no_mem():
    """战斗外读不到 species 时退回 order[0]，不抛异常。"""
    with patch.object(auto_battle, "_order", [4, 0, 1]), \
         patch.object(auto_battle, "_field", {"t": 0.0, "sp": None, "slot": None}), \
         patch.object(auto_battle, "rd", lambda a, n: b""):
        assert auto_battle.active_slot() == 4
        auto_battle.invalidate_field()
    print("J active_slot 无内存兜底 ok")


test_active_slot_from_species_cached()
test_active_slot_fallback_no_mem()
print("全部通过")
