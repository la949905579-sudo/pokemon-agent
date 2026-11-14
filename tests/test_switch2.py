"""离线测试：_pick_and_switch 成功才 invalidate，不维护第二份顺序。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
from unittest.mock import patch
import switch
import action
import state


def test_switch_ok():
    calls = []
    with patch.object(switch, "_cursor_for_species", lambda sp: 2), \
         patch.object(action, "pick_and_switch", lambda pos: (calls.append(pos) or True)), \
         patch.object(switch, "invalidate_field", lambda: calls.append("inv")), \
         patch.object(switch, "_wait_array_stable", lambda *a, **k: calls.append("stable")), \
         patch.object(switch, "_wait_species", lambda *a, **k: True), \
         patch.object(switch, "my_mon", lambda i: {"species": 8}):
        ok = switch._pick_and_switch(3, False, "t")
    assert ok and calls == [2, "inv", "stable"], calls
    print("A 成功换人只 invalidate ok", calls)


def test_switch_fail():
    with patch.object(switch, "_cursor_for_species", lambda sp: 2), \
         patch.object(action, "pick_and_switch", lambda pos: False), \
         patch.object(state, "in_dialog", lambda: False):
        ok = switch._pick_and_switch(3, False, "t")
    assert not ok
    print("B 失败不 invalidate ok")


test_switch_ok()
test_switch_fail()
print("全部通过")
