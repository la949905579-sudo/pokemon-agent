#!/usr/bin/env python3
"""tools/gen_map_assets.py 的离线测试：假 ROM（结构体 + blockdata 字节）验证
地址定位、连接出口/落点规则、多目标合并、实测表校验、资产校验（含 behaviors/maps）。

不读真 ROM、不联网、不依赖 /root/refs。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "tools", "gen_map_assets.py")


def load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = load("gen_map_assets", SCRIPT)


def u32b(v):
    return int(v).to_bytes(4, "little")


ROM_SIZE = 0x4000
BASE = 0x08000000


def make_rom():
    """64KB 假 ROM：一张 4x3 的 blockdata + 一个指向它的布局结构体。"""
    rom = bytearray(ROM_SIZE)
    # blockdata 放在 0x100：12 个 block（u16），(1,1) 带碰撞位
    block_off = 0x100
    blocks = [0] * 12
    blocks[1 * 4 + 1] = 0x0400
    for i, b in enumerate(blocks):
        rom[block_off + i * 2:block_off + i * 2 + 2] = int(b).to_bytes(2, "little")
    border_off = 0x200
    rom[border_off:border_off + 8] = b"\x01\x00\x02\x00\x03\x00\x04\x00"
    # 布局结构体放在 0x400：w=4,h=3,border,map,primary,secondary
    s = 0x400
    rom[s:s + 4] = u32b(4)
    rom[s + 4:s + 8] = u32b(3)
    rom[s + 8:s + 12] = u32b(BASE + border_off)
    rom[s + 12:s + 16] = u32b(BASE + block_off)
    rom[s + 16:s + 20] = u32b(BASE + 0x300)
    rom[s + 20:s + 24] = u32b(BASE + 0x380)
    return bytes(rom)


def make_ref(tmp):
    """最小解包仓库：1 个布局（含 border.bin/map.bin）+ 2 张地图 + 1 条连接。"""
    lay = {
        "id": "LAYOUT_TEST", "name": "Test_Layout", "width": 4, "height": 3,
        "border_width": 2, "border_height": 2,
        "primary_tileset": "gTileset_Primary", "secondary_tileset": "gTileset_Secondary",
        "border_filepath": "data/layouts/Test/border.bin",
        "blockdata_filepath": "data/layouts/Test/map.bin",
    }
    os.makedirs(os.path.join(tmp, "data", "layouts", "Test"), exist_ok=True)
    with open(os.path.join(tmp, "data", "layouts", "Test", "map.bin"), "wb") as f:
        blocks = [0] * 12
        blocks[1 * 4 + 1] = 0x0400
        for b in blocks:
            f.write(int(b).to_bytes(2, "little"))
    with open(os.path.join(tmp, "data", "layouts", "Test", "border.bin"), "wb") as f:
        f.write(b"\x01\x00\x02\x00\x03\x00\x04\x00")
    json.dump({"layouts_table_label": "gMapLayouts", "layouts": [{}, lay]},
              open(os.path.join(tmp, "data", "layouts", "layouts.json"), "w", encoding="utf-8"))
    # 第二张地图用同一布局（测试同布局共享地址）
    for mid, name in (("MAP_TEST", "TestMap"), ("MAP_OTHER", "OtherMap")):
        write_json(os.path.join(tmp, "data", "maps", mid, "map.json"), {
            "id": mid, "name": name, "layout": "LAYOUT_TEST",
            "connections": None, "warp_events": [],
        })
    make_tilesets(tmp)
    return tmp


def make_tilesets(tmp):
    """最小 tileset：metatiles.h + 属性表 + 行为名常量（behavior_grid 用）。

    primary 640 个 metatile（[5]=MB_POND_WATER）、secondary 384 个（[0]=MB_TALL_GRASS）。
    """
    def attrs(path, ids):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            for b in ids:
                f.write(int(b).to_bytes(4, "little"))

    ts = os.path.join(tmp, "src", "data", "tilesets")
    os.makedirs(ts, exist_ok=True)
    with open(os.path.join(ts, "metatiles.h"), "w", encoding="utf-8") as f:
        f.write('static const u32 gMetatileAttributes_Primary[] = '
                'INCBIN_U32("data/tilesets/primary/metatile_attributes.bin");\n')
        f.write('static const u32 gMetatileAttributes_Secondary[] = '
                'INCBIN_U32("data/tilesets/secondary/metatile_attributes.bin");\n')
    primary = [0] * 640
    primary[5] = 0x10  # MB_POND_WATER
    attrs(os.path.join(tmp, "data", "tilesets", "primary", "metatile_attributes.bin"), primary)
    secondary = [0] * 384
    secondary[0] = 0x02  # MB_TALL_GRASS
    attrs(os.path.join(tmp, "data", "tilesets", "secondary", "metatile_attributes.bin"), secondary)
    inc = os.path.join(tmp, "include", "constants")
    os.makedirs(inc, exist_ok=True)
    with open(os.path.join(inc, "metatile_behaviors.h"), "w", encoding="utf-8") as f:
        f.write("#define MB_NORMAL 0x0\n#define MB_TALL_GRASS 0x2\n#define MB_POND_WATER 0x10\n")



def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def with_tmp(fn):
    d = tempfile.mkdtemp(prefix="map_assets_")
    try:
        return fn(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_scan_and_locate_layout_addr():
    def run(tmp):
        rom = make_rom()
        ref = make_ref(tmp)
        structs = MOD.scan_layout_structs(rom)
        assert (4, 3, BASE + 0x100, BASE + 0x200) in structs, structs
        layouts = json.load(open(os.path.join(ref, "data", "layouts", "layouts.json")))["layouts"]
        layout = layouts[1]
        by_size = {}
        for item in structs:
            by_size.setdefault((item[0], item[1]), []).append(item)
        addr, how, n = MOD.layout_rom_addr(rom, ref, layout, by_size)
        assert addr == BASE + 0x100 and how == "struct", (addr, how, n)
    with_tmp(run)


def test_conn_edges_rules():
    lay = {"width": 10, "height": 8}
    nlay = {"width": 20, "height": 12}
    # down：exit 在 y=h-1，落点 y=2，x 平移 -offset
    out = MOD._conn_edges(lay, {"direction": "down", "offset": -3}, nlay)
    assert ((0, 7), "south", (3, 2)) in out, out[:3]
    assert all(side == "south" and to[1] == 2 for _, side, to in out), out[:3]
    # up：exit 在 y=0，落点 y=nh-3
    out = MOD._conn_edges(lay, {"direction": "up", "offset": 0}, nlay)
    assert ((0, 0), "north", (0, 9)) in out, out[:3]
    # right：exit 在 x=w-1，落点 x=2，y 平移 -offset
    out = MOD._conn_edges(lay, {"direction": "right", "offset": -2}, nlay)
    assert ((9, 0), "east", (2, 2)) in out, out[:2]
    # left：exit 在 x=0，落点 x=nw-3
    out = MOD._conn_edges(lay, {"direction": "left", "offset": 0}, nlay)
    assert ((0, 0), "west", (17, 0)) in out, out[:2]


def test_build_links_merges_targets():
    edges = [
        (0x100, (3, 4), None, 0x200, (5, 6), "warp", "MAP_B"),
        (0x100, (3, 4), None, 0x300, (7, 8), "warp", "MAP_C"),
        (0x100, (1, 0), "north", 0x200, (1, 9), "conn", "MAP_B"),
    ]
    links = MOD.build_links(edges)
    assert len(links) == 2, links
    door = [l for l in links if l["exit"] == [3, 4]][0]
    assert door["to_map"] == 0x200 and door["to_pos"] == [5, 6]
    assert door["to_name"] == "MAP_B", door
    assert len(door["targets"]) == 2, door
    assert {"to_map": 0x300, "to_pos": [7, 8], "to_name": "MAP_C"} in door["targets"], door


def test_validate_observed_tolerance():
    links = [{"map": 0x100, "exit": [1, 0], "side": "north", "to_map": 0x200, "to_pos": [1, 9]}]
    old = [
        {"map": 0x100, "exit": [1, 0], "side": None, "to_map": 0x200, "to_pos": [1, 9]},  # side 口径不同
        {"map": 0x100, "exit": [1, 1], "side": None, "to_map": 0x200, "to_pos": [1, 9]},  # exit 差 1 格（口径）
        {"map": 0x100, "exit": [2, 2], "side": None, "to_map": 0x200, "to_pos": [0, 0]},  # 未命中
    ]
    hit, side_diff, miss, exit_diff = MOD.validate_observed(links, old)
    assert hit == 2, (hit, side_diff, miss, exit_diff)
    assert len(side_diff) == 1 and len(miss) == 1 and len(exit_diff) == 1, (side_diff, miss, exit_diff)


def test_door_warps_generate_side_null_edges():
    """解包 warp_events → side=null 的门边（exit=解包触发格，落点=目标图 warp 坐标）。"""
    layouts = {"LAYOUT_TEST": {"width": 4, "height": 3}}
    maps = {
        "MAP_TEST": {"layout": "LAYOUT_TEST", "connections": None,
                     "warp_events": [{"x": 2, "y": 2, "dest_map": "MAP_OTHER", "dest_warp_id": 0}]},
        "MAP_OTHER": {"layout": "LAYOUT_TEST", "connections": None,
                      "warp_events": [{"x": 1, "y": 1, "dest_map": "MAP_TEST", "dest_warp_id": 0}]},
    }
    edges = MOD.collect_edges({"LAYOUT_TEST": 0x8200100}, layouts, maps, with_doors=True)
    door = [e for e in edges if e[5] == "warp"]
    assert (0x8200100, (2, 2), None, 0x8200100, (1, 1), "warp", "MAP_OTHER") in door, door
    assert (0x8200100, (1, 1), None, 0x8200100, (2, 2), "warp", "MAP_TEST") in door, door
    links = MOD.build_links(edges)
    assert len(links) == 2, links
    got = {(tuple(l["exit"]), l.get("side")): (l["to_map"], tuple(l["to_pos"])) for l in links}
    assert got[((2, 2), None)] == (0x8200100, (1, 1)), got
    assert [l for l in links if l["exit"] == [2, 2]][0]["to_name"] == "MAP_OTHER"
    # 不带门时不应有 side=null 边
    assert [e for e in MOD.collect_edges({"LAYOUT_TEST": 0x8200100}, layouts, maps, with_doors=False)
            if e[5] == "warp"] == []


def test_check_assets_schema():
    def run(tmp):
        out = os.path.join(tmp, "assets")
        os.makedirs(out, exist_ok=True)
        write_json(os.path.join(out, "map_82d5844.json"),
                   {"addr": "0x82d5844", "w": 2, "h": 2, "tiles": [[0, 1], [1, 0]]})
        write_json(os.path.join(out, "map_links.json"),
                   [{"map": 0x82d5844, "exit": [0, 0], "side": None, "to_map": 0x82d5845, "to_pos": [1, 1]}])
        # 文件数不足 300 → 报问题；但仍应能识别单文件 schema 问题
        problems = MOD.check_assets(out)
        assert any("地图资产只有" in p for p in problems), problems
        good = {"addr": "0x82d5844", "w": 2, "h": 2, "tiles": [[0, 1], [1, 0]]}
        write_json(os.path.join(out, "map_82d5844.json"), good)
        assert MOD.check_assets(out)  # 仍然只有 1 个文件 → 至少报「资产只有」
    with_tmp(run)


def test_help_exit0():
    r = subprocess.run([sys.executable, SCRIPT, "--help"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-300:]
    for flag in ("--rom", "--check", "--validate", "--merge-old", "--no-doors"):
        assert flag in r.stdout, flag


def test_emit_assets_behaviors_maps_encounters():
    """emit_assets 每图写 behaviors/maps、拷遭遇表；同布局多地图时 maps 合并。"""
    def run(tmp):
        ref = make_ref(tmp)
        # 改 blockdata：(1,1) 用 metatile 5（primary 表里 = MB_POND_WATER 0x10），碰撞位 0
        with open(os.path.join(ref, "data", "layouts", "Test", "map.bin"), "wb") as f:
            for i in range(12):
                f.write((5 if i == 5 else 0).to_bytes(2, "little"))
        rom = bytearray(make_rom())
        off = 0x100 + 5 * 2
        rom[off:off + 2] = (5).to_bytes(2, "little")
        enc = {"version": "test", "maps": {"MAP_TEST": {"land": {"slots": []}}}}
        enc_path = os.path.join(tmp, "encounters_src.json")
        write_json(enc_path, enc)
        old_src = MOD.ENCOUNTERS_SRC
        MOD.ENCOUNTERS_SRC = enc_path
        try:
            out = os.path.join(tmp, "assets")
            stats = MOD.emit_assets(bytes(rom), ref, out)
            assert stats["assets"] == 1, stats
            assert stats["behaviors_missing"] == 0 and stats["encounters_maps"] == 1, stats
            doc = json.load(open(os.path.join(out, "map_8000100.json"), encoding="utf-8"))
            assert list(doc.keys()) == ["addr", "w", "h", "tiles", "behaviors", "maps"], doc.keys()
            assert doc["maps"] == ["MAP_OTHER", "MAP_TEST"], doc["maps"]
            assert doc["behaviors"][1] == "00100000", doc["behaviors"]
            assert doc["behaviors"][0] == "00000000", doc["behaviors"]
            assert json.load(open(os.path.join(out, "encounters_leafgreen.json"), encoding="utf-8")) == enc
        finally:
            MOD.ENCOUNTERS_SRC = old_src
    with_tmp(run)


def write_assets_fixture(out, n=301):
    """完整资产目录（n 张图 + 连接表 + 遭遇表），用于 check_assets 全绿/变体用例。"""
    os.makedirs(out, exist_ok=True)
    for i in range(n):
        write_json(os.path.join(out, "map_%x.json" % (0x8200000 + i)),
                   {"addr": "0x%x" % (0x8200000 + i), "w": 2, "h": 2,
                    "tiles": [[0, 1], [1, 0]], "behaviors": ["0201", "0101"],
                    "maps": ["MAP_TEST"]})
    write_json(os.path.join(out, "map_links.json"),
               [{"map": 0x8200000, "exit": [0, 0], "side": None,
                 "to_map": 0x8200001, "to_pos": [1, 1]}])
    write_json(os.path.join(out, "encounters_leafgreen.json"),
               {"version": "test", "maps": {"MAP_DUMMY%d" % i: {} for i in range(101)}})



def test_check_assets_accepts_behaviors_maps():
    def run(tmp):
        out = os.path.join(tmp, "assets")
        write_assets_fixture(out)
        assert MOD.check_assets(out) == [], MOD.check_assets(out)
        # 有地图引用却缺 behaviors → 报错
        path = os.path.join(out, "map_8200000.json")
        doc = json.load(open(path, encoding="utf-8"))
        doc.pop("behaviors")
        write_json(path, doc)
        problems = MOD.check_assets(out)
        assert any("缺 behaviors" in p for p in problems), problems
        # 没有任何地图引用时允许缺 behaviors（如 LAYOUT_UNUSED1）
        doc["maps"] = []
        write_json(path, doc)
        problems = [p for p in MOD.check_assets(out) if "缺 behaviors" in p]
        assert problems == [], problems
        # behaviors 行长度与 w 不一致 → 报错
        doc["maps"] = ["MAP_TEST"]
        doc["behaviors"] = ["02", "01"]
        write_json(path, doc)
        problems = MOD.check_assets(out)
        assert any("behaviors 行内容不对" in p for p in problems), problems
    with_tmp(run)


def test_layout_table_disambiguates_duplicate_content():
    """同内容复制块（两个 blob 地址）：ROM 里的 gMapLayouts 表能精确分到各自地址。"""
    def run(tmp):
        base = 0x08000000
        rom = bytearray(ROM_SIZE)
        # 两个内容相同的 blockdata 副本 + 一份不同内容
        def write_blocks(off, seed):
            for i in range(12):
                v = 0 if i == 1 else 0
                rom[off + i * 2: off + i * 2 + 2] = int(v).to_bytes(2, "little")
            # (1,1) 放碰撞位，让内容带 seed 区分（用 metatile 号）
            rom[off + 5 * 2: off + 5 * 2 + 2] = int(seed).to_bytes(2, "little")
        blocks = (0x100, 0x140, 0x180)
        write_blocks(blocks[0], 0)
        write_blocks(blocks[1], 0)   # 与 A 内容完全相同（复制块）
        write_blocks(blocks[2], 3)   # 唯一内容（锚点）
        border = b"\x01\x00\x02\x00\x03\x00\x04\x00"
        bps = (0x300, 0x320, 0x340)
        for bp in bps:
            rom[bp:bp + 8] = border
        ts = (0x500, 0x520)
        # 三个布局结构体（同宽高，只有 map/border 指针不同）
        structs = []
        for s, mp, bp in ((0x400, blocks[0], bps[0]), (0x440, blocks[1], bps[1]), (0x480, blocks[2], bps[2])):
            rom[s:s + 4] = u32b(4); rom[s + 4:s + 8] = u32b(3)
            rom[s + 8:s + 12] = u32b(base + bp)
            rom[s + 12:s + 16] = u32b(base + mp)
            rom[s + 16:s + 20] = u32b(base + ts[0])
            rom[s + 20:s + 24] = u32b(base + ts[1])
            rom[s + 0x18] = 2; rom[s + 0x19] = 2
            structs.append(base + s)
        # gMapLayouts 表：与 layouts.json 顺序一致
        table = 0x600
        for i, st in enumerate(structs):
            rom[table + 4 * i: table + 4 * i + 4] = u32b(st)

        ref = tmp
        def lay(lid, name, block_off):
            return {
                "id": lid, "name": name + "_Layout", "width": 4, "height": 3,
                "border_width": 2, "border_height": 2,
                "primary_tileset": "gTileset_Primary", "secondary_tileset": "gTileset_Secondary",
                "border_filepath": "data/layouts/%s/border.bin" % lid,
                "blockdata_filepath": "data/layouts/%s/map.bin" % lid,
            }
        entries = [lay("LAYOUT_A", "A", blocks[0]), lay("LAYOUT_B", "B", blocks[1]),
                   lay("LAYOUT_C", "C", blocks[2])]
        for e, mp in zip(entries, blocks):
            d = os.path.join(ref, "data", "layouts", e["id"])
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "map.bin"), "wb") as f:
                f.write(rom[mp:mp + 24])
            with open(os.path.join(d, "border.bin"), "wb") as f:
                f.write(border)
        write_json(os.path.join(ref, "data", "layouts", "layouts.json"),
                   {"layouts_table_label": "gMapLayouts", "layouts": entries})
        make_tilesets(ref)

        mapped, stats = MOD.locate_all(bytes(rom), ref)
        assert stats.get("table"), stats
        assert mapped["LAYOUT_A"] == base + blocks[0], mapped
        assert mapped["LAYOUT_B"] == base + blocks[1], mapped
        assert mapped["LAYOUT_C"] == base + blocks[2], mapped
        assert len(set(mapped.values())) == 3, mapped   # 重复内容也分到不同地址
    with_tmp(run)


if __name__ == "__main__":
    for fn in (test_scan_and_locate_layout_addr, test_conn_edges_rules,
               test_build_links_merges_targets, test_validate_observed_tolerance,
               test_check_assets_schema, test_emit_assets_behaviors_maps_encounters,
               test_check_assets_accepts_behaviors_maps,
               test_door_warps_generate_side_null_edges,
               test_layout_table_disambiguates_duplicate_content, test_help_exit0):
        fn()
    print("全部通过")
