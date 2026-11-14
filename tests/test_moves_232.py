"""离线测试：招式名表收录 232（金属爪），战斗页不再显示占位 `#232`。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))

from bdata import MOVES


def test_move_232_present():
    assert 232 in MOVES, "MOVES 缺 232（战斗页会显示占位 #232）"
    name, mtype, power = MOVES[232]
    assert name and name.strip(), f"232 名字为空: {MOVES[232]!r}"
    assert name != "#232", "232 仍是占位名"
    print("A MOVES[232] =", (name, mtype, power), "ok")


def test_move_232_metadata():
    # 来源：PokeAPI move/232（metal-claw / 钢 / 威力 50，zh-hans 金属爪）
    # 交叉：52poke「金属爪」+ Serebii Gen III AttackDex（Steel / 50 / PP 35）
    assert MOVES[232] == ("金属爪", "钢", 50), MOVES[232]
    print("B 232 名字/属性/威力与来源一致 ok")


def test_move_names_nonempty():
    empty = [mid for mid, info in MOVES.items() if not info[0].strip()]
    assert not empty, f"空名字招式: {empty}"
    print(f"C {len(MOVES)} 条招式名均非空 ok")


test_move_232_present()
test_move_232_metadata()
test_move_names_nonempty()
print("全部通过")
