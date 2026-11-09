"""离线测试：战斗内部队伍顺序 party_order 与光标映射。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import auto_battle
import switch
from unittest.mock import patch as _patch

# 这些用例只测内存里的 order 逻辑，不读实机战斗状态
_patch.object(switch, "in_battle", lambda: False).start()


def set_order(o):
    switch._order = list(o)


def test_cursor_mapping():
    # 左边 #3 卡咪龟，右侧 [#0, #2, #1, #4, #5]
    set_order([3, 0, 2, 1, 4, 5])
    assert switch.active_slot() == 3
    got = {s: switch._cursor_for_slot(s) for s in range(6)}
    assert got == {3: 0, 0: 1, 2: 2, 1: 3, 4: 4, 5: 5}, got
    print("A 光标映射 ok", got)


def test_order_init_from_party():
    """没有记录时按队伍顺序初始化：第一只健康放左边。"""
    with _patch.object(switch, "_order", None), \
         _patch.object(switch, "_init_active", lambda: 1), \
         _patch.object(switch, "my_mon",
                      lambda i: {"hp": 0 if i == 0 else 20, "species": i}):
        o = switch.party_order()
    assert o == [1, 0, 2, 3, 4, 5], o
    print("B 初始化按队伍顺序 ok", o)


def test_swap_after_switch():
    """换人后 order[0] 与选中位置交换（模拟 3 次换人后界面顺序）。"""
    set_order([1, 0, 2, 3, 4, 5])
    # 换到 #3
    pos = switch._cursor_for_slot(3)
    o = switch.party_order(); o[0], o[pos] = o[pos], o[0]
    assert o == [3, 0, 2, 1, 4, 5], o
    # 再换到 #4
    pos = switch._cursor_for_slot(4)
    o[0], o[pos] = o[pos], o[0]
    assert o == [4, 0, 2, 1, 3, 5], o
    # 再换到 #2
    pos = switch._cursor_for_slot(2)
    o[0], o[pos] = o[pos], o[0]
    assert o == [2, 0, 4, 1, 3, 5], o
    print("C 三次交换序列 ok", o)


test_cursor_mapping()
test_order_init_from_party()
test_swap_after_switch()
print("全部通过")
