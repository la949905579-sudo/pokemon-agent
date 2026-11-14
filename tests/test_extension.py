"""离线测试：info / decision 的扩展接口。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
from unittest.mock import patch
import info
import decision


def test_register_scene():
    # 注册一个高优先级场景，应该压过内置判定
    info.register_scene("test_scene", lambda: True, priority=10)
    assert info.scene() == "test_scene", info.scene()
    info.unregister_scene("test_scene")

    # 注销后恢复内置：用 mock snapshot 验证
    fake = {"battle": False, "dialog": False, "choice": False, "turn": 4, "x": 8, "y": 8}
    with patch.object(info, "snapshot", lambda: fake):
        assert info.scene() == info.MAP
    print("A 场景注册/注销 ok")


def test_register_low_priority():
    info.register_scene("low", lambda: True, priority=-1)
    fake = {"battle": False, "dialog": False, "choice": False, "turn": 4, "x": 8, "y": 8}
    with patch.object(info, "snapshot", lambda: fake):
        # 低优先级场景不命中时才会用到（hook 仍会返回 low，所以这里验证它会命中）
        assert info.scene() == "low"
    info.unregister_scene("low")
    print("B 低优先级场景 ok")


def test_move_strategy():
    decision.set_move_strategy(lambda mon, et: (3, "自定义选招"))
    assert decision.choose_move({}, ()) == (3, "自定义选招")
    decision.set_move_strategy(None)
    m = {"moves": [98], "pp": [10]}
    idx, _ = decision.choose_move(m, ("草",))
    assert idx == 0
    print("C 选招策略可替换/恢复 ok")


def test_switch_strategy():
    decision.set_switch_strategy(lambda party, enemy: 5)
    assert decision.choose_switch([], {}) == 5
    decision.set_switch_strategy(None)
    print("D 换人策略可替换/恢复 ok")


test_register_scene()
test_register_low_priority()
test_move_strategy()
test_switch_strategy()
print("全部通过")
