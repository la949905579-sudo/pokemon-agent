"""离线测试：decision 层纯逻辑（不碰游戏）。"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import decision


def mon(slot, lv, hp, types, moves, pp=None, species=1):
    return {"slot": slot, "lv": lv, "hp": hp, "mhp": hp, "species": species,
            "types": types, "moves": moves, "pp": pp or [10] * len(moves)}


def test_choose_move_prefers_effective():
    m = mon(0, 12, 31, ("电",), [55, 98])     # 水枪 / 电光一闪
    idx, why = decision.choose_move(m, ("火",))  # 水打火 x2
    assert idx == 0, (idx, why)
    print("A 选克制招 ok:", why)


def test_choose_move_skips_no_pp():
    m = mon(0, 12, 31, ("电",), [55, 98], pp=[0, 10])
    idx, why = decision.choose_move(m, ("火",))
    assert idx == 1, (idx, why)               # 水枪没 PP -> 用电光一闪
    print("B 跳过空 PP ok:", why)


def test_choose_switch_prefers_killer():
    party = [
        mon(0, 10, 31, ("一般",), [98]),
        mon(1, 20, 31, ("飞行",), [64]),
        mon(2, 15, 31, ("水",), [55]),
    ]
    enemy = {"lv": 10, "hp": 30, "types": ("火",)}
    assert decision.choose_switch(party, enemy) == 2, "应选水系（水枪克制火）"
    print("C 换人选克制 ok")


def test_choose_switch_skips_fainted():
    party = [
        mon(0, 10, 0, ("水",), [55]),          # 已倒下
        mon(1, 8, 26, ("一般",), [98]),
    ]
    enemy = {"lv": 10, "hp": 30, "types": ("火",)}
    assert decision.choose_switch(party, enemy) == 1, "应跳过倒下的那只"
    print("D 跳过濒死 ok")


def test_should_switch():
    party = [
        mon(0, 12, 31, ("草",), [45]),         # 草被火克制
        mon(1, 15, 31, ("水",), [55]),         # 水克火
    ]
    enemy = {"lv": 10, "hp": 30, "types": ("火",)}
    party[0]["hp"] = 10                        # 受伤 10/31 ≈ 32% < 45%
    tgt = decision.should_switch(party, enemy, 0)
    assert tgt == 1, tgt                       # 应换到水系
    assert decision.should_switch(party, enemy, 1) is None   # 水系不被克
    party[0]["hp"] = 31                        # 满血但被克制 2x -> 任意条件成立，仍换
    assert decision.should_switch(party, enemy, 0) == 1
    # 不被克制且满血时不换
    party2 = [mon(0, 12, 31, ("水",), [55]), mon(1, 15, 31, ("电",), [98])]
    enemy2 = {"lv": 10, "hp": 30, "types": ("火",)}
    assert decision.should_switch(party2, enemy2, 0) is None
    print("E 主动换人判断 ok")


test_choose_move_prefers_effective()
test_choose_move_skips_no_pp()
test_choose_switch_prefers_killer()
test_choose_switch_skips_fainted()
def test_has_attack_move():
    assert not decision.has_attack_move(
        {"moves": [104, 45, 39, 86], "pp": [6, 40, 30, 20]})   # 皮卡丘：全是变化招
    assert decision.has_attack_move({"moves": [84, 116], "pp": [10, 5]})
    assert not decision.has_attack_move({"moves": [31], "pp": [0]})  # PP 耗尽
    assert not decision.has_attack_move({"moves": [0, 0], "pp": [0, 0]})
    print("F 无攻击招判定 ok")


def test_threat_score():
    assert decision.threat_score([33, 28, 16, 98], ("虫", "毒")) == 80   # 起风×2
    assert decision.threat_score([], ("水",)) == 0
    assert decision.threat_score([0, 0], ("水",)) == 0
    print("G 敌方威胁评估 ok")


test_should_switch()
test_has_attack_move()
def test_level_suppression():
    party = [
        {"slot": 1, "lv": 29, "hp": 60, "mhp": 81, "types": ("虫", "毒"),
         "moves": [31, 116, 40, 41], "pp": [20, 30, 35, 20]},
        {"slot": 3, "lv": 26, "hp": 70, "mhp": 70, "types": ("水",),
         "moves": [55, 39, 145, 44], "pp": [25, 30, 30, 25]},
    ]
    low = {"lv": 15, "hp": 41, "mhp": 41, "types": ("一般", "飞行"),
           "moves": [33, 28, 16, 98]}
    assert decision.should_switch_opening(party, low, 1) is None
    print("H 等级压制不换 ok")


def test_v2_prefers_faster_kill():
    bee = {"slot": 1, "lv": 29, "hp": 60, "mhp": 81, "types": ("虫", "毒"),
           "moves": [31, 116, 40, 41], "pp": [20, 30, 35, 20]}
    turtle = {"slot": 3, "lv": 26, "hp": 70, "mhp": 70, "types": ("水",),
              "moves": [55, 39, 145, 44], "pp": [25, 30, 30, 25]}
    foe = {"lv": 15, "hp": 41, "mhp": 41, "types": ("一般", "飞行"),
           "moves": [33, 28, 16, 98]}
    assert decision.score_switch(turtle, foe) > decision.score_switch(bee, foe)
    print("I v2 优先击杀更快者 ok")


test_level_suppression()
test_v2_prefers_faster_kill()
test_threat_score()
print("全部通过")
