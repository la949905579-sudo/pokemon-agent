"""离线测试：队伍槽解码共享模块（消循环依赖后，解码逻辑的单一真源）。

不读实机：自己按「pid/otid 异或加密 + 子结构排列」构造 100 字节槽，
再交给 bdata_shared.mon_from_bytes 解回来，验证等级/HP/招式/PP/物种。
"""
import struct
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))

from bdata_shared import PARTY_MON_SIZE, mon_from_bytes, party_species, _SUBSTRUCT_TABLE


def make_slot(pid, otid, lv, hp, mhp, species, moves, pp, slot_pad=0):
    """按火红的加密规则构造一个队伍槽（100 字节）。"""
    key = pid ^ otid
    seq = _SUBSTRUCT_TABLE[pid % 24]
    blocks = {
        "G": struct.pack("<H", species) + b"\x00" * 10,
        "A": struct.pack("<4H", *moves) + struct.pack("<4B", *pp),
        "E": b"\x00" * 12,
        "M": b"\x00" * 12,
    }
    plain = b"".join(blocks[c] for c in seq)
    words = [struct.unpack_from("<I", plain, i)[0] ^ key for i in range(0, 48, 4)]
    raw = b"".join(struct.pack("<I", w) for w in words)

    d = bytearray(PARTY_MON_SIZE + slot_pad)
    struct.pack_into("<I", d, 0, pid)
    struct.pack_into("<I", d, 4, otid)
    d[0x20:0x20 + 48] = raw
    d[0x54] = lv
    struct.pack_into("<HH", d, 0x56, hp, mhp)
    return bytes(d)


def test_decode_known_slot():
    moves = [52, 53, 54, 0]          # 火花 / 喷射火焰 / 白雾 / 空
    pp = [25, 15, 30, 0]
    d = make_slot(pid=100, otid=7, lv=36, hp=88, mhp=120,
                  species=6, moves=moves, pp=pp)   # 6 = 喷火龙
    m = mon_from_bytes(3, d)
    assert m is not None
    assert m["slot"] == 3 and m["lv"] == 36
    assert (m["hp"], m["mhp"]) == (88, 120)
    assert m["species"] == 6
    assert m["moves"] == moves
    assert m["pp"] == pp
    print("A 已知槽解码 ok", m["species"], m["moves"], m["pp"])


def test_decode_other_substructure_order():
    # pid % 24 = 0 → GAEM；再换一个 pid 覆盖不同排列
    for pid, otid in ((24, 3), (7, 11), (1, 1)):
        d = make_slot(pid=pid, otid=otid, lv=5, hp=20, mhp=20,
                      species=25, moves=[84, 85, 86, 87], pp=[30, 15, 20, 10])
        m = mon_from_bytes(0, d)
        assert m and m["species"] == 25 and m["moves"] == [84, 85, 86, 87], (pid, m)
    print("B 多种子结构排列都解对 ok")


def test_short_slot_returns_none():
    assert mon_from_bytes(0, b"") is None
    assert mon_from_bytes(0, b"\x00" * 99) is None
    assert mon_from_bytes(0, b"\x00" * 100) is not None   # 全零也是合法 0 号物种
    print("C 长度不足返回 None ok")


def test_party_species_uses_injected_reader():
    d0 = make_slot(pid=100, otid=7, lv=36, hp=1, mhp=1, species=6,
                   moves=[0, 0, 0, 0], pp=[0, 0, 0, 0])
    d1 = make_slot(pid=24, otid=3, lv=5, hp=1, mhp=1, species=25,
                   moves=[0, 0, 0, 0], pp=[0, 0, 0, 0])
    slots = {0: d0, 1: d1}

    def fake_rd(addr, n):
        base = 0x02024284
        idx = (addr - base) // PARTY_MON_SIZE
        return slots.get(idx, b"")

    got = party_species(fake_rd, 0x02024284)
    assert got == {6, 25}, got
    print("D party_species 注入读取 ok", got)


test_decode_known_slot()
test_decode_other_substructure_order()
test_short_slot_returns_none()
test_party_species_uses_injected_reader()
print("全部通过")
