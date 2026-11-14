#!/usr/bin/env python3
"""生成 354 招数据（Gen3 / 火红叶绿）：数据源 PokeAPI。

用法：
    python3 tools/gen_moves_data.py             # 重新抓取并写 games/pokemon_firered/data/moves.json
    python3 tools/gen_moves_data.py --from-dir /tmp/moves   # 离线：从已抓取的 {id}.json 目录组装
    python3 tools/gen_moves_data.py --check     # 只校验现有文件（354 条、字段齐全），不联网

输出格式：JSON 对象，key=招式 id（1..354，字符串），value={"name":中文名,"type":属性中文,"power":威力}
- name 取 PokeAPI names 里的 zh-Hans（官方译名；与 ROM「官译修正」一致），缺失回退 zh-Hant 并打印告警
- power 为 null（变化招）时写 0
- 类型名统一为 17 属性中文（与 pyplatform/bdata.py、GameData.kt 顺序表一致）
"""
import json
import os
import re
import sys
import urllib.request
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "games", "pokemon_firered", "data", "moves.json")
API = "https://pokeapi.co/api/v2/move/%d"
MAX_ID = 354  # Gen3 招式上限（火红/叶绿）

# Gen6 起被改成妖精属性的旧招式：火红/叶绿（Gen3）里仍是「一般」
TYPE_OVERRIDES = {186: "一般", 204: "一般", 236: "一般"}  # 天使之吻 / 撒娇 / 月光

TYPE_ZH = {
    "normal": "一般", "fighting": "格斗", "flying": "飞行", "poison": "毒",
    "ground": "地面", "rock": "岩石", "bug": "虫", "ghost": "幽灵",
    "steel": "钢", "fire": "火", "water": "水", "grass": "草",
    "electric": "电", "psychic": "超能力", "ice": "冰", "dragon": "龙",
    "dark": "恶",
}


UA = {"User-Agent": "pokemon-agent/1.0 (data generator; contact: local)"}


def fetch(mid):
    for attempt in range(5):
        try:
            req = urllib.request.Request(API % mid, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if attempt == 4:
                raise SystemExit(f"fetch move {mid} failed: {e}")
            time.sleep(2.0 + 2.0 * attempt)
    raise AssertionError


def zh_name(d):
    # PokeAPI 语言名是小写：zh-hans / zh-hant
    names = {n["language"]["name"].lower(): n["name"] for n in d["names"]}
    if "zh-hans" in names:
        return names["zh-hans"], None
    if "zh-hant" in names:
        return names["zh-hant"], f"move {d['id']} 无 zh-hans，回退 zh-hant"
    raise SystemExit(f"move {d['id']} 无中文名")


def gen3_power(d):
    """取 Gen3（火红/叶绿）威力：PokeAPI past_values 里「PostGen3 最早一次改动」的旧值。"""
    cur = d["power"]
    post = []
    for pv in d.get("past_values") or []:
        vg = pv.get("version_group") or {}
        m = re.search(r"version-group/(\d+)/", vg.get("url") or "")
        if not m:
            continue
        gid = int(m.group(1))
        if gid >= 8 and pv.get("power") is not None:  # 8 = diamond-pearl（Gen4 起）
            post.append((gid, pv["power"]))
    if post:
        return sorted(post)[0][1]
    return cur or 0


def assemble(data):
    out, warns = {}, []
    for d in data:
        mid = d["id"]
        name, warn = zh_name(d)
        if warn:
            warns.append(warn)
        typ = TYPE_OVERRIDES.get(mid) or TYPE_ZH.get(d["type"]["name"])
        if typ is None:
            raise SystemExit(f"move {mid} 未知属性 {d['type']['name']}")
        out[str(mid)] = {"name": name, "type": typ, "power": gen3_power(d)}
    assert len(out) == MAX_ID, len(out)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write("\n")
    for w in warns:
        print("WARN", w)
    print(f"写入 {OUT}（{len(out)} 条）")
    bad = [k for k, v in out.items() if not v['name'] or v['name'].isdigit()]
    print('空名/数字名:', bad)


def build():
    with ThreadPoolExecutor(max_workers=3) as ex:
        data = list(ex.map(fetch, range(1, MAX_ID + 1)))
    assemble(data)


def from_dir(d):
    data = []
    for mid in range(1, MAX_ID + 1):
        with open(os.path.join(d, f"{mid}.json"), encoding="utf-8") as f:
            data.append(json.load(f))
    assemble(data)


def check():
    with open(OUT, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == MAX_ID, f"条目数 {len(data)} != {MAX_ID}"
    for k, v in data.items():
        assert k.isdigit() and 1 <= int(k) <= MAX_ID, k
        assert v["name"] and isinstance(v["name"], str), k
        assert v["type"] in TYPE_ZH.values(), (k, v["type"])
        assert isinstance(v["power"], int) and v["power"] >= 0, k
    print(f"OK {OUT}（{len(data)} 条）")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    elif "--from-dir" in sys.argv:
        from_dir(sys.argv[sys.argv.index("--from-dir") + 1])
    else:
        build()
