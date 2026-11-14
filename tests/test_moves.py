"""离线数据测试：招式/属性表防手抄错（FireRed = Gen3 数值）。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
from bdata import MOVES, SPECIES_TYPES

# 期望值来源：PokeAPI zh-hans（官方译名，与 ROM「官译修正」一致）
# + past_values 还原 Gen3（火红/叶绿）威力；生成脚本 tools/gen_moves_data.py。
MOVES_CASES = {
    10: ("抓", "一般", 40),     16: ("起风", "飞行", 40),
    22: ("藤鞭", "草", 35),     28: ("泼沙", "地面", 0),
    31: ("乱击", "一般", 15),   33: ("撞击", "一般", 35),
    35: ("紧束", "一般", 15),   39: ("摇尾巴", "一般", 0),
    40: ("毒针", "毒", 15),     41: ("双针", "虫", 25),
    42: ("飞弹针", "虫", 14),   43: ("瞪眼", "一般", 0),
    44: ("咬住", "恶", 60),     45: ("叫声", "一般", 0),
    55: ("水枪", "水", 40),     56: ("水炮", "水", 120),
    64: ("啄", "飞行", 35),     74: ("生长", "一般", 0),
    79: ("催眠粉", "草", 0),    86: ("电磁波", "电", 0),
    91: ("挖洞", "地面", 60),   98: ("电光一闪", "一般", 40),
    104: ("影子分身", "一般", 0), 116: ("聚气", "一般", 0),
    129: ("高速星星", "一般", 60), 145: ("泡沫", "水", 20),
}
assert len(MOVES_CASES) == 26

SPECIES_CASES = {
    8: ("水",), 15: ("虫", "毒"), 16: ("一般", "飞行"), 22: ("一般", "飞行"),
    25: ("电",), 32: ("毒",), 52: ("一般",), 69: ("草", "毒"),
}


def test_moves():
    assert len(MOVES) == 354, f"招式表应为 354 条，实际 {len(MOVES)}"
    bad = {i: (MOVES.get(i), exp) for i, exp in MOVES_CASES.items()
           if MOVES.get(i) != exp}
    assert not bad, bad
    print(f"A 招式表 {len(MOVES)} 条 / {len(MOVES_CASES)} 条抽验 ok")


def test_species():
    bad = {i: (SPECIES_TYPES.get(i), exp) for i, exp in SPECIES_CASES.items()
           if SPECIES_TYPES.get(i) != exp}
    assert not bad, bad
    print(f"B 属性表 {len(SPECIES_CASES)} 条 ok")


test_moves()
test_species()
print("全部通过")
