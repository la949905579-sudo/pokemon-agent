"""离线测试：_pick_and_switch 成功才交换内部顺序。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import switch
import action


def test_switch_ok():
    order = [1, 0, 2, 3, 4, 5]
    with patch.object(switch, "_cursor_for_slot", lambda t: 2), \
         patch.object(action, "pick_and_switch", lambda pos: True), \
         patch.object(switch, "party_order", lambda: order):
        ok = switch._pick_and_switch(3, False, "t")
    assert ok and order == [2, 0, 1, 3, 4, 5], (ok, order)
    print("A 成功换人交换顺序 ok", order)


def test_switch_fail():
    order = [1, 0, 2, 3, 4, 5]
    with patch.object(switch, "_cursor_for_slot", lambda t: 2), \
         patch.object(action, "pick_and_switch", lambda pos: False), \
         patch.object(switch, "party_order", lambda: order):
        ok = switch._pick_and_switch(3, False, "t")
    assert not ok and order == [1, 0, 2, 3, 4, 5], (ok, order)
    print("B 失败不交换 ok")


test_switch_ok()
test_switch_fail()
print("全部通过")
