#!/usr/bin/env python3
"""从 pret/pokefirered 解包仓库离线提取地图可走格数据（不联网、不编译 ROM）。

用法：
    python3 tools/gen_maps_data.py --match                 # 用现有真机 RAM 地图交叉校验解包布局
    python3 tools/gen_maps_data.py --emit MAP_CERULEAN_CITY MAP_VERMILION_CITY MAP_ROUTE5
    python3 tools/gen_maps_data.py --emit-all              # 全量 425 张（按地图名，重名回退 id）
    python3 tools/gen_maps_data.py --check                 # 只校验已生成的 maps_decomp（不读解包仓库）
    python3 tools/gen_maps_data.py --ref /path/pokefirered ...

数据来源（都是解包仓库里的明文文件）：
    data/layouts/layouts.json           布局表：宽高 + blockdata_filepath（map.bin）+ 边框
    data/layouts/<Layout>/map.bin       每格 u16：metatile id(bits0-9) | 碰撞(bits10-11) | 海拔(bits12-15)
    data/maps/<Map>/map.json            地图 id / 名称 / layout / connections / warp_events
    src/data/tilesets/metatiles.h       tileset → data/tilesets/.../metatile_attributes.bin 路径
    include/constants/metatile_behaviors.h  MB_* 行为常量（写成 data/metatile_behaviors.json）
    src/data/wild_encounters.json       野生遭遇表（挑 _LeafGreen 版本 → data/encounters_leafgreen.json）

可走判定（本小步）：碰撞位（bits 10-11）非 0 → 不可走（1），否则可走（0）。
草丛/水面/台阶/门等「行为」、海拔差、野生遭遇表是后续步骤，不在本步。

真机对照：`games/pokemon_firered/maps/map_<addr>.json` 是既往真机 RAM 抓取的可走格
（0=可走 1=障碍）。`--match` 先按宽高筛候选解包布局，再逐格比对；diff=0 即汉化版与
香草解包数据在该图上一致。注意解包布局是全果 426 张图，RAM 只有走到过的图。

约定：离线工具，不引入第三方依赖；输出对齐现有 maps JSON 的 `w/h/tiles` 字段，
另外带 `id/name/layout/connections/warps/ram_crosscheck`。
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DEFAULT = os.environ.get("POKEFIRERED_REF", "/root/refs/pokefirered")
EXISTING_MAPS = os.path.join(ROOT, "games", "pokemon_firered", "maps")
OUT_DIR = os.path.join(ROOT, "games", "pokemon_firered", "maps_decomp")
DATA_DIR = os.path.join(ROOT, "games", "pokemon_firered", "data")
LEGEND_PATH = os.path.join(DATA_DIR, "metatile_behaviors.json")
ENCOUNTERS_PATH = os.path.join(DATA_DIR, "encounters_leafgreen.json")

# gen3 地图 block（u16）：低 10 位 metatile id、bits 10-11 碰撞、bits 12-15 海拔。
COLLISION_MASK = 0x0C00
METATILE_ID_MASK = 0x03FF
# FRLG：primary 640 个 metatile、合计 1024；属性是 u32/个，behavior 在 bits 0-8。
NUM_METATILES_IN_PRIMARY = 640
NUM_METATILES_TOTAL = 1024
BEHAVIOR_MASK = 0x01FF
UNKNOWN_BEHAVIOR = 0xFF  # 超出 tileset 表/未定义（输出里计到 behavior_unknown）

# 本小步产出/校验的目标地图（layout 由 map.json 反查）。
EXPECTED = {
    "MAP_CERULEAN_CITY": (48, 40, "LAYOUT_CERULEAN_CITY"),
    "MAP_VERMILION_CITY": (48, 40, "LAYOUT_VERMILION_CITY"),
    "MAP_ROUTE5": (48, 40, "LAYOUT_ROUTE5"),
}


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_layouts(ref):
    """解包布局表 → {layout_id: layout}；跳过表里的 {} 占位条目。"""
    table = _read_json(os.path.join(ref, "data", "layouts", "layouts.json"))["layouts"]
    out = {}
    for lay in table:
        if not lay or not lay.get("id") or "blockdata_filepath" not in lay:
            continue
        out[lay["id"]] = lay
    return out


def build_grid(ref, layout):
    """layout → 可走格（0=可走 1=障碍），按碰撞位；尺寸不符直接报错（不猜）。"""
    w, h = layout["width"], layout["height"]
    path = os.path.join(ref, layout["blockdata_filepath"])
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) != w * h * 2:
        raise ValueError("%s: map.bin %d 字节，期望 %d（%dx%d）" % (path, len(raw), w * h * 2, w, h))
    grid = []
    for y in range(h):
        row = []
        for x in range(w):
            i = (y * w + x) * 2
            block = raw[i] | (raw[i + 1] << 8)
            row.append(1 if block & COLLISION_MASK else 0)
        grid.append(row)
    return grid


def load_map_jsons(ref):
    """解包 data/maps/*/map.json → {map_id: map}。"""
    out = {}
    for path in sorted(glob.glob(os.path.join(ref, "data", "maps", "*", "map.json"))):
        m = _read_json(path)
        if m.get("id"):
            out[m["id"]] = m
    return out


def load_tileset_attr_paths(ref):
    """src/data/tilesets/metatiles.h 的 INCBIN_U32 行 → {gMetatileAttributes_X: 相对路径}。"""
    path = os.path.join(ref, "src", "data", "tilesets", "metatiles.h")
    out = {}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for m in re.finditer(r'const\s+u32\s+(gMetatileAttributes_\w+)\s*\[\]\s*=\s*INCBIN_U32\("([^"]+)"\)', text):
        out[m.group(1)] = m.group(2)
    return out


def load_metatile_attrs(ref, rel_path):
    """metatile_attributes.bin → [u32]（每个 metatile 一条，behavior 在 bits 0-8）。"""
    path = os.path.join(ref, rel_path)
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) % 4:
        raise ValueError("%s: 字节数不是 4 的倍数" % path)
    return [int.from_bytes(raw[i:i + 4], "little") for i in range(0, len(raw), 4)]


def _tileset_symbol(tileset):
    """layout 的 gTileset_X → 属性表符号 gMetatileAttributes_X。"""
    if not tileset:
        return None
    name = tileset[len("gTileset_"):] if tileset.startswith("gTileset_") else tileset
    return "gMetatileAttributes_" + name


def behavior_grid(ref, layout, attr_paths, attr_cache):
    """layout → 行为 id 网格（0..0xFF；超出表范围记 UNKNOWN_BEHAVIOR 并计数）。"""
    w, h = layout["width"], layout["height"]
    path = os.path.join(ref, layout["blockdata_filepath"])
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) != w * h * 2:
        raise ValueError("%s: map.bin %d 字节，期望 %d（%dx%d）" % (path, len(raw), w * h * 2, w, h))

    def attrs_for(symbol):
        if symbol is None:
            return None
        if symbol not in attr_paths:
            raise ValueError("tileset 属性路径缺失：%s" % symbol)
        if symbol not in attr_cache:
            attr_cache[symbol] = load_metatile_attrs(ref, attr_paths[symbol])
        return attr_cache[symbol]

    primary = attrs_for(_tileset_symbol(layout.get("primary_tileset")))
    secondary = attrs_for(_tileset_symbol(layout.get("secondary_tileset")))
    grid = []
    unknown = 0
    for y in range(h):
        row = []
        for x in range(w):
            i = (y * w + x) * 2
            block = raw[i] | (raw[i + 1] << 8)
            meta = block & METATILE_ID_MASK
            if meta < NUM_METATILES_IN_PRIMARY:
                table, idx = primary, meta
            elif meta < NUM_METATILES_TOTAL:
                table, idx = secondary, meta - NUM_METATILES_IN_PRIMARY
            else:
                table, idx = None, 0
            if table is None or idx >= len(table):
                row.append(UNKNOWN_BEHAVIOR)
                unknown += 1
            else:
                row.append(table[idx] & BEHAVIOR_MASK)
        grid.append(row)
    return grid, unknown


def load_behavior_names(ref):
    """include/constants/metatile_behaviors.h → {id: MB_NAME}。"""
    path = os.path.join(ref, "include", "constants", "metatile_behaviors.h")
    out = {}
    with open(path, encoding="utf-8") as f:
        for m in re.finditer(r"#define\s+(MB_\w+)\s+(0x[0-9A-Fa-f]+)", f.read()):
            out[int(m.group(2), 16)] = m.group(1)
    return out


def load_species_ids(ref):
    """include/constants/species.h → {SPECIES_X: id}；支持 (NUM_SPECIES + n) 一类表达式。"""
    path = os.path.join(ref, "include", "constants", "species.h")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    exprs = dict(re.findall(r"#define\s+(SPECIES_\w+)\s+([^\n]+)", text))
    exprs.update(dict(re.findall(r"#define\s+(NUM_SPECIES)\s+([^\n]+)", text)))
    values = {}
    changed = True
    while changed:
        changed = False
        for name, expr in exprs.items():
            if name in values:
                continue
            e = expr
            for k, v in list(values.items()) + [("NUM_SPECIES", values.get("SPECIES_EGG"))]:
                if v is not None:
                    e = e.replace(k, str(v))
            if re.fullmatch(r"[\d\s+\-()]+", e or ""):
                try:
                    values[name] = int(eval(e))  # noqa: S307  （只含数字/括号/加减）
                    changed = True
                except Exception:
                    pass
    values.pop("NUM_SPECIES", None)
    return {k: v for k, v in values.items() if k != "SPECIES_EGG" or True}


def _species_id(species, species_ids):
    """'SPECIES_X' → id；解析不到就原样返回字符串（数据可追溯）。"""
    if not isinstance(species, str):
        return species
    return species_ids.get(species, species)


def build_encounters(ref, version="leafgreen"):
    """解包野生遭遇表 → LeafGreen 版（base_label 以 _LeafGreen 结尾）。"""
    d = _read_json(os.path.join(ref, "src", "data", "wild_encounters.json"))
    groups = d["wild_encounter_groups"]
    if not groups:
        raise SystemExit("wild_encounters.json 没有分组")
    group = groups[0]
    rates = {f["type"]: f for f in group["fields"]}
    suffix = "_LeafGreen" if version.lower() in ("leafgreen", "lg") else "_FireRed"
    species_ids = load_species_ids(ref)
    maps = {}
    for e in group["encounters"]:
        if not (e.get("base_label") or "").endswith(suffix):
            continue
        mid = e["map"]
        out = {}
        for sec in ("land_mons", "water_mons", "rock_smash_mons"):
            s = e.get(sec)
            if not s:
                continue
            chances = rates.get(sec, {}).get("encounter_rates", [])
            slots = []
            for i, mo in enumerate(s.get("mons") or []):
                slot = {
                    "species": _species_id(mo.get("species"), species_ids),
                    "min": mo.get("min_level"),
                    "max": mo.get("max_level"),
                }
                if i < len(chances):
                    slot["chance"] = chances[i]
                slots.append(slot)
            obj = {"slots": slots}
            if "encounter_rate" in s:
                obj["rate"] = s["encounter_rate"]
            out[sec[: -len("_mons")]] = obj
        fm = e.get("fishing_mons")
        if fm:
            chances = rates.get("fishing_mons", {}).get("encounter_rates", [])
            rods = rates.get("fishing_mons", {}).get("groups", {})
            mons = fm.get("mons") or []
            fish = {}
            if rods:
                for rod, idxs in rods.items():
                    fish[rod] = []
                    for i in idxs:
                        if i >= len(mons):
                            continue
                        mo = mons[i]
                        slot = {
                            "species": _species_id(mo.get("species"), species_ids),
                            "min": mo.get("min_level"),
                            "max": mo.get("max_level"),
                        }
                        if i < len(chances):
                            slot["chance"] = chances[i]
                        fish[rod].append(slot)
            else:
                fish["any_rod"] = [
                    {"species": _species_id(mo.get("species"), species_ids),
                     "min": mo.get("min_level"), "max": mo.get("max_level")}
                    for mo in mons
                ]
            obj = {"rods": fish}
            if "encounter_rate" in fm:
                obj["rate"] = fm["encounter_rate"]
            out["fishing"] = obj
        maps[mid] = out
    return {
        "version": version.lower(),
        "source": "pokefirered: src/data/wild_encounters.json（base_label 后缀 %s）" % suffix,
        "maps": maps,
    }


def emit_behavior_legend(ref, path):
    names = load_behavior_names(ref)
    doc = {
        "source": "pokefirered: include/constants/metatile_behaviors.h",
        "names": {str(k): v for k, v in sorted(names.items())},
    }
    _write_json(path, doc)
    return path


def _write_json(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return path


def load_existing_maps(repo_root=ROOT):
    """现有真机 RAM 地图 → [(path, doc)]；跳过没有可走格的 JSON（如 map_links.json）。"""
    out = []
    for path in sorted(glob.glob(os.path.join(repo_root, "games", "pokemon_firered", "maps", "*.json"))):
        doc = _read_json(path)
        if "w" not in doc or "tiles" not in doc:
            continue
        out.append((path, doc))
    return out


def _diff(tiles, grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    return sum(1 for y in range(h) for x in range(w) if grid[y][x] != tiles[y][x])


def match_existing(ref, repo_root=ROOT):
    """现有 RAM 地图 × 同尺寸解包布局逐格比对 → 报告行（按 diff 升序）。"""
    layouts = load_layouts(ref)
    by_dims = {}
    for lid, lay in layouts.items():
        by_dims.setdefault((lay["width"], lay["height"]), []).append(lid)
    rows = []
    for path, doc in load_existing_maps(repo_root):
        w, h, tiles = doc["w"], doc["h"], doc["tiles"]
        scored = []
        for lid in by_dims.get((w, h), []):
            try:
                grid = build_grid(ref, layouts[lid])
            except ValueError:
                continue
            scored.append((_diff(tiles, grid), lid))
        scored.sort()
        exact = sum(1 for d, _ in scored if d == 0)
        rows.append({
            "file": os.path.basename(path),
            "w": w, "h": h,
            "best": scored[0][1] if scored else None,
            "diff": scored[0][0] if scored else -1,
            "candidates": len(scored),
            "exact_candidates": exact,
        })
    return rows


def _ram_crosscheck(existing, w, h, grid):
    """和现有同尺寸 RAM 地图逐格比；只有 diff=0（同一张图且碰撞位一致）才记匹配，否则 None。"""
    if not existing:
        return None
    best = None
    for path, doc in existing:
        if doc["w"] != w or doc["h"] != h:
            continue
        d = _diff(doc["tiles"], grid)
        if best is None or d < best["diff"]:
            best = {"file": os.path.basename(path), "diff": d}
    if best is None or best["diff"] != 0:
        return None
    return best


def build_doc(ref, mid, layouts, maps, grid_cache, existing=None,
              attr_paths=None, attr_cache=None, behavior_cache=None):
    """按地图 id 造可走格文档（含 connections / warps / 与真机 RAM 数据的交叉校验）。"""
    m = maps.get(mid)
    if m is None:
        raise SystemExit("找不到地图 %s（解包 data/maps/*/map.json）" % mid)
    lid = m.get("layout")
    if lid not in layouts:
        raise SystemExit("%s: 布局 %s 不在 layouts.json" % (mid, lid))
    lay = layouts[lid]
    grid = grid_cache.get(lid)
    if grid is None:
        grid = grid_cache[lid] = build_grid(ref, lay)
    if attr_paths is None:
        attr_paths = load_tileset_attr_paths(ref)
    if attr_cache is None:
        attr_cache = {}
    if behavior_cache is None:
        behavior_cache = {}
    if lid not in behavior_cache:
        behav, unknown = behavior_grid(ref, lay, attr_paths, attr_cache)
        behavior_cache[lid] = (["".join("%02x" % v for v in row) for row in behav], unknown)
    behav_rows, unknown = behavior_cache[lid]
    doc = {
        "id": mid,
        "name": m.get("name"),
        "layout": lid,
        "w": lay["width"],
        "h": lay["height"],
        "tiles": grid,
        # 行为 id 网格（每格 2 位十六进制；0x00=MB_NORMAL），名字见 data/metatile_behaviors.json
        "behaviors": list(behav_rows),
        # 室内图的 map.json 里 connections 是 null，统一成 []（check 也据此校验）
        "connections": m.get("connections") or [],
        "warps": m.get("warp_events") or [],
        "ram_crosscheck": _ram_crosscheck(existing, lay["width"], lay["height"], grid),
        "source": "pokefirered: collision bits + metatile behavior",
    }
    if unknown:
        doc["behavior_unknown"] = unknown
    return doc


def _write_doc(out_dir, fname, doc):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "%s.json" % fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return path


def emit(ref, map_ids, out_dir=OUT_DIR, repo_root=ROOT, grid_cache=None, layouts=None, maps=None):
    """按地图 id 生成可走格 JSON（文件名=地图名）。"""
    layouts = load_layouts(ref) if layouts is None else layouts
    maps = load_map_jsons(ref) if maps is None else maps
    grid_cache = {} if grid_cache is None else grid_cache
    existing = load_existing_maps(repo_root) if repo_root else []
    attr_paths = load_tileset_attr_paths(ref)
    attr_cache = {}
    behavior_cache = {}
    written = []
    for mid in map_ids:
        doc = build_doc(ref, mid, layouts, maps, grid_cache, existing,
                        attr_paths, attr_cache, behavior_cache)
        written.append(_write_doc(out_dir, doc["name"] or mid, doc))
    return written


def emit_all(ref, out_dir=OUT_DIR, repo_root=ROOT, data_dir=None):
    """全量生成（解包 maps 表里所有地图）；文件名默认地图名，重名回退地图 id。"""
    layouts = load_layouts(ref)
    maps = load_map_jsons(ref)
    grid_cache = {}
    existing = load_existing_maps(repo_root) if repo_root else []
    attr_paths = load_tileset_attr_paths(ref)
    attr_cache = {}
    behavior_cache = {}
    used = set()
    written = []
    for mid in sorted(maps, key=lambda k: (maps[k].get("name") or "", k)):
        doc = build_doc(ref, mid, layouts, maps, grid_cache, existing,
                        attr_paths, attr_cache, behavior_cache)
        fname = doc["name"] or mid
        if fname in used:  # 防御：同名回退 id（当前 425 张名字唯一，走不到）
            fname = mid
        used.add(fname)
        written.append(_write_doc(out_dir, fname, doc))
    base = data_dir or DATA_DIR
    written.append(emit_behavior_legend(ref, os.path.join(base, "metatile_behaviors.json")))
    written.append(_write_json(os.path.join(base, "encounters_leafgreen.json"), build_encounters(ref)))
    return written


def check(out_dir=OUT_DIR, expected=None, ref=None, data_dir=None, with_extras=False):
    """校验已生成的地图 JSON。expected 指定子集；ref 给出时按解包 maps/layouts 校验尺寸与 layout；
    with_extras 时额外校验行为名表与遭遇表（emit-all 会一起生成）。"""
    problems = []
    found = {}
    for path in sorted(glob.glob(os.path.join(out_dir, "*.json"))):
        try:
            doc = _read_json(path)
        except Exception as e:  # noqa: BLE001
            problems.append("%s: JSON 解析失败 %s" % (os.path.basename(path), e))
            continue
        found[doc.get("id")] = doc

    layouts = maps = None
    if ref is not None:
        layouts = load_layouts(ref)
        maps = load_map_jsons(ref)

    if expected is not None:
        targets = expected
    elif layouts is not None:
        targets = {}
        for mid, m in maps.items():
            lay = layouts.get(m.get("layout"))
            if lay is not None:
                targets[mid] = (lay["width"], lay["height"], lay["id"])
    else:
        # 没有解包仓库：只能做自洽校验（tiles 与 w/h 一致、0/1、字段齐全）
        targets = {mid: (doc.get("w"), doc.get("h"), None) for mid, doc in found.items()}

    for mid in found:
        if mid not in targets:
            problems.append("%s: 解包 maps 里没有这个 id" % mid)
    for mid, (w, h, lid) in targets.items():
        doc = found.get(mid)
        if doc is None:
            problems.append("缺少 %s" % mid)
            continue
        if doc.get("w") != w or doc.get("h") != h:
            problems.append("%s: 尺寸 %sx%s，期望 %dx%d" % (mid, doc.get("w"), doc.get("h"), w, h))
        if lid is not None and doc.get("layout") != lid:
            problems.append("%s: layout %s，期望 %s" % (mid, doc.get("layout"), lid))
        tiles = doc.get("tiles")
        if not isinstance(tiles, list) or len(tiles) != h:
            problems.append("%s: tiles 行数不对" % mid)
            continue
        for y, row in enumerate(tiles):
            if not isinstance(row, list) or len(row) != w:
                problems.append("%s: 第 %d 行宽度不对" % (mid, y))
                break
            if any(v not in (0, 1) for v in row):
                problems.append("%s: 第 %d 行有非 0/1 值" % (mid, y))
                break
        behav = doc.get("behaviors")
        if not isinstance(behav, list) or len(behav) != h:
            problems.append("%s: behaviors 行数不对" % mid)
        else:
            for y, row in enumerate(behav):
                if not isinstance(row, str) or len(row) != w * 2 or not re.fullmatch(r"[0-9a-f]+", row):
                    problems.append("%s: behaviors 第 %d 行应是 %d 位十六进制" % (mid, y, w * 2))
                    break
        if not isinstance(doc.get("connections"), list):
            problems.append("%s: 缺 connections" % mid)
        if not isinstance(doc.get("warps"), list):
            problems.append("%s: 缺 warps" % mid)
        cc = doc.get("ram_crosscheck")
        if cc is not None and cc.get("diff") != 0:
            problems.append("%s: 与真机 RAM 数据 diff=%s（预期 0）" % (mid, cc.get("diff")))
    if with_extras:
        base = data_dir or DATA_DIR
        problems += _check_legend(os.path.join(base, "metatile_behaviors.json"))
        problems += _check_encounters(os.path.join(base, "encounters_leafgreen.json"))
    return problems


def _check_legend(path):
    if not os.path.isfile(path):
        return ["缺 %s（行为名表，--emit-all 会生成）" % os.path.basename(path)]
    doc = _read_json(path)
    names = doc.get("names")
    if not isinstance(names, dict) or not names:
        return ["%s: names 为空" % os.path.basename(path)]
    bad = [k for k in names if not re.fullmatch(r"\d+", k)]
    return ["%s: 行为 id 不是十进制：%s" % (os.path.basename(path), bad[:3])] if bad else []


def _check_encounters(path):
    if not os.path.isfile(path):
        return ["缺 %s（遭遇表，--emit-all 会生成）" % os.path.basename(path)]
    doc = _read_json(path)
    maps = doc.get("maps")
    if not isinstance(maps, dict) or not maps:
        return ["%s: maps 为空" % os.path.basename(path)]
    problems = []
    for mid, data in maps.items():
        if not isinstance(data, dict):
            problems.append("%s: 不是对象" % mid)
            continue
        for sec in ("land", "water", "rock_smash"):
            s = data.get(sec)
            if s is None:
                continue
            for slot in s.get("slots") or []:
                if not isinstance(slot.get("species"), (int, str)):
                    problems.append("%s.%s: species 类型不对" % (mid, sec))
                if not (isinstance(slot.get("min"), int) and isinstance(slot.get("max"), int)
                        and 1 <= slot["min"] <= slot["max"] <= 100):
                    problems.append("%s.%s: 等级区间不对" % (mid, sec))
        fish = data.get("fishing")
        if fish:
            for rod, slots in (fish.get("rods") or {}).items():
                for slot in slots:
                    if not (isinstance(slot.get("min"), int) and isinstance(slot.get("max"), int)
                            and 1 <= slot["min"] <= slot["max"] <= 100):
                        problems.append("%s.fishing.%s: 等级区间不对" % (mid, rod))
        if len(problems) > 20:
            problems.append("……（遭遇表问题过多，截断）")
            break
    return problems


def build_parser():
    ap = argparse.ArgumentParser(
        prog="gen_maps_data.py",
        description="从 pokefirered 解包仓库离线提取地图可走格（碰撞位），并和真机 RAM 地图交叉校验。",
    )
    ap.add_argument("--ref", default=REF_DEFAULT, help="pokefirered 仓库路径（默认 %(default)s）")
    ap.add_argument("--match", action="store_true", help="现有 RAM 地图 × 解包布局逐格比对，打印报告")
    ap.add_argument("--emit", nargs="+", metavar="MAP_ID", help="按地图 id 生成可走格 JSON")
    ap.add_argument("--emit-all", action="store_true",
                    help="全量生成地图 + 行为名表(data/metatile_behaviors.json) + 叶绿遭遇表(data/encounters_leafgreen.json)")
    ap.add_argument("--check", action="store_true", help="只校验已生成的 maps_decomp JSON（离线）")
    ap.add_argument("--out", default=OUT_DIR, help="输出目录（默认 %(default)s）")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    did = False

    if args.match:
        if not os.path.isdir(args.ref):
            print("找不到解包仓库：%s（用 --ref 指定）" % args.ref)
            return 1
        rows = match_existing(args.ref, ROOT)
        exact = 0
        for r in rows:
            if r["diff"] == 0:
                exact += 1
            tag = "OK " if r["diff"] == 0 else "   "
            amb = "（同尺寸另有 %d 个 diff=0）" % (r["exact_candidates"] - 1) if r["exact_candidates"] > 1 else ""
            print("%s%s %dx%d -> %s diff=%d 候选=%d%s" % (
                tag, r["file"], r["w"], r["h"], r["best"], r["diff"], r["candidates"], amb))
        print("交叉校验：%d/%d 张现有地图与解包碰撞位完全一致（diff=0）" % (exact, len(rows)))
        did = True

    if args.emit:
        if not os.path.isdir(args.ref):
            print("找不到解包仓库：%s（用 --ref 指定）" % args.ref)
            return 1
        for path in emit(args.ref, args.emit, args.out, ROOT):
            print("写入 %s" % os.path.relpath(path, ROOT))
        did = True

    if args.emit_all:
        if not os.path.isdir(args.ref):
            print("找不到解包仓库：%s（用 --ref 指定）" % args.ref)
            return 1
        paths = emit_all(args.ref, args.out, ROOT)
        print("全量写入 %d 个文件（地图 + 行为名表 + 叶绿遭遇表）" % len(paths))
        did = True

    if args.check:
        ref = args.ref if os.path.isdir(args.ref) else None
        problems = check(args.out, ref=ref, with_extras=True)
        if problems:
            print("FAIL 地图数据校验：")
            for p in problems:
                print("  - %s" % p)
            return 1
        n = len(glob.glob(os.path.join(args.out, "*.json")))
        print("PASS 地图数据校验（%d 个文件）" % n)
        did = True

    if not did:
        build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
