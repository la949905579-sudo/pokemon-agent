"""地图间连接表：记录每张地图的出口坐标和通向哪里。

数据来源：实际走位实测（走出口 -> 记录换图后的新坐标）。

用法：
    import map_links
    map_links.links_from(0x82e9260)      # 该地图的所有出口
    map_links.link_at(0x82e9260, 12, 39) # 指定格子的连接
    map_links.find_route(src_map, dst_map)# 地图级路线（不精确到格子）
"""
import json, os

DATA_FILE = "/root/workspace/map_links.json"

# 实测连接（双向）
# 格式：{"map": 地图地址, "exit": (x,y), "side": "north/south/east/west",
#        "to_map": 目标地图, "to_pos": 目标地图进入坐标}
_LINKS = [
    # 6 号道路 <-> 枯叶市
    {"map": 0x82e9260, "exit": (12, 39), "side": "south",
     "to_map": 0x82e0614, "to_pos": (31, 8)},
    {"map": 0x82e0614, "exit": (24, 0), "side": "north",
     "to_map": 0x82e9260, "to_pos": (19, 45)},
]


def _load():
    global _LINKS
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if data:
                _LINKS = data
    except Exception:
        pass


def save():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(_LINKS, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def add_link(map_addr, exit_xy, to_map, to_pos, side=None):
    """记录一条连接。

    同一出口如果通向不同地图（房间复用），会存成 targets 列表并标记 reused。
    """
    for ln in _LINKS:
        if ln["map"] == map_addr and tuple(ln["exit"]) == tuple(exit_xy):
            ln["side"] = side or ln.get("side")
            if ln.get("to_map") == to_map:
                ln["to_pos"] = list(to_pos)
                save()
                return
            # 多目标（复用房间）
            ts = ln.setdefault("targets", [])
            if not ts and ln.get("to_map"):
                ts.append({"to_map": ln["to_map"], "to_pos": ln.get("to_pos")})
            for t in ts:
                if t["to_map"] == to_map:
                    t["to_pos"] = list(to_pos)
                    break
            else:
                ts.append({"to_map": to_map, "to_pos": list(to_pos)})
            ln["reused"] = True
            save()
            return
    _LINKS.append({
        "map": map_addr, "exit": list(exit_xy), "side": side,
        "to_map": to_map, "to_pos": list(to_pos),
    })
    save()


def links_from(map_addr):
    """该地图的所有出口连接。"""
    return [ln for ln in _LINKS if ln["map"] == map_addr]


def link_at(map_addr, x, y):
    """指定格子的连接（出口）。复用房间会有 targets 列表。"""
    for ln in _LINKS:
        if ln["map"] == map_addr and tuple(ln["exit"]) == (x, y):
            return ln
    return None


def route_maps(src_map, dst_map, max_depth=8):
    """地图级路线（BFS：只返回地图地址序列）。"""
    if src_map == dst_map:
        return [src_map]
    from collections import deque
    q = deque([(src_map, [src_map])])
    seen = {src_map}
    while q:
        cur, path = q.popleft()
        if len(path) > max_depth:
            continue
        for ln in links_from(cur):
            # 复用房间可能有多个目标
            targets = ln.get("targets")
            if targets:
                nxts = [t["to_map"] for t in targets]
            elif ln.get("to_map"):
                nxts = [ln["to_map"]]
            else:
                nxts = []
            for nxt in nxts:
                if nxt == dst_map:
                    return path + [nxt]
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, path + [nxt]))
    return None


_load()
