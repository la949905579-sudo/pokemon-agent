"""全局地图坐标系：把每张地图的局部坐标（0..w, 0..h）映射到统一坐标系。

游戏里读到的是「局部坐标」（每张地图独立）。
拼接/跨图规划需要「全局坐标」——所有地图放在同一个平面里。

用法：
    import map_coords
    gx, gy = map_coords.to_global(0x82e9260, 12, 39)   # 局部 -> 全局
    mx, my = map_coords.to_local(0x82e9260, gx, gy)    # 全局 -> 局部
    map_coords.offset_of(0x82e9260)                    # 该地图的全局偏移
    map_coords.map_at(gx, gy)                          # 全局坐标属于哪张地图
"""
import map_links
from collections import deque

# 地图地址 -> (offset_x, offset_y)：局部 (0,0) 对应的全局坐标
_offsets = {}
# 全局坐标 -> 地图地址的占位范围（用于 map_at）
_ranges = []


def rebuild():
    """从连接表重新计算所有地图的偏移（BFS 传播）。"""
    global _offsets, _ranges
    adj = {}
    for ln in map_links._LINKS:
        a = ln["map"]
        ex, ey = ln["exit"]
        targets = ln.get("targets") or (
            [{"to_map": ln["to_map"], "to_pos": ln["to_pos"]}] if ln.get("to_map") else [])
        for t in targets:
            b = t["to_map"]
            bx, by = t["to_pos"]
            adj.setdefault(a, []).append(((ex, ey), b, (bx, by)))
            adj.setdefault(b, []).append(((bx, by), a, (ex, ey)))  # 反向

    _offsets = {}
    if not adj:
        return
    start = min(adj)
    _offsets[start] = (0, 0)
    q = deque([start])
    while q:
        a = q.popleft()
        ax, ay = _offsets[a]
        for (ex, ey), b, (bx, by) in adj.get(a, []):
            if b in _offsets:
                continue
            # a 的出口全局坐标 = (ax+ex, ay+ey) = b 的入口全局坐标 = (ox+bx, oy+by)
            # => b 的偏移 = a偏移 + (ex-bx, ey-by)
            _offsets[b] = (ax + ex - bx, ay + ey - by)
            q.append(b)
    _ranges = []  # 尺寸由调用方补充


def offset_of(map_addr):
    return _offsets.get(map_addr)


def to_global(map_addr, x, y):
    """局部坐标 -> 全局坐标。未知地图返回 None。"""
    off = _offsets.get(map_addr)
    if off is None:
        return None
    return (off[0] + x, off[1] + y)


def to_local(map_addr, gx, gy):
    """全局坐标 -> 局部坐标。"""
    off = _offsets.get(map_addr)
    if off is None:
        return None
    return (gx - off[0], gy - off[1])


def register_size(map_addr, w, h):
    """登记地图尺寸（map_at 用）。"""
    off = _offsets.get(map_addr)
    if off is None:
        return
    _ranges.append((off[0], off[1], off[0] + w, off[1] + h, map_addr))


def map_at(gx, gy):
    """全局坐标落在哪张地图（需要先 register_size）。"""
    for x0, y0, x1, y1, addr in _ranges:
        if x0 <= gx < x1 and y0 <= gy < y1:
            return addr
    return None


def summary():
    """打印当前所有地图的偏移。"""
    for addr, off in sorted(_offsets.items()):
        print(f"{addr:08x}  offset=({off[0]},{off[1]})")


rebuild()
