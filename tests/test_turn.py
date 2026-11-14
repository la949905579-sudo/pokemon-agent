"""离线测试：朝向获取 + 决策层转身判断 + 执行层分两步（turn 再 walk）。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
from unittest.mock import patch
import info
import decision
import action


def snap(x=8, y=8):
    return {"battle": False, "dialog": False, "choice": False,
            "turn": 4, "x": x, "y": y}


def test_need_turn():
    assert decision.need_turn("up", "up") is False
    assert decision.need_turn("up", "down") is True
    assert decision.need_turn("left", None) is False       # 读不到朝向时不转身
    print("A need_turn ok")


def test_walk_plan():
    assert decision.walk_plan("down", "up") == {"direction": "down", "turn": True}
    assert decision.walk_plan("down", "down") == {"direction": "down", "turn": False}
    print("B walk_plan ok")


def test_info_facing():
    with patch.object(info, "player_facing", lambda: "left"):
        assert info.facing() == "left"
    print("C info.facing ok")


def test_turn_is_separate_action():
    """turn() 只发一次 0.06 的转向键，不移动。"""
    presses = []
    with patch.object(action, "press", lambda n, d=0.35: presses.append((n, d))), \
         patch("time.sleep", lambda s: None):
        action.turn("down")
    assert presses == [("down", 0.06)], presses
    print("D turn 独立转身 ok", presses)


def test_walk_does_not_turn():
    """walk() 只移动，不负责转身。"""
    presses = []
    with patch.object(action, "snapshot", lambda: snap()), \
         patch.object(action, "press", lambda n, d=0.35: presses.append((n, d))), \
         patch("time.sleep", lambda s: None):
        action.walk("up", 1)
    assert presses[0] == ("up", 0.18), presses   # base 0.06 + step 0.12
    print("E walk 只移动 ok", presses)


def test_flow_decision_then_action():
    """决策层：朝向不一致 -> 先 turn 再 walk；一致 -> 只 walk。"""
    presses = []
    facing = {"v": "down"}
    with patch.object(action, "snapshot", lambda: snap()), \
         patch.object(action, "press", lambda n, d=0.35: presses.append((n, d))), \
         patch("time.sleep", lambda s: None):
        d = "up"
        if decision.need_turn(d, facing["v"]):
            action.turn(d)
        action.walk(d, 1)
    assert presses[0] == ("up", 0.06) and presses[1] == ("up", 0.18), presses
    print("F 不一致：先转身再走 ok", presses)

    presses = []
    facing["v"] = "up"
    with patch.object(action, "snapshot", lambda: snap()), \
         patch.object(action, "press", lambda n, d=0.35: presses.append((n, d))), \
         patch("time.sleep", lambda s: None):
        if decision.need_turn(d, facing["v"]):
            action.turn(d)
        action.walk(d, 1)
    assert presses[0] == ("up", 0.18), presses
    print("G 一致：直接走 ok", presses)


test_need_turn()
test_walk_plan()
test_info_facing()
test_turn_is_separate_action()
test_walk_does_not_turn()
test_flow_decision_then_action()
print("全部通过")
