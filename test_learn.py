"""离线测试：学招处理（迁移后防止未定义名/分支错）。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import learn


def test_no_interface():
    with patch.object(learn, "snapshot", lambda: {"battle": False, "dialog": False, "choice": False}):
        assert learn.learn_moves_guard() == 0
    print("A 无界面直接返回 ok")


def test_replace_move_branch():
    calls = []
    with patch.object(learn, "snapshot", lambda: {"battle": False, "dialog": True, "choice": False}), \
         patch("state.menu_kind", lambda: "moves"), \
         patch("bdata.my_mon", lambda s: {"moves": [104, 45, 39, 86], "pp": [1, 1, 1, 1]}), \
         patch("switch.active_slot", lambda: 0), \
         patch.object(learn.action, "move_move_cursor", lambda t: calls.append(("move", t))), \
         patch.object(learn.action, "tap_a", lambda: calls.append(("a",))), \
         patch.object(learn.action, "tap_b", lambda: calls.append(("b",))):
        n = learn.learn_moves_guard(max_rounds=1)
    assert n == 1 and ("move", 0) in calls and ("a",) in calls, calls
    print("B 替换变化技分支 ok", calls)


def test_choice_branch():
    calls = []
    with patch.object(learn, "snapshot", lambda: {"battle": False, "dialog": True, "choice": True}), \
         patch.object(learn.action, "choose_option", lambda i: calls.append(("choose", i))):
        n = learn.learn_moves_guard(max_rounds=1)
    assert n == 1 and calls == [("choose", 0)], calls
    print("C 选「是」分支 ok")


def test_dialog_branch():
    calls = []
    with patch.object(learn, "snapshot", lambda: {"battle": False, "dialog": True, "choice": False}), \
         patch("state.menu_kind", lambda: "main"), \
         patch.object(learn.action, "advance_dialog", lambda: calls.append(("adv",))):
        n = learn.learn_moves_guard(max_rounds=1)
    assert n == 0 and calls == [("adv",)], calls
    print("D 普通对话推进 ok")


test_no_interface()
test_replace_move_branch()
test_choice_branch()
test_dialog_branch()
print("全部通过")
