#!/usr/bin/env python3
"""tools/gen_maps_data.py 的离线测试：在临时目录里造一个最小「解包仓库」，
验证碰撞位解析、尺寸校验、--match 交叉校验、--emit 输出与 --check 校验。

不依赖 /root/refs/pokefirered，也不联网。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "tools", "gen_maps_data.py")


def load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = load("gen_maps_data", SCRIPT)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def write_bin(path, blocks):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        for b in blocks:
            f.write(bytes((b & 0xFF, (b >> 8) & 0xFF)))


def write_tilesets(base):
    """补 tileset 属性表与行为常量（primary/secondary 各几百字节）。"""
    write_json(os.path.join(base, "src", "data", "tilesets", "metatiles.h"), {}) if False else None
    os.makedirs(os.path.join(base, "src", "data", "tilesets"), exist_ok=True)
    with open(os.path.join(base, "src", "data", "tilesets", "metatiles.h"), "w", encoding="utf-8") as f:
        f.write('const u32 gMetatileAttributes_TestPrimary[] = INCBIN_U32("data/tilesets/primary/test/metatile_attributes.bin");\n')
        f.write('const u32 gMetatileAttributes_TestSecondary[] = INCBIN_U32("data/tilesets/secondary/test/metatile_attributes.bin");\n')
    os.makedirs(os.path.join(base, "include", "constants"), exist_ok=True)
    with open(os.path.join(base, "include", "constants", "metatile_behaviors.h"), "w", encoding="utf-8") as f:
        f.write("#define MB_NORMAL 0x00\n#define MB_TALL_GRASS 0x02\n")
    # 遭遇表（叶绿/火红各一条，验证只取 _LeafGreen）+ 物种常量
    write_json(os.path.join(base, "src", "data", "wild_encounters.json"), {
        "wild_encounter_groups": [{
            "label": "gWildMonHeaders",
            "for_maps": True,
            "fields": [{"type": "land_mons",
                        "encounter_rates": [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1]}],
            "encounters": [
                {"map": "MAP_TEST", "base_label": "sTest_LeafGreen",
                 "land_mons": {"mons": [{"min_level": 2, "max_level": 3, "species": "SPECIES_PIDGEY"},
                                       {"min_level": 2, "max_level": 2, "species": "SPECIES_UNOWN_B"}]}},
                {"map": "MAP_TEST", "base_label": "sTest_FireRed",
                 "land_mons": {"mons": [{"min_level": 9, "max_level": 9, "species": "SPECIES_PIDGEY"}]}},
            ],
        }]
    })
    with open(os.path.join(base, "include", "constants", "species.h"), "w", encoding="utf-8") as f:
        f.write("#define SPECIES_NONE 0\n#define SPECIES_EGG 412\n")
        f.write("#define NUM_SPECIES SPECIES_EGG\n")
        f.write("#define SPECIES_PIDGEY 16\n#define SPECIES_UNOWN_B (NUM_SPECIES + 1)\n")
    # primary：metatile 0 普通、1 高草；secondary：metatile 640 普通
    for rel, attrs in (("data/tilesets/primary/test/metatile_attributes.bin", [0x000, 0x002]),
                       ("data/tilesets/secondary/test/metatile_attributes.bin", [0x000])):
        path = os.path.join(base, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            for v in attrs:
                f.write(v.to_bytes(4, "little"))


def make_ref(base):
    """造最小解包仓库：1 个 4x3 布局（含碰撞位）+ 1 个 {} 占位 + 1 张地图。"""
    layout = {
        "id": "LAYOUT_TEST",
        "name": "Test_Layout",
        "width": 4,
        "height": 3,
        "border_width": 2,
        "border_height": 2,
        "primary_tileset": "gTileset_TestPrimary",
        "secondary_tileset": "gTileset_TestSecondary",
        "border_filepath": "data/layouts/Test/border.bin",
        "blockdata_filepath": "data/layouts/Test/map.bin",
    }
    write_json(os.path.join(base, "data", "layouts", "layouts.json"),
               {"layouts_table_label": "gMapLayouts", "layouts": [{}, layout]})
    write_tilesets(base)
    # 4x3：只有 (1,1) 和 (3,0) 带碰撞位（0x0400），其余可走
    blocks = [0] * 12
    blocks[1 * 4 + 1] = 0x0400
    blocks[0 * 4 + 3] = 0x0800
    write_bin(os.path.join(base, "data", "layouts", "Test", "map.bin"), blocks)
    write_json(os.path.join(base, "data", "maps", "TestMap", "map.json"), {
        "id": "MAP_TEST",
        "name": "TestMap",
        "layout": "LAYOUT_TEST",
        "connections": [{"map": "MAP_OTHER", "offset": 3, "direction": "up"}],
        "warp_events": [{"x": 1, "y": 2, "dest_map": "MAP_OTHER", "dest_warp_id": "0"}],
    })
    return base


def make_repo(base, tiles):
    path = os.path.join(base, "games", "pokemon_firered", "maps", "map_deadbeef.json")
    write_json(path, {"addr": "0xdeadbeef", "w": 4, "h": 3, "tiles": tiles})
    # 只有链接表、没有可走格的 JSON 应被跳过
    write_json(os.path.join(base, "games", "pokemon_firered", "maps", "map_links.json"),
               {"links": []})
    return base


TEST_TILES = [
    [0, 0, 0, 1],
    [0, 1, 0, 0],
    [0, 0, 0, 0],
]


def with_tmp(fn):
    d = tempfile.mkdtemp(prefix="maps_data_")
    try:
        return fn(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_build_grid_uses_collision_bits():
    def run(tmp):
        ref = make_ref(tmp)
        layouts = MOD.load_layouts(ref)
        assert "LAYOUT_TEST" in layouts and "" not in layouts  # {} 占位被跳过
        grid = MOD.build_grid(ref, layouts["LAYOUT_TEST"])
        assert grid == TEST_TILES, grid
    with_tmp(run)


def test_build_grid_wrong_size_raises():
    def run(tmp):
        ref = make_ref(tmp)
        write_bin(os.path.join(ref, "data", "layouts", "Test", "map.bin"), [0] * 5)
        layouts = MOD.load_layouts(ref)
        try:
            MOD.build_grid(ref, layouts["LAYOUT_TEST"])
        except ValueError:
            return
        raise AssertionError("尺寸不符应抛 ValueError")
    with_tmp(run)


def test_match_existing_finds_exact_layout():
    def run(tmp):
        ref = make_ref(tmp)
        repo = make_repo(tmp, TEST_TILES)
        rows = MOD.match_existing(ref, repo)
        assert len(rows) == 1, rows
        r = rows[0]
        assert r["file"] == "map_deadbeef.json", r
        assert r["best"] == "LAYOUT_TEST" and r["diff"] == 0, r
        assert r["exact_candidates"] == 1, r
    with_tmp(run)


def test_emit_and_check_roundtrip():
    def run(tmp):
        ref = make_ref(tmp)
        repo = make_repo(tmp, TEST_TILES)
        out = os.path.join(tmp, "out")
        paths = MOD.emit(ref, ["MAP_TEST"], out, repo)
        assert len(paths) == 1 and os.path.isfile(paths[0]), paths
        doc = json.load(open(paths[0], encoding="utf-8"))
        assert doc["id"] == "MAP_TEST" and doc["layout"] == "LAYOUT_TEST", doc
        assert doc["tiles"] == TEST_TILES, doc["tiles"]
        assert doc["connections"] and doc["warps"], doc
        assert doc["ram_crosscheck"] == {"file": "map_deadbeef.json", "diff": 0}, doc["ram_crosscheck"]
        assert MOD.check(out, expected={"MAP_TEST": (4, 3, "LAYOUT_TEST")}) == []
    with_tmp(run)


def test_check_reports_problems():
    def run(tmp):
        ref = make_ref(tmp)
        out = os.path.join(tmp, "out")
        MOD.emit(ref, ["MAP_TEST"], out, None)
        path = os.path.join(out, "TestMap.json")
        doc = json.load(open(path, encoding="utf-8"))
        doc["w"] = 99
        doc["tiles"][0][0] = 7
        write_json(path, doc)
        problems = MOD.check(out, expected={"MAP_TEST": (4, 3, "LAYOUT_TEST")})
        assert any("尺寸" in p for p in problems), problems
        assert any("非 0/1" in p for p in problems), problems
    with_tmp(run)


def test_emit_unknown_map_exits():
    def run(tmp):
        ref = make_ref(tmp)
        try:
            MOD.emit(ref, ["MAP_NOPE"], os.path.join(tmp, "out"), None)
        except SystemExit:
            return
        raise AssertionError("未知地图应 SystemExit")
    with_tmp(run)


def make_ref_multi(base):
    """两张地图共用同一布局（验证 grid 缓存）+ 一张重名地图（验证文件名回退 id）。"""
    layout = {
        "id": "LAYOUT_TEST", "name": "Test_Layout", "width": 2, "height": 2,
        "border_width": 2, "border_height": 2,
        "primary_tileset": "gTileset_TestPrimary", "secondary_tileset": "gTileset_TestSecondary",
        "border_filepath": "data/layouts/Test/border.bin",
        "blockdata_filepath": "data/layouts/Test/map.bin",
    }
    write_json(os.path.join(base, "data", "layouts", "layouts.json"),
               {"layouts_table_label": "gMapLayouts", "layouts": [{}, layout]})
    write_tilesets(base)
    # 2x2：只有 (0,0) 带碰撞位
    write_bin(os.path.join(base, "data", "layouts", "Test", "map.bin"), [0x0400, 0, 0, 0])
    for mid, name in (("MAP_A", "Alpha"), ("MAP_B", "Beta"), ("MAP_C", "Alpha")):
        write_json(os.path.join(base, "data", "maps", name + "_" + mid, "map.json"),
                   {"id": mid, "name": name, "layout": "LAYOUT_TEST",
                    "connections": [], "warp_events": []})
    return base


def test_emit_all_and_check_against_ref():
    def run(tmp):
        ref = make_ref_multi(tmp)
        out = os.path.join(tmp, "out")
        data = os.path.join(tmp, "data")
        paths = MOD.emit_all(ref, out, None, data_dir=data)
        names = sorted(os.path.basename(p) for p in paths if p.endswith(".json") and os.path.dirname(p) == out)
        # 两张 Alpha 重名：一张用地图名，另一张回退地图 id
        assert names == ["Alpha.json", "Beta.json", "MAP_C.json"], names
        doc = json.load(open(os.path.join(out, "Beta.json"), encoding="utf-8"))
        assert doc["tiles"] == [[1, 0], [0, 0]], doc["tiles"]
        assert MOD.check(out, ref=ref, data_dir=data, with_extras=True) == []
        # 尺寸/布局/内容任一不符都要报问题
        doc["tiles"][0][0] = 5
        write_json(os.path.join(out, "Beta.json"), doc)
        problems = MOD.check(out, ref=ref, data_dir=data, with_extras=True)
        assert any("非 0/1" in p for p in problems), problems
        # 解包里没有的 id 也要报
        write_json(os.path.join(out, "Ghost.json"), {"id": "MAP_GHOST", "w": 2, "h": 2,
                                                     "tiles": [[0, 0], [0, 0]],
                                                     "connections": [], "warps": []})
        problems = MOD.check(out, ref=ref, data_dir=data, with_extras=True)
        assert any("解包 maps 里没有" in p for p in problems), problems
    with_tmp(run)


def test_encounters_leafgreen_only_and_species_resolution():
    def run(tmp):
        ref = make_ref(tmp)
        doc = MOD.build_encounters(ref)
        assert doc["version"] == "leafgreen", doc
        m = doc["maps"]["MAP_TEST"]["land"]
        assert len(m["slots"]) == 2, m
        first, second = m["slots"]
        assert first["species"] == 16 and first["min"] == 2 and first["max"] == 3, first
        assert first["chance"] == 20, first          # 概率来自 fields.encounter_rates
        assert second["species"] == 413, second      # (NUM_SPECIES + 1) = 412 + 1
        # 没有把火红那条（lv9）混进来
        assert all(s["max"] != 9 for s in m["slots"]), m
    with_tmp(run)


def test_help_and_offline_check():
    r = subprocess.run([sys.executable, SCRIPT, "--help"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-300:]
    for flag in ("--match", "--emit", "--check", "--ref"):
        assert flag in r.stdout, flag
    # --check 不读解包仓库：故意给不存在的 ref，仍能跑（只校验输出目录）
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, SCRIPT, "--check", "--out", tmp],
                           capture_output=True, text=True)
        assert r.returncode == 1 and "FAIL" in r.stdout, (r.returncode, r.stdout[-300:])


if __name__ == "__main__":
    for fn in (test_build_grid_uses_collision_bits, test_build_grid_wrong_size_raises,
               test_match_existing_finds_exact_layout, test_emit_and_check_roundtrip,
               test_check_reports_problems, test_emit_unknown_map_exits,
               test_emit_all_and_check_against_ref, test_encounters_leafgreen_only_and_species_resolution,
               test_help_and_offline_check):
        fn()
    print("全部通过")
