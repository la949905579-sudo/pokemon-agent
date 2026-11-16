#!/usr/bin/env python3
"""tools/gen_map_assets.py 的离线测试：假 ROM（结构体 + blockdata 字节）验证
地址定位、连接出口/落点规则、多目标合并、实测表校验与资产校验。

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
    return tmp


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
        (0x100, (3, 4), None, 0x200, (5, 6), "warp"),
        (0x100, (3, 4), None, 0x300, (7, 8), "warp"),
        (0x100, (1, 0), "north", 0x200, (1, 9), "conn"),
    ]
    links = MOD.build_links(edges)
    assert len(links) == 2, links
    door = [l for l in links if l["exit"] == [3, 4]][0]
    assert door["to_map"] == 0x200 and door["to_pos"] == [5, 6]
    assert len(door["targets"]) == 2, door
    assert {"to_map": 0x300, "to_pos": [7, 8]} in door["targets"], door


def test_validate_observed_side_diff():
    links = [{"map": 0x100, "exit": [1, 0], "side": "north", "to_map": 0x200, "to_pos": [1, 9]}]
    old = [
        {"map": 0x100, "exit": [1, 0], "side": None, "to_map": 0x200, "to_pos": [1, 9]},  # side 口径不同
        {"map": 0x100, "exit": [2, 2], "side": None, "to_map": 0x200, "to_pos": [0, 0]},  # 未命中
    ]
    hit, side_diff, miss = MOD.validate_observed(links, old)
    assert hit == 1 and len(side_diff) == 1 and len(miss) == 1, (hit, side_diff, miss)


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
    for flag in ("--rom", "--check", "--validate", "--merge-old"):
        assert flag in r.stdout, flag


if __name__ == "__main__":
    for fn in (test_scan_and_locate_layout_addr, test_conn_edges_rules,
               test_build_links_merges_targets, test_validate_observed_side_diff,
               test_check_assets_schema, test_help_exit0):
        fn()
    print("全部通过")
