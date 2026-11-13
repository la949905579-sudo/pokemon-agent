#!/usr/bin/env python3
"""从 bdata.py 的 MOVES / TYPE_CHART 生成 Kotlin 的 GameData.kt（生成表，勿手改）。

用法：
    python3 native-emu/tools/gen_moves.py           # 重新生成 GameData.kt
    python3 native-emu/tools/gen_moves.py --check   # 只比对，与现有文件不一致时退出码 1

数据源：<repo>/bdata.py
  - MOVES：id -> (中文名, 属性, 威力)
  - TYPE_CHART：(攻击属性, 防御属性) -> 倍率

生成表：native-emu/app/src/main/java/com/dsh/emu/game/GameData.kt

输出顺序固定：招式按 id 升序；属性表按 ATTACK_ORDER / DEFENSE_ORDER
（沿用既有 GameData.kt 的展示顺序，保证数据不变时重跑输出逐字节一致）。
数据源出现未登记顺序的新属性时脚本报错退出，需人工把它们补进顺序表。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "native-emu/app/src/main/java/com/dsh/emu/game/GameData.kt"

# 属性表的展示顺序（攻击属性 / 各攻击属性下的防御属性），与既有生成表一致。
ATTACK_ORDER = [
    "一般", "冰", "地面", "岩石", "幽灵", "恶", "格斗", "毒",
    "水", "火", "电", "草", "虫", "超能力", "钢", "飞行",
]
DEFENSE_ORDER = {
    "一般": ["岩石", "幽灵"],
    "冰": ["地面", "草", "飞行", "龙"],
    "地面": ["岩石", "毒", "火", "电", "草", "虫", "飞行"],
    "岩石": ["冰", "地面", "格斗", "火", "虫", "钢", "飞行"],
    "幽灵": ["一般", "幽灵", "超能力"],
    "恶": ["幽灵", "恶", "格斗", "超能力"],
    "格斗": ["一般", "冰", "岩石", "毒", "飞行"],
    "毒": ["地面", "岩石", "幽灵", "草"],
    "水": ["地面", "岩石", "水", "火", "草"],
    "火": ["冰", "岩石", "水", "草", "虫"],
    "电": ["地面", "水", "草", "飞行", "龙"],
    "草": ["地面", "岩石", "水", "火"],
    "虫": ["毒", "火", "草", "超能力", "飞行"],
    "超能力": ["格斗", "毒", "超能力"],
    "钢": ["冰", "岩石", "水", "火", "电"],
    "飞行": ["岩石", "格斗", "电", "草", "虫"],
}


def load_data():
    sys.path.insert(0, str(ROOT))
    import bdata

    moves = bdata.MOVES
    chart = bdata.TYPE_CHART
    for mid, info in moves.items():
        if not (isinstance(info, tuple) and len(info) == 3):
            raise SystemExit(f"MOVES[{mid}] 应为 (名字, 属性, 威力)，实际 {info!r}")
    covered = {(a, d) for a in ATTACK_ORDER for d in DEFENSE_ORDER[a]}
    if covered != set(chart):
        raise SystemExit(
            "TYPE_CHART 与生成顺序表不一致，请先更新 ATTACK_ORDER/DEFENSE_ORDER："
            f" 缺 {sorted(set(chart) - covered)} / 多 {sorted(covered - set(chart))}"
        )
    return moves, chart


def render(moves, chart):
    lines = [
        "package com.dsh.emu.game",
        "",
        "/** 招式与属性克制表（从 Python 的 bdata.py 生成，勿手改）。 */",
        "object GameData {",
        "",
        "    /** 招式 id -> (名字, 属性, 威力) */",
        "    val moves: Map<Int, Triple<String, String, Int>> = mapOf(",
    ]
    for mid in sorted(moves):
        name, mtype, power = moves[mid]
        lines.append(f'        {mid} to Triple("{name}", "{mtype}", {power}),')
    lines += [
        "    )",
        "",
        "    /** 属性克制表 (攻击属性, 防御属性) -> 倍率 */",
        "    val typeChart: Map<Pair<String, String>, Double> = mapOf(",
    ]
    for attack in ATTACK_ORDER:
        for defense in DEFENSE_ORDER[attack]:
            lines.append(f'        ("{attack}" to "{defense}") to {chart[(attack, defense)]},')
    lines += ["    )", "}", ""]
    return "\n".join(lines)


def main():
    moves, chart = load_data()
    text = render(moves, chart)
    current = OUT.read_text(encoding="utf-8")
    check = "--check" in sys.argv[1:]
    if text == current:
        print(f"与现有生成表逐字节一致（{len(moves)} 条招式 / {len(chart)} 条克制）")
        return 0
    if check:
        print("生成结果与现有 GameData.kt 不一致；运行不带 --check 重新生成")
        return 1
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"已写入 {OUT.relative_to(ROOT)}（{len(moves)} 条招式 / {len(chart)} 条克制）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
