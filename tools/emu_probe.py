#!/usr/bin/env python3
"""真机招式取证（合同 C3 §6②）：读 MY_BATTLE+0x0C 的 4 个 u16 招式 id，对照 bdata.MOVES。

用法：
    python3 tools/emu_probe.py --check-move 232 [--expect-name 金属爪]

行为：
- 经 `emu_bridge.rd`（TCP :55401，只读）读 8 字节 = 4 个 u16（GBA 小端）招式 id；
- 命中且名字可核对 → 输出**恰好一行** `PASS <id> <name>`，exit 0；
- 未命中 / 名字不符 / 未知 id / 读取失败 → 输出**恰好一行** `FAIL <id> <name>`，exit 1；
- 名字取 `bdata.MOVES[id][0]`，表里没有写「未知」。

截图约定（本工具**只给约定，不写文件、不截屏**）：
    /sdcard/Download/DSH-Go/probe-<id>-<ts>.jpg  ← 常量 `SHOT_DIR` + `shot_path()`

离线可测：模块 import 时不连 TCP、不读内存；真实读取只在 CLI 里经 `emu_bridge.rd` 发生，
判定走 `judge(read_fn, ...)`，测试可注入任意 `read_fn(addr, n) -> bytes`。
"""
import argparse
import collections
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SHOT_DIR = "/sdcard/Download/DSH-Go"   # 截图目录约定（真机执行回路径，工具不截屏）
MOVE_OFFSET = 0x0C                     # MY_BATTLE+0x0C = 4 招(u16)
SLOT_COUNT = 4
SLOT_SIZE = 2
SLOT_BYTES = SLOT_COUNT * SLOT_SIZE
UNKNOWN_NAME = "未知"

# ok=True/False；move_id 待核对 id；name 招式名；slots 读到的 4 个 id
ProbeResult = collections.namedtuple("ProbeResult", "ok move_id name slots")


def move_addr():
    """返回 MY_BATTLE+0x0C（延迟 import，保证模块 import 不碰地址表/内存）。"""
    import addresses
    return addresses.MY_BATTLE + MOVE_OFFSET


def parse_slots(raw):
    """8 字节 → 4 个 u16 招式 id（GBA 小端）；不足 8 字节抛 ValueError。"""
    if raw is None:
        raise ValueError("没有读到数据")
    raw = bytes(raw)
    if len(raw) < SLOT_BYTES:
        raise ValueError("读取不足：%d/%d 字节" % (len(raw), SLOT_BYTES))
    return struct.unpack("<4H", raw[:SLOT_BYTES])


def read_slots(read_fn):
    """经注入的 read_fn 读 4 招；read_fn(addr, n) -> bytes。"""
    return parse_slots(read_fn(move_addr(), SLOT_BYTES))


def move_name(move_id):
    """bdata.MOVES 里的中文名；未知 id 返回「未知」。"""
    import bdata
    info = bdata.MOVES.get(int(move_id))
    return info[0] if info else UNKNOWN_NAME


def judge(read_fn, move_id, expect_name=None):
    """纯判定（离线可测）：4 招里命中该 id，且名字可核对/与期望一致 → ok。"""
    slots = read_slots(read_fn)
    name = move_name(move_id)
    hit = int(move_id) in slots
    known = name != UNKNOWN_NAME
    name_ok = expect_name is None or expect_name == name
    return ProbeResult(ok=bool(hit and known and name_ok), move_id=int(move_id),
                       name=name, slots=slots)


def format_line(ok, move_id, name):
    """恰好一行的 PASS/FAIL 行（协议固定，供真机执行原样回执）。"""
    return "%s %d %s" % ("PASS" if ok else "FAIL", int(move_id), name)


def shot_path(move_id, ts):
    """截图路径约定：/sdcard/Download/DSH-Go/probe-<id>-<ts>.jpg（只算路径，不写文件）。"""
    return os.path.join(SHOT_DIR, "probe-%d-%s.jpg" % (int(move_id), ts))


def build_parser():
    ap = argparse.ArgumentParser(
        prog="emu_probe.py",
        description="真机招式取证：读 MY_BATTLE+0x0C 的 4 个 u16 招式 id，"
                    "对照 bdata.MOVES，输出一行 PASS<id><name> / FAIL<id><name>。",
        epilog="截图约定：%s/probe-<id>-<ts>.jpg（只给路径，不写文件、不截屏）" % SHOT_DIR,
    )
    ap.add_argument("--check-move", type=int, required=True, metavar="ID",
                    help="要核对的招式 id（如 232 = 金属爪）")
    ap.add_argument("--expect-name", default=None, metavar="名",
                    help="期望招式名（不符则 FAIL）")
    return ap


def main(argv=None, read_fn=None):
    """CLI 入口；返回值即 exit code（0=PASS / 1=FAIL）。测试可注入 read_fn。"""
    args = build_parser().parse_args(argv)
    if read_fn is None:
        import emu_bridge
        read_fn = emu_bridge.rd
    try:
        res = judge(read_fn, args.check_move, args.expect_name)
    except Exception:
        print(format_line(False, args.check_move, UNKNOWN_NAME))
        return 1
    print(format_line(res.ok, res.move_id, res.name))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
