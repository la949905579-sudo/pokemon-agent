"""离线测试：数组下标=光标号，active_slot 由 species 驱动。"""
import struct
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import switch

SPECIES = {0: 25, 1: 15, 2: 22, 3: 8, 4: 69, 5: 32}


def test_cursor_from_active():
    with patch.object(switch, "active_slot", lambda: 4):
        assert switch.party_order() == [4, 0, 1, 2, 3, 5]
        assert switch._cursor_for_slot(4) == 0
        assert switch._cursor_for_slot(0) == 1
        assert switch._cursor_for_slot(5) == 5
    print("A 光标由 active 推导 ok")


def test_party_order_active_first():
    with patch.object(switch, "active_slot", lambda: 2):
        assert switch.party_order() == [2, 0, 1, 3, 4, 5]
    print("B 出场排最前 ok")


def test_active_from_species():
    with patch.object(switch, "in_battle", lambda: True), \
         patch.object(switch, "_field", {"t": 0.0, "sp": None, "slot": None}), \
         patch.object(switch, "rd", lambda a, n: struct.pack("<H", 8)), \
         patch.object(switch, "my_mon", lambda i: {"species": SPECIES[i]}):
        assert switch.active_slot() == 3
    print("C species 驱动出场槽位 ok")


test_cursor_from_active()
test_party_order_active_first()
test_active_from_species()
print("全部通过")
