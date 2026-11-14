"""离线测试：执行闭环（出招确认 + 回合完成）。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
from unittest.mock import patch
import action
import auto_battle
import watchdog


def test_use_move_fails_when_no_change():
    """按 A 后 turn 一直没变 -> 判定失败。"""
    with patch.object(action, "move_move_cursor", lambda i: True), \
         patch.object(action, "read_cursor", lambda addr: 0), \
         patch.object(action, "snapshot", lambda: {"turn": 2, "battle": True}), \
         patch.object(action, "tap_a", lambda: None), \
         patch("time.sleep", lambda s: None):
        ok = action.use_move(0)
    print("A 出招未生效 -> ", ok, "OK" if ok is False else "FAIL")
    assert ok is False


def test_use_move_succeeds_on_turn_change():
    """turn 从 2 变成 4 -> 成功。"""
    seq = [2, 4, 4]
    it = iter(seq)
    with patch.object(action, "move_move_cursor", lambda i: True), \
         patch.object(action, "read_cursor", lambda addr: 0), \
         patch.object(action, "snapshot", lambda: {"turn": next(it, 4), "battle": True}), \
         patch.object(action, "tap_a", lambda: None), \
         patch("time.sleep", lambda s: None):
        ok = action.use_move(0)
    print("B 出招成功 -> ", ok, "OK" if ok else "FAIL")
    assert ok is True


def test_wait_round_end_ready():
    """turn 序列 4 -> 0 -> 1，最后应返回 ready。"""
    seq = [4, 4, 0, 1]
    it = iter(seq)
    with patch.object(action, "snapshot", lambda: {"turn": next(it, 1), "battle": True}), \
         patch.object(action, "tap_a", lambda: None), \
         patch("time.sleep", lambda s: None):
        r = watchdog.wait_round_end(max_polls=10)
    print("C 回合完成 -> ", r, "OK" if r == "ready" else "FAIL")
    assert r == "ready"


def test_wait_round_end_battle_over():
    seq = [4, {"battle": False, "turn": 0}]
    def snap():
        return next(it, {"battle": False, "turn": 0})
    it = iter([{"turn": 4, "battle": True}, {"turn": 0, "battle": False}])
    with patch.object(action, "snapshot", snap), \
         patch.object(action, "tap_a", lambda: None), \
         patch("time.sleep", lambda s: None):
        r = watchdog.wait_round_end(max_polls=10)
    print("D 战斗结束 -> ", r, "OK" if r == "end" else "FAIL")
    assert r == "end"


def test_wait_round_end_timeout():
    """一直卡在 turn=4 -> timeout（交给看门狗）。"""
    with patch.object(action, "snapshot", lambda: {"turn": 4, "battle": True}), \
         patch.object(action, "tap_a", lambda: None), \
         patch("time.sleep", lambda s: None):
        r = watchdog.wait_round_end(max_polls=5)
    print("E 一直卡住 -> ", r, "OK" if r == "timeout" else "FAIL")
    assert r == "timeout"


test_use_move_fails_when_no_change()
test_use_move_succeeds_on_turn_change()
test_wait_round_end_ready()
test_wait_round_end_battle_over()
test_wait_round_end_timeout()
print("全部通过")
