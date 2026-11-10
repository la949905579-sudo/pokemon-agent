"""地图通行性：定位地图结构、读取地块、输出九宫格。
用法: python3 terrain.py
"""
import sys, struct
sys.path.insert(0, "/root/workspace")
from state import rd, coords

OFF_X, OFF_Y = 7, 7
GRASS_IDS = {13}   # 待确认：高草的地块编号        # 坐标 -> 地块 偏移（实测校准）
_cache = {"addr": None, "w": 0, "h": 0, "hdr": None}
_vals_cache = {"hdr": None, "addr": None, "vals": None}
CACHE_FILE = "/root/workspace/map_cache.txt"
MAP_HDR_PTR = 0x02036DFC   # gMapHeader 指针：换图后值立刻变化（实测室内/室外互切均验证）

def _read_cache():
    try:
        a, w, h = open(CACHE_FILE).read().split()
        return int(a, 16), int(w), int(h)
    except Exception:
        return None

def _write_cache(a, w, h):
    try:
        open(CACHE_FILE, "w").write(f"{a:#x} {w} {h}")
    except Exception:
        pass

def _ewram():
    buf = bytearray()
    for a in range(0x02000000, 0x02040000, 4096):
        d = rd(a, 4096, retries=1)
        buf.extend(d if len(d) == 4096 else b"\0" * 4096)
    return bytes(buf)

def _map_hdr():
    """当前地图 header 指针；换图会变。读不到返回 None。"""
    d = rd(MAP_HDR_PTR, 4)
    if len(d) < 4:
        return None
    return struct.unpack_from("<I", d, 0)[0]


def _from_hdr(hdr):
    """从地图 header 读出 (地块数组地址, 宽, 高)。"""
    hd = rd(hdr, 16)
    if len(hd) < 16:
        return None
    w, h = struct.unpack_from("<ii", hd, 0)
    m = struct.unpack_from("<I", hd, 0x0C)[0]
    if 5 <= w <= 120 and 5 <= h <= 120 and m:
        return m, w, h
    return None


def locate_map(force=False):
    """返回 (map数组地址, 宽, 高)。

    首选 gMapHeader 指针：换图后它立刻变，1 次 UDP 就能判断，不用扫 EWRAM。
    读不到 / 不合法时才回退到 EWRAM 扫描（慢，约 4 秒）。
    """
    if not force:
        hdr = _map_hdr()
        if hdr:
            if _cache["addr"] and _cache["hdr"] == hdr:
                return _cache["addr"], _cache["w"], _cache["h"]
            r = _from_hdr(hdr)
            if r:
                _cache.update(addr=r[0], w=r[1], h=r[2], hdr=hdr)
                _write_cache(hdr, r[1], r[2])
                return r
    buf = _ewram()
    ptrs = sorted({struct.unpack_from("<I", buf, i)[0]
                   for i in range(0, len(buf) - 4, 4)} & set(range(0x08000000, 0x0A000000)))
    for p in ptrs:
        d = rd(p, 20)
        if len(d) < 20:
            continue
        w, h = struct.unpack_from("<ii", d, 0)
        m = struct.unpack_from("<I", d, 0x0C)[0]
        if 5 <= w <= 120 and 5 <= h <= 120 and (0x08000000 <= m < 0x0A000000 or 0x02000000 <= m < 0x02040000):
            _cache.update(addr=m, w=w, h=h, hdr=p)
            _write_cache(p, w, h)
            return m, w, h
    return None, 0, 0

def _sane(addr, w, h, vals):
    """校验：角色当前所在格必须是可走的，否则说明地图不是当前的。"""
    from state import coords
    p = coords()
    if not p or not vals:
        return True
    tx, ty = p[0] - OFF_X, p[1] - OFF_Y
    if not (0 <= tx < w and 0 <= ty < h):
        return False
    return walkable(vals, w, tx, ty)

_last_pos = {"p": None}

def _check_warp():
    """坐标剧变（>5 格）视为换图，强制重扫地图，避免用旧图导航。"""
    from state import coords as _c
    p = _c()
    lp = _last_pos["p"]
    _last_pos["p"] = p
    if p and lp and (abs(p[0]-lp[0]) > 5 or abs(p[1]-lp[1]) > 5):
        locate_map(force=True)

def load():
    global _cur_addr
    # 换图由 locate_map 里的 gMapHeader 指针检测，不再靠坐标剧变
    addr, w, h = locate_map()
    if not addr:
        return None, 0, 0, None
    # 同一张地图（addr+hdr 都没变）直接复用上次解析结果，省一次 1920 字节 UDP
    hdr = _cache.get("hdr")
    if (_vals_cache["addr"] == addr and _vals_cache["hdr"] == hdr
            and _vals_cache["vals"] is not None):
        _cur_addr = addr
        return addr, w, h, _vals_cache["vals"]
    _cur_addr = addr
    d = rd(addr, w * h * 2)
    if len(d) < w * h * 2:
        return None, w, h, None
    vals = [struct.unpack_from("<H", d, i * 2)[0] for i in range(w * h)]
    if not _sane(addr, w, h, vals):
        addr, w, h = locate_map(force=True)
        if not addr:
            return None, w, h, None
        _cur_addr = addr
        d = rd(addr, w * h * 2)
        if len(d) < w * h * 2:
            return None, w, h, None
        vals = [struct.unpack_from("<H", d, i * 2)[0] for i in range(w * h)]
    _vals_cache.update(addr=addr, hdr=_cache.get("hdr"), vals=vals)
    _save_cache(addr, w, h, vals)
    return addr, w, h, vals

def _save_cache(addr, w, h, vals):
    """把地图数据存到 map_cache/<addr>.json，供多图拼接使用（同一地图只存一次）。"""
    import json, os
    try:
        d = "/root/workspace/map_cache"
        os.makedirs(d, exist_ok=True)
        fn = os.path.join(d, f"{addr:08x}.json")
        if os.path.exists(fn):
            return
        with open(fn, "w") as f:
            json.dump({"addr": addr, "w": w, "h": h, "vals": list(vals)}, f)
    except Exception:
        pass


def is_grass(vals, w, x, y):
    if not (0 <= x < w and 0 <= y < len(vals) // w):
        return False
    return (vals[y * w + x] & 0x3FF) in GRASS_IDS

TREE_SAPLING = 317   # 小树苗：需要居合斩，当前不可走

# 运行时校正层：数据说可走、实际走不动的格（按地图地址持久化）
_cur_addr = None
_overrides = {}


def _override_path(addr):
    return f"/root/workspace/maps/override_{addr:x}.json"


def _load_overrides(addr):
    import json, os
    if addr in _overrides:
        return _overrides[addr]
    d = {"blocked": []}
    try:
        with open(_override_path(addr), encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        pass
    _overrides[addr] = {"blocked": {tuple(p) for p in d.get("blocked", [])}}
    return _overrides[addr]


def mark_blocked(x, y, addr=None):
    """记录「数据说可走、实际走不动」的格（供下次寻路绕开）。"""
    import json
    addr = addr or _cur_addr
    if not addr:
        return
    ov = _load_overrides(addr)
    ov["blocked"].add((x, y))
    try:
        with open(_override_path(addr), "w", encoding="utf-8") as f:
            json.dump({"blocked": sorted([list(p) for p in ov["blocked"]])}, f,
                      ensure_ascii=False)
    except Exception:
        pass


def walkable(vals, w, x, y):
    if not (0 <= x < w and 0 <= y < len(vals) // w):
        return False
    v = vals[y * w + x]
    if (v & 0x3FF) == TREE_SAPLING:
        return False
    if _cur_addr:
        ov = _load_overrides(_cur_addr)
        if (x, y) in ov["blocked"]:
            return False
    return ((v >> 10) & 3) == 0


OBJ_BASE = 0x02036E38
OBJ_SIZE = 0x24
OBJ_MAX  = 16

def npc_tiles():
    """返回 {(tile_x, tile_y)}：活动对象（NPC/物体）占的格子。"""
    out = set()
    for i in range(1, OBJ_MAX):          # 0 是玩家自己
        d = rd(OBJ_BASE + i * OBJ_SIZE, OBJ_SIZE)
        if len(d) < OBJ_SIZE:
            continue
        active = d[0]
        if not active:
            continue
        x, y = struct.unpack_from("<hh", d, 0x10)
        if 0 < x < 200 and 0 < y < 200:
            out.add((x - OFF_X, y - OFF_Y))
    return out

if __name__ == "__main__":
    p = coords()
    addr, w, h, vals = load()
    if not vals:
        print("读不到地图数据"); sys.exit(1)
    tx, ty = p[0] - OFF_X, p[1] - OFF_Y
    print(f"地图 {addr:#x} {w}x{h}  坐标 {p} -> 地块 ({tx},{ty})")
    npcs = npc_tiles()
    for dy in (-1, 0, 1):
        row = []
        for dx in (-1, 0, 1):
            gx, gy = tx + dx, ty + dy
            ok = walkable(vals, w, gx, gy)
            if dx == 0 and dy == 0:
                row.append("@")
            elif (gx, gy) in npcs:
                row.append("N")
            elif not ok:
                row.append("#")
            elif is_grass(vals, w, gx, gy):
                row.append("G")
            else:
                row.append(".")
        print(" ".join(row))
    print("NPC 格子:", sorted(npcs) if npcs else "无")
