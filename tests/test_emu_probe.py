#!/usr/bin/env python3
"""tools/emu_probe.py 的离线测试（注入 read_fn / 直接喂字节，不连 TCP、不读内存）。"""
import contextlib
import importlib.util
import io
import os
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBE = os.path.join(ROOT, "tools", "emu_probe.py")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = load("emu_probe", PROBE)
import addresses  # noqa: E402  （常量表，只读）


def slots(*ids):
    return struct.pack("<4H", *ids)


def run_main(argv, raw):
    """跑 MOD.main 并捕获 stdout；read_fn 注入固定字节。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = MOD.main(argv, read_fn=lambda addr, n: raw)
    return rc, buf.getvalue()


def test_hit_pass_232_metal_claw():
    """命中 232 + 期望名一致 → PASS 232 金属爪，exit 0，恰好一行。"""
    seen = {}

    def fake_read(addr, n):
        seen["addr"], seen["n"] = addr, n
        return slots(52, 33, 98, 232)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = MOD.main(["--check-move", "232", "--expect-name", "金属爪"], read_fn=fake_read)
    out = buf.getvalue()
    assert rc == 0, rc
    assert out == "PASS 232 金属爪\n", repr(out)
    assert seen["addr"] == addresses.MY_BATTLE + 0x0C, seen
    assert seen["n"] == 8, seen


def test_miss_fail_232():
    """4 招里没有 232 → FAIL 232 金属爪，exit 非 0。"""
    rc, out = run_main(["--check-move", "232"], slots(52, 33, 98, 65))
    assert rc != 0, rc
    assert out == "FAIL 232 金属爪\n", repr(out)


def test_expect_name_mismatch_fail():
    """命中 232 但 --expect-name 不符 → FAIL（名字仍是真实名）。"""
    rc, out = run_main(["--check-move", "232", "--expect-name", "火花"], slots(232, 33, 98, 65))
    assert rc != 0, rc
    assert out == "FAIL 232 金属爪\n", repr(out)


def test_unknown_id_and_shot_path():
    """未知 id → FAIL + 「未知」；截图路径只按约定拼出，不写文件。"""
    rc, out = run_main(["--check-move", "9999"], slots(9999, 33, 98, 65))
    assert rc != 0, rc
    assert out == "FAIL 9999 未知\n", repr(out)
    assert MOD.SHOT_DIR == "/sdcard/Download/DSH-Go"
    p = MOD.shot_path(232, "20261114-0900")
    assert p == "/sdcard/Download/DSH-Go/probe-232-20261114-0900.jpg", p
    assert not os.path.exists(p), "只给路径约定，不允许写文件"


def test_help_exit0_contains_check_move():
    """--help exit 0 且含 --check-move（合同 §7.1 M1）。"""
    r = subprocess.run([sys.executable, PROBE, "--help"], capture_output=True, text=True)
    assert r.returncode == 0, (r.returncode, r.stderr[-300:])
    assert "--check-move" in r.stdout, r.stdout


def test_parse_slots_little_endian_and_short():
    """8 字节按小端解 4 个 u16；不足 8 字节抛 ValueError。"""
    assert MOD.parse_slots(b"\x34\x00\x21\x00\x62\x00\xe8\x00") == (52, 33, 98, 232)
    try:
        MOD.parse_slots(b"\x01\x02")
    except ValueError:
        pass
    else:
        raise AssertionError("短读应抛 ValueError")


if __name__ == "__main__":
    for fn in (test_hit_pass_232_metal_claw, test_miss_fail_232,
               test_expect_name_mismatch_fail, test_unknown_id_and_shot_path,
               test_help_exit0_contains_check_move, test_parse_slots_little_endian_and_short):
        fn()
    print("全部通过")
