"""队伍槽解码的共享纯函数（无 IO、不 import state/bdata，消掉循环依赖）。

为什么单独一个模块：`state.py` 的战斗状态校验要看「我方队伍 species 集合」，
而队伍解码原来只写在 `bdata.my_mon()` 里 → `state` 函数内 `import bdata`，
`bdata` 又在模块级 `from state import rd, PARTY_ADDR`，形成环（STRUCTURE §三 违规）。
现在两边都从这里取：
- `state` → `party_species(read_fn, addr)`（只读 species，用于校验）
- `bdata` → `mon_from_bytes(slot, d)`（完整解码后再补属性表）

约束：
- 本模块只做字节解析，不读内存、不写文件、不打日志；
- 地址常量只从 `addresses.py` 取（唯一真源），别再复制一份。
"""
import struct

PARTY_MON_SIZE = 100   # 队伍槽固定 100 字节（实测）

# 加密后 48 字节四个子结构的排列（按 pid % 24 取）
_SUBSTRUCT_TABLE = [
    "GAEM", "GAME", "GEAM", "GEMA", "GMAE", "GMEA",
    "AGEM", "AGME", "AEGM", "AEMG", "AMGE", "AMEG",
    "EGAM", "EGMA", "EAGM", "EAMG", "EMGA", "EMAG",
    "MGAE", "MGEA", "MAGE", "MAEG", "MEGA", "MEAG",
]


def mon_from_bytes(slot, d):
    """100 字节队伍槽 → 等级/HP/招式/PP/species；长度不足返回 None。

    只做解码，不带属性（属性表在 bdata.SPECIES_TYPES，避免这里反向依赖）。
    """
    if not d or len(d) < PARTY_MON_SIZE:
        return None
    lv = d[0x54]
    hp, mhp = struct.unpack_from("<HH", d, 0x56)
    pid = struct.unpack_from("<I", d, 0)[0]
    otid = struct.unpack_from("<I", d, 4)[0]
    key = pid ^ otid
    raw = d[0x20:0x20 + 48]
    words = [struct.unpack_from("<I", raw, i)[0] ^ key for i in range(0, 48, 4)]
    sb = b"".join(struct.pack("<I", w) for w in words)
    seq = _SUBSTRUCT_TABLE[pid % 24]
    ai = seq.index("A")
    att = sb[ai * 12:(ai + 1) * 12]
    moves = [struct.unpack_from("<H", att, j * 2)[0] for j in range(4)]
    pp = list(att[8:12])
    # growth 子结构的第 1 个 u16 是 species
    gi = seq.index("G")
    growth = sb[gi * 12:(gi + 1) * 12]
    species = struct.unpack_from("<H", growth, 0)[0]
    return {"slot": slot, "lv": lv, "hp": hp, "mhp": mhp,
            "moves": moves, "pp": pp, "species": species}


def party_species(read_fn, party_addr, slots=6):
    """读队伍前 slots 只的 species 集合（读不到的槽跳过）。

    read_fn(addr, n) 由调用方注入（state.rd），本模块不直接碰内存层。
    """
    out = set()
    for i in range(slots):
        try:
            d = read_fn(party_addr + i * PARTY_MON_SIZE, PARTY_MON_SIZE)
        except Exception:
            continue
        m = mon_from_bytes(i, d)
        if m:
            out.add(m["species"])
    return out
