"""离线测试：一致性快照 + 看门狗。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import info
import auto_battle
import watchdog


def test_consistent_snapshot():
    """坐标在两次读取之间变化 -> 应该重读，直到稳定。"""
    seq = [(10, 20), (10, 21), (10, 21), (10, 21)]
    it = iter(seq)

    def fake_coords():
        return next(it, (10, 21))

    calls = {"n": 0}

    def fake_snap():
        calls["n"] += 1
        return {"battle": False, "dialog": False, "choice": False,
                "turn": 4, "x": 0, "y": 0}

    with patch("state.coords", fake_coords), \
         patch("state.turn_state", lambda: 4), \
         patch("state.snapshot", fake_snap):
        d = info.consistent_snapshot(max_tries=3)
    print("A 一致性快照：读完", calls["n"], "次 ->", d["x"], d["y"], "OK")
    assert calls["n"] >= 2


def test_watchdog_triggers():
    watchdog._wd.update({"last": None, "count": 0})
    key = ("battle", 40, 18)
    hit = False
    for i in range(13):
        if watchdog._watchdog(key):
            hit = True
            break
    print("B 看门狗：连续同状态", i + 1, "轮触发 =", hit, "OK" if hit else "FAIL")
    assert hit


def test_watchdog_resets_on_change():
    watchdog._wd.update({"last": None, "count": 0})
    watchdog._watchdog(("battle", 40, 18))
    watchdog._watchdog(("battle", 40, 18))
    watchdog._watchdog(("battle", 30, 18))     # 血量变化 -> 重置
    hit = watchdog._watchdog(("battle", 30, 18))
    print("C 看门狗：状态变化后重置，不误触发 =", not hit, "OK" if not hit else "FAIL")
    assert not hit


test_consistent_snapshot()
test_watchdog_triggers()
test_watchdog_resets_on_change()
print("全部通过")
