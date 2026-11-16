#!/usr/bin/env python3
"""把 pokefirered 解包地图数据接到 App 的 assets（全量地图资产 + 跨图连接表）。

用法：
    python3 tools/gen_map_assets.py --rom /sdcard/rom/gba/叶绿....gba
    python3 tools/gen_map_assets.py --rom ... --check          # 只校验生成物格式
    python3 tools/gen_map_assets.py --rom ... --validate /tmp/old_map_links.json

原理：
  1. 解包 layouts 的 `map.bin`（blockdata 字节）在 ROM 里按内容反查地址——游戏里
     `gMapHeader.layout->map` 就是这个 ROM 地址，App 的 assets 以它为 key；
     用「布局结构体」校验（结构体 +0/+4=宽高、+8=border 指针、+12=map 指针）+ border 字节
     消歧，找不到结构体的退回首个字节命中并在报告里标注。
  2. 连接表：解包 `map.json` 的 `connections`（方向+offset）按实测规则算出口格与落点：
       up/down：exit 在 y=0 / h-1，落点 y=nh-3 / 2，x 平移 -offset；
       left/right：exit 在 x=0 / w-1，落点 x=nw-3 / 2，y 平移 -offset；
     门/楼梯用 `warp_events`（exit=(x,y)，落点=目标地图同一 warp 的坐标，side=null）；
     同一出口多去向合并成 `targets`（App 的 MapLink 已支持）。
  3. 每张图再加 `behaviors`（每格 2 位十六进制行为 id，来自布局 tileset 的
     metatile 属性表；0x00=MB_NORMAL）与 `maps`（用该布局的地图 id 列表，查询遭遇表用），
     并把 `games/pokemon_firered/data/encounters_leafgreen.json` 原样拷进 assets。
  4. 输出：`native-emu/app/src/main/assets/maps/map_<addr>.json`（addr/w/h/tiles/behaviors/maps，
     tiles 1=挡）与 `map_links.json`（App MapLinks 现有格式）。

校验：`--validate 旧链接表` 会拿实测记录逐条比对（忽略门的 side 差异），打印命中率。
只读 ROM；不联网、不依赖 Android。
"""
import argparse
import glob
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_maps_data as gmd  # noqa: E402  （同目录工具，复用解包解析）

REF_DEFAULT = gmd.REF_DEFAULT
ROM_DEFAULT_GLOB = "/sdcard/rom/gba/口袋妖怪 - 叶绿*.gba"
ASSETS_DIR = os.path.join(ROOT, "native-emu", "app", "src", "main", "assets", "maps")
LINKS_NAME = "map_links.json"
# 遭遇表（gen_maps_data --emit-all 产出）随地图资产一起进 APK，App 地图页按地图 id 查询。
ENCOUNTERS_NAME = "encounters_leafgreen.json"
ENCOUNTERS_SRC = gmd.ENCOUNTERS_PATH

# 连接方向 → App 的 side 名（实测：up=北、down=南、left=西、right=东）
SIDE = {"up": "north", "down": "south", "left": "west", "right": "east"}


def find_rom(arg):
    if arg:
        return arg
    hits = sorted(glob.glob(ROM_DEFAULT_GLOB))
    if not hits:
        raise SystemExit("找不到 ROM：%s（用 --rom 指定）" % ROM_DEFAULT_GLOB)
    return hits[0]


def _u32(b, i):
    return b[i] | (b[i + 1] << 8) | (b[i + 2] << 16) | (b[i + 3] << 24)


def _is_rom_ptr(b, i):
    if i < 0 or i + 4 > len(b):
        return False
    v = _u32(b, i)
    return 0x08000000 <= v < 0x0A000000


def scan_layout_structs(rom):
    """扫 ROM 里的布局结构体 {+0 w, +4 h, +8 border ptr, +12 map ptr, +16/20 tileset ptr}。

    返回 [(w, h, map_ptr, border_ptr)]。4 字节对齐、宽高 1..200、四个指针都在 ROM 段内才算。
    """
    out = []
    n = len(rom) - 24
    for s in range(0, n, 4):
        w = _u32(rom, s)
        h = _u32(rom, s + 4)
        if not (1 <= w <= 200 and 1 <= h <= 200):
            continue
        for p in (s + 8, s + 12, s + 16, s + 20):
            v = _u32(rom, p)
            if not (0x08000000 <= v < 0x0A000000):
                break
        else:
            out.append((w, h, _u32(rom, s + 12), _u32(rom, s + 8)))
    return out


def layout_rom_addr(rom, ref, layout, structs_by_size):
    """解包布局 → ROM 里 blockdata 地址。用结构体 (w,h) 桶 + 字节比对 + border 校验消歧。"""
    data_path = os.path.join(ref, layout["blockdata_filepath"])
    with open(data_path, "rb") as f:
        block = f.read()
    w, h = layout["width"], layout["height"]
    if len(block) != w * h * 2:
        raise ValueError("%s: blockdata 长度不符（%d vs %d）" % (layout["id"], len(block), w * h * 2))
    border = b""
    if layout.get("border_filepath"):
        try:
            with open(os.path.join(ref, layout["border_filepath"]), "rb") as f:
                border = f.read()
        except OSError:
            border = b""

    candidates = []
    for (sw, sh, map_ptr, border_ptr) in structs_by_size.get((w, h), []):
        off = map_ptr - 0x08000000
        if off < 0 or off + len(block) > len(rom):
            continue
        if rom[off:off + len(block)] != block:
            continue
        if border:
            boff = border_ptr - 0x08000000
            if not (0 <= boff and boff + len(border) <= len(rom) and rom[boff:boff + len(border)] == border):
                continue
        candidates.append(map_ptr)
    if len(candidates) == 1:
        return candidates[0], "struct", 1
    if candidates:
        return candidates[0], "struct-multi", len(candidates)
    # 结构体没命中：退回内容反查（取对齐的、最多几个）
    pos = rom.find(block)
    hits = []
    while pos >= 0 and len(hits) < 8:
        hits.append(0x08000000 + pos)
        pos = rom.find(block, pos + 1)
    if hits:
        return hits[0], "raw", len(hits)
    return None, "missing", 0


def locate_all(rom, ref):
    layouts = gmd.load_layouts(ref)
    structs_by_size = {}
    for (w, h, map_ptr, border_ptr) in scan_layout_structs(rom):
        structs_by_size.setdefault((w, h), []).append((w, h, map_ptr, border_ptr))
    out = {}
    stats = {"struct": 0, "struct-multi": 0, "raw": 0, "missing": 0}
    for lid in sorted(layouts):
        addr, how, n = layout_rom_addr(rom, ref, layouts[lid], structs_by_size)
        stats[how] += 1
        if addr is not None:
            out[lid] = addr
    return out, stats


def _conn_edges(layout, conn, neighbor_layout):
    """一条 connections 记录 → [(exit, side, dest, to_pos)]，坐标按实测规则算。"""
    out = []
    w, h = layout["width"], layout["height"]
    nw, nh = neighbor_layout["width"], neighbor_layout["height"]
    off = int(conn.get("offset", 0))
    d = conn["direction"]
    side = SIDE[d]
    if d in ("up", "down"):
        y = 0 if d == "up" else h - 1
        ty = nh - 3 if d == "up" else 2
        for x in range(max(0, off), min(w - 1, off + nw - 1) + 1):
            tx = x - off
            if 0 <= tx < nw:
                out.append(((x, y), side, (tx, ty)))
    else:
        x = w - 1 if d == "right" else 0
        tx = 2 if d == "right" else nw - 3
        for y in range(max(0, off), min(h - 1, off + nh - 1) + 1):
            ty = y - off
            if 0 <= ty < nh:
                out.append(((x, y), side, (tx, ty)))
    return out


def collect_edges(addr_of_layout, layouts, maps, with_doors=False):
    """换图边：[(map_addr, exit, side, to_map_addr, to_pos, kind)]；kind=conn/warp。

    默认只出「地图连接（connections）」——实测 door 坐标口径与解包差 1 格（见 --merge-old），
    门默认沿用实测表；需要解包门时加 with_doors。
    """
    edges = []
    for mid, m in maps.items():
        lid = m.get("layout")
        if lid not in addr_of_layout or m.get("connections") is None:
            continue
        layout = layouts.get(lid)
        for c in m.get("connections") or []:
            nid = c.get("map")
            nmap = maps.get(nid)
            if nmap is None:
                continue
            nlid = nmap.get("layout")
            if nlid not in addr_of_layout:
                continue
            src = addr_of_layout[lid]
            dst = addr_of_layout[nlid]
            for exit_cell, side, to_pos in _conn_edges(layout, c, layouts[nlid]):
                edges.append((src, exit_cell, side, dst, to_pos, "conn", nid))
    if not with_doors:
        return edges
    # 门/楼梯：warp_events 互相指
    for mid, m in maps.items():
        lid = m.get("layout")
        if lid not in addr_of_layout:
            continue
        src = addr_of_layout[lid]
        for wp in m.get("warp_events") or []:
            dest = maps.get(wp.get("dest_map"))
            if dest is None or dest.get("layout") not in addr_of_layout:
                continue
            try:
                wid = int(str(wp.get("dest_warp_id")))
            except (TypeError, ValueError):
                continue
            warps = dest.get("warp_events") or []
            if not (0 <= wid < len(warps)):
                continue
            dst = addr_of_layout[dest["layout"]]
            to_pos = (int(warps[wid]["x"]), int(warps[wid]["y"]))
            # 门/楼梯：exit=warp 格、落点=目标地图同一 warp 格（App：踩上出口格即换图）
            edges.append((src, (int(wp["x"]), int(wp["y"])), None, dst, to_pos, "warp",
                          wp.get("dest_map")))
    return edges


def build_links(edges):
    """按 (map, exit, side) 合并多目标 → App MapLinks 的 JSON 列表。"""
    grouped = {}
    for src, exit_cell, side, dst, to_pos, kind, name in edges:
        key = (src, exit_cell[0], exit_cell[1], side)
        grouped.setdefault(key, []).append((dst, to_pos, kind, name))
    out = []
    for (src, ex, ey, side), targets in sorted(
            grouped.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][1], kv[0][3] or "")):
        uniq = []
        names = {}
        for dst, to_pos, kind, name in targets:
            item = (dst, to_pos)
            if item not in uniq:
                uniq.append(item)
            if name:
                names.setdefault(item, name)
        first = uniq[0]
        entry = {
            "map": src,
            "exit": [ex, ey],
            "side": side,
            "to_map": first[0],
            "to_pos": [first[1][0], first[1][1]],
        }
        if first in names:
            entry["to_name"] = names[first]
        if len(uniq) > 1:
            entry["targets"] = [
                dict({"to_map": d, "to_pos": [p[0], p[1]]},
                     **({"to_name": names[(d, p)]} if (d, p) in names else {}))
                for d, p in uniq
            ]
        out.append(entry)
    return out


def emit_assets(rom, ref, assets_dir, links_name=LINKS_NAME, with_doors=True, merge_old=None):
    """生成全量地图资产与连接表；返回统计。merge_old 给旧实测表时追加解包不出的记录。

    默认把解包 `warp_events`（门/楼梯，side=null）也生成进连接表：解包坐标=真实触发格，
    落点=目标图同一 warp 的坐标；实测表里北向门的 exit 常是「门口下方一格」的测量口径，
    所以别再 merge-old（会让同一扇门多出一条差 1 格的错边），用 --validate 校验即可。

    每张图带 behaviors（tileset 行为网格，2 hex/格）与 maps（该布局对应的地图 id），
    并把遭遇表拷进 assets；同一 blockdata 地址对应多个布局时行为取第一个布局并告警。
    """
    layouts = gmd.load_layouts(ref)
    maps = gmd.load_map_jsons(ref)
    addr_of_layout, stats = locate_all(rom, ref)
    os.makedirs(assets_dir, exist_ok=True)

    # 布局 → 地图 id（多张图可共用同一布局；查询遭遇表要用具体地图 id）
    maps_of_layout = {}
    for mid in sorted(maps):
        lid = maps[mid].get("layout")
        if lid in addr_of_layout:
            maps_of_layout.setdefault(lid, []).append(mid)
    # 同一 blockdata 地址 → 布局列表（同内容共址）
    layouts_of_addr = {}
    for lid, addr in sorted(addr_of_layout.items()):
        layouts_of_addr.setdefault(addr, []).append(lid)

    attr_paths = gmd.load_tileset_attr_paths(ref)
    attr_cache = {}
    behavior_cache = {}
    missing_behavior = []
    unknown_total = 0
    behavior_conflicts = 0

    def behaviors_of(lid):
        """布局 → (行为网格 hex 行, 越界格数)；tileset 缺失等失败返回 (None, 0)。"""
        if lid not in behavior_cache:
            try:
                grid, unknown = gmd.behavior_grid(ref, layouts[lid], attr_paths, attr_cache)
                behavior_cache[lid] = (["".join("%02x" % v for v in row) for row in grid], unknown)
            except Exception as e:  # noqa: BLE001
                print("WARN 行为网格生成失败 %s: %s" % (lid, e))
                behavior_cache[lid] = (None, 0)
        return behavior_cache[lid]

    written = 0
    for addr in sorted(layouts_of_addr):
        lids = layouts_of_addr[addr]
        layout = layouts[lids[0]]
        w, h = layout["width"], layout["height"]
        grid = gmd.build_grid(ref, layout)  # 1=挡（碰撞位），与 App 现有资产同口径
        rows, unknown = behaviors_of(lids[0])
        unknown_total += unknown
        if rows is None:
            missing_behavior.append(lids[0])
        # 同址多布局：tileset 不同则行为网格会不同（数据无法按地址区分），取第一个并告警
        for other in lids[1:]:
            orows, _ = behaviors_of(other)
            if orows is not None and rows is not None and orows != rows:
                behavior_conflicts += 1
                print("WARN 同址行为不一致 0x%x：%s 与 %s 行为网格不同（用 %s）" % (
                    addr, lids[0], other, lids[0]))
                break
        map_ids = []
        for l2 in lids:
            for mid in maps_of_layout.get(l2, []):
                if mid not in map_ids:
                    map_ids.append(mid)
        doc = {"addr": "0x%x" % addr, "w": w, "h": h, "tiles": grid}
        if rows is not None:
            doc["behaviors"] = rows
        doc["maps"] = map_ids
        gmd._write_json(os.path.join(assets_dir, "map_%x.json" % addr), doc)
        written += 1

    encounters_maps = 0
    if os.path.isfile(ENCOUNTERS_SRC):
        shutil.copyfile(ENCOUNTERS_SRC, os.path.join(assets_dir, ENCOUNTERS_NAME))
        encounters_maps = len(gmd._read_json(ENCOUNTERS_SRC).get("maps") or {})
    else:
        print("WARN 缺遭遇表：%s" % ENCOUNTERS_SRC)

    edges = collect_edges(addr_of_layout, layouts, maps, with_doors)
    links = build_links(edges)
    merged = 0
    if merge_old:
        old = gmd._read_json(merge_old)
        have = {(l["map"], tuple(l["exit"]), l.get("side"), l["to_map"], tuple(l["to_pos"])) for l in links}
        for o in old:
            key = (o["map"], tuple(o["exit"]), o.get("side"), o["to_map"], tuple(o["to_pos"]))
            if key in have:
                continue
            entry = {"map": o["map"], "exit": list(o["exit"]), "side": o.get("side"),
                     "to_map": o["to_map"], "to_pos": list(o["to_pos"])}
            if o.get("targets"):
                entry["targets"] = o["targets"]
            links.append(entry)
            merged += 1
    gmd._write_json(os.path.join(assets_dir, links_name), links)
    door_edges = sum(1 for e in edges if e[5] == "warp")
    return {
        "door_edges": door_edges,
        "assets": written,
        "layouts": len(layouts),
        "addr_stats": stats,
        "edges": len(edges),
        "links": len(links),
        "merged_old": merged,
        "targets": sum(1 for l in links if l.get("targets")),
        "behaviors_missing": len(missing_behavior),
        "behavior_unknown": unknown_total,
        "behavior_conflicts": behavior_conflicts,
        "encounters_maps": encounters_maps,
    }


def validate_observed(links, old_links):
    """生成表 vs 实测记录：按 (map, 落点) 匹配，exit 容差 1 格单独统计为「测量口径差」。

    实测表里北向门的 exit 常记录成门口下方一格（玩家按方向前的站位），
    生成表用解包 warp 的触发格，所以 exit 差 1 格属口径差异，不算错；
    落点（to_map + to_pos）必须一致才算命中。
    """
    by_map = {}
    for l in links:
        dsts = {(l["to_map"], tuple(l["to_pos"]))}
        for t in l.get("targets") or []:
            dsts.add((t["to_map"], tuple(t["to_pos"])))
        by_map.setdefault(l["map"], []).append((tuple(l["exit"]), l.get("side"), dsts))
    hit, exit_diff, side_diff, miss = 0, [], [], []
    for o in old_links:
        target = (o["to_map"], tuple(o["to_pos"]))
        best = None
        for ex, side, dsts in by_map.get(o["map"], []):
            if target not in dsts:
                continue
            d = abs(ex[0] - o["exit"][0]) + abs(ex[1] - o["exit"][1])
            if best is None or d < best[0]:
                best = (d, ex, side)
        if best is None:
            miss.append({"map": o["map"], "exit": o["exit"], "side": o.get("side"),
                         "to_map": o["to_map"], "to_pos": o["to_pos"]})
            continue
        hit += 1
        d, ex, side = best
        if d != 0:
            exit_diff.append((o, ex))
        elif side != o.get("side"):
            side_diff.append((o, side))
    return hit, side_diff, miss, exit_diff


def check_assets(assets_dir):
    problems = []
    files = sorted(f for f in glob.glob(os.path.join(assets_dir, "map_*.json"))
                   if os.path.basename(f) != LINKS_NAME)
    if len(files) < 300:
        problems.append("地图资产只有 %d 个（预期 ~365），可能未生成" % len(files))
    addrs = set()
    for path in files:
        try:
            doc = gmd._read_json(path)
        except Exception as e:  # noqa: BLE001
            problems.append("%s: JSON 解析失败 %s" % (os.path.basename(path), e))
            continue
        addr = int(doc.get("addr", "0x0"), 16)
        if addr in addrs:
            problems.append("%s: addr 重复" % os.path.basename(path))
        addrs.add(addr)
        w, h, tiles = doc.get("w"), doc.get("h"), doc.get("tiles")
        if not (isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0):
            problems.append("%s: w/h 不对" % os.path.basename(path))
            continue
        if not isinstance(tiles, list) or len(tiles) != h:
            problems.append("%s: tiles 行数不对" % os.path.basename(path))
            continue
        for row in tiles:
            if not isinstance(row, list) or len(row) != w or any(v not in (0, 1) for v in row):
                problems.append("%s: tiles 行内容不对" % os.path.basename(path))
                break
        # 地图 id 列表（查询遭遇表用；允许为空=该布局没被任何地图引用）
        map_ids = doc.get("maps")
        if not isinstance(map_ids, list) \
                or any(not isinstance(m, str) or not m.startswith("MAP_") for m in map_ids):
            problems.append("%s: maps 字段不对" % os.path.basename(path))
            map_ids = None
        # 行为网格：每格 2 位十六进制（0x00=MB_NORMAL），行数/列数必须与 w/h 一致。
        # 唯一允许缺 behaviors 的情况：没有任何地图引用该布局（如 LAYOUT_UNUSED1）
        behavior_rows = doc.get("behaviors")
        if behavior_rows is None:
            if map_ids is None or map_ids:
                problems.append("%s: 缺 behaviors" % os.path.basename(path))
        elif not isinstance(behavior_rows, list) or len(behavior_rows) != h:
            problems.append("%s: behaviors 行数不对" % os.path.basename(path))
        else:
            for row in behavior_rows:
                if not isinstance(row, str) or len(row) != w * 2 \
                        or any(c not in "0123456789abcdefABCDEF" for c in row):
                    problems.append("%s: behaviors 行内容不对" % os.path.basename(path))
                    break
    enc_path = os.path.join(assets_dir, ENCOUNTERS_NAME)
    if not os.path.isfile(enc_path):
        problems.append("缺 %s" % ENCOUNTERS_NAME)
    else:
        try:
            enc = gmd._read_json(enc_path)
            n = len(enc.get("maps") or {})
            if n < 100:
                problems.append("%s: 遭遇表只有 %d 张图（预期 ~124）" % (ENCOUNTERS_NAME, n))
        except Exception as e:  # noqa: BLE001
            problems.append("%s: JSON 解析失败 %s" % (ENCOUNTERS_NAME, e))
    links_path = os.path.join(assets_dir, LINKS_NAME)
    if not os.path.isfile(links_path):
        problems.append("缺 %s" % LINKS_NAME)
    else:
        links = gmd._read_json(links_path)
        if not isinstance(links, list) or not links:
            problems.append("%s 为空" % LINKS_NAME)
        else:
            for l in links:
                try:
                    assert isinstance(l["map"], int) and l["map"] > 0
                    assert len(l["exit"]) == 2
                    assert isinstance(l["to_map"], int) and l["to_map"] > 0
                    assert len(l["to_pos"]) == 2
                except Exception:  # noqa: BLE001
                    problems.append("%s: 条目格式不对 %s" % (LINKS_NAME, str(l)[:80]))
                    break
    return problems


def build_parser():
    ap = argparse.ArgumentParser(
        prog="gen_map_assets.py",
        description="解包地图 → App assets（全量 map_<addr>.json + map_links.json）。",
    )
    ap.add_argument("--rom", default=None, help="叶绿 ROM 路径（默认 /sdcard/rom/gba/口袋妖怪 - 叶绿*.gba）")
    ap.add_argument("--ref", default=REF_DEFAULT, help="pokefirered 仓库路径（默认 %(default)s）")
    ap.add_argument("--out", default=ASSETS_DIR, help="输出目录（默认 assets/maps）")
    ap.add_argument("--check", action="store_true", help="只校验已生成资产/连接表，不读 ROM")
    ap.add_argument("--validate", default=None, metavar="OLD_LINKS",
                    help="用旧 map_links.json（实测记录）校验生成表命中率")
    ap.add_argument("--retain", action="store_true",
                    help="保留输出目录里旧的 map_*.json（默认先清掉再生成）")
    ap.add_argument("--no-doors", action="store_true",
                    help="不生成解包门/楼梯边（默认生成；坐标用解包 warp=真实触发格）")
    ap.add_argument("--merge-old", default=None, metavar="OLD_LINKS",
                    help="把旧实测表里解包生成不了的门记录追加进新表（推荐）")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    did = False

    if args.check:
        problems = check_assets(args.out)
        if problems:
            print("FAIL 地图资产校验：")
            for p in problems[:20]:
                print("  - %s" % p)
            return 1
        n = len([f for f in glob.glob(os.path.join(args.out, "map_*.json"))
                 if os.path.basename(f) != LINKS_NAME])
        print("PASS 地图资产校验（%d 个地图文件 + %s）" % (n, LINKS_NAME))
        return 0

    if not os.path.isdir(args.ref):
        print("找不到解包仓库：%s（用 --ref 指定）" % args.ref)
        return 1
    rom = find_rom(args.rom)
    with open(rom, "rb") as f:
        rom_data = f.read()
    print("ROM：%s（%d 字节）" % (rom, len(rom_data)))

    if not args.retain:
        for old in glob.glob(os.path.join(args.out, "map_*.json")):
            os.remove(old)
    stats = emit_assets(rom_data, args.ref, args.out, with_doors=not args.no_doors,
                        merge_old=args.merge_old)
    print("地图资产 %d 个（布局 %d，地址定位 %s）；连接边 %d 条（门/楼梯 %d）→ %d 个出口（多目标 %d，合并实测 %d）" % (
        stats["assets"], stats["layouts"], stats["addr_stats"], stats["edges"],
        stats["door_edges"], stats["links"], stats["targets"], stats["merged_old"]))
    print("地形/遭遇：行为网格缺失 %d 张（越界格 %d，同址行为冲突 %d）；遭遇表 %d 张图 → %s" % (
        stats["behaviors_missing"], stats["behavior_unknown"], stats["behavior_conflicts"],
        stats["encounters_maps"], ENCOUNTERS_NAME))

    if args.validate:
        old = gmd._read_json(args.validate)
        hit, side_diff, miss, exit_diff = validate_observed(
            gmd._read_json(os.path.join(args.out, LINKS_NAME)), old)
        print("实测连接校验：%d/%d 命中（落点一致；side 口径不同 %d，exit 差 1 格 %d）" % (
            hit, len(old), len(side_diff), len(exit_diff)))
        for o, ex in exit_diff[:10]:
            print("  exit 口径差：map=%x 实测 exit=%s vs 生成 %s（落点一致）" % (
                o["map"], o["exit"], list(ex)))
        for m in miss[:10]:
            print("  未命中：map=%x exit=%s side=%s -> %x %s" % (
                m["map"], m["exit"], m["side"], m["to_map"], m["to_pos"]))
        if miss:
            print("  ……共 %d 条未命中（已保留生成表；差异需人工确认）" % len(miss))
    did = True
    return 0 if did else 1


if __name__ == "__main__":
    sys.exit(main())
