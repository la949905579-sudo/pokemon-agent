"""离线测试：指令层（生命周期/护栏/优先级/决策接入）。"""
import sys
sys.path.insert(0, "/root/workspace")
import intent
import decision

MON = {"moves": [31, 116, 40, 41], "pp": [10, 10, 10, 10]}
FOE = {"hp": 40, "mhp": 40, "types": ("一般",)}


def test_submit_tick_expire():
    intent.reset()
    intent.submit(intent.Intent("prolong", ttl=2))
    assert [i.kind for i in intent.active()] == ["prolong"]
    intent.tick()
    assert len(intent.active()) == 1
    intent.tick()
    assert not intent.active()
    assert any(a["event"] == "expire" for a in intent.audit())
    print("A 提交/递减/过期 ok")


def test_replace_same_kind():
    intent.reset()
    intent.submit(intent.Intent("prolong", ttl=5))
    intent.submit(intent.Intent("prolong", ttl=1))
    assert len(intent.active()) == 1
    print("B 同 kind 替换 ok")


def test_low_hp_drops_prolong():
    intent.reset()
    intent.submit(intent.Intent("prolong", {"hp_floor": 0.5}))
    out = intent.effective({"hp": 10, "mhp": 100}, force=True)
    assert not any(i.kind == "prolong" for i in out), out
    assert any(a["event"] == "dropped_low_hp" for a in intent.audit())
    print("C 低血自动放弃拖回合 ok")


def test_safety_flee():
    intent.reset()
    out = intent.effective({"hp": 10, "mhp": 100}, force=True)
    assert any(i.kind == "flee" and i.source == "guard" for i in out), out
    print("D 危急自动脱战 ok")


def test_priority_order():
    intent.reset()
    intent.submit(intent.Intent("prolong"))
    intent.submit(intent.Intent("no_kill"))
    out = intent.effective(FOE, force=True)
    kinds = [i.kind for i in out]
    assert kinds.index("no_kill") < kinds.index("prolong"), kinds
    print("E 优先级排序 ok", kinds)


def test_choose_move_prolong():
    idx, why = decision.choose_move(
        MON, ("一般",), intents=[intent.Intent("prolong")])
    assert idx == 1 and "变化招" in why, (idx, why)
    print("F prolong 选变化招 ok", why)


def test_choose_move_no_kill_low():
    idx, why = decision.choose_move(
        MON, ("一般",), intents=[intent.Intent("no_kill")],
        enemy={"hp": 3, "mhp": 40})
    assert idx == 1 and "指令" in why, (idx, why)
    print("G no_kill 低血停手 ok", why)


def test_choose_move_no_kill_high():
    idx, why = decision.choose_move(
        MON, ("一般",), intents=[intent.Intent("no_kill")],
        enemy={"hp": 40, "mhp": 40})
    assert "指令" not in why, why
    print("H no_kill 高血正常打 ok", why)


def test_only_class():
    idx, why = decision.choose_move(
        MON, ("一般",), intents=[intent.Intent("only_class", {"power": 0})])
    assert idx == 1, (idx, why)
    print("I only_class 过滤 ok", why)


test_submit_tick_expire()
test_replace_same_kind()
test_low_hp_drops_prolong()
test_safety_flee()
test_priority_order()
test_choose_move_prolong()
test_choose_move_no_kill_low()
test_choose_move_no_kill_high()
test_only_class()
intent.reset()
print("全部通过")
