"""跨图寻路：在连接表上做 A*，输出逐段路线并执行。

- 图：map_links.json 的地图连接（实测出口/入口）
- 启发：map_coords 全局坐标曼哈顿距离（未知地图退化为 BFS）
- 执行：同图走 pathfind.travel 到出口 -> 朝外走一步 -> 校验换图 -> 下一段

用法：
    import map_route
    map_route.plan(map_a, map_b)             # 只规划
    map_route.travel_map(map_b, x, y)        # 规划 + 执行
"""
import heapq
import time

import action
import map_coords
import map_links
import pathfind
import terrain

DIRS = ("up", "down", "left", "right")

# 复用房间（车站/通道）用实测固定路线，图搜索不可靠
FIXED = {
    (0x82e9260, 0x82e833c): "route_6_to_5",
    (0x82e833c, 0x82e9260): "route_5_to_6",
}

R6, R5 = 0x82e9260, 0x82e833c
# 通道北侧：5号道路、华蓝市、华蓝道馆
NORTH = {R5, 0x82df30c, 0x82d5cbc}


def _edges(map_addr):
    out = []
    for ln in map_links.links_from(map_addr):
        ts = ln.get("targets")
        if ts is None:
            ts = ([{"to_map": ln["to_map"], "to_pos": ln.get("to_pos")}]
                  if ln.get("to_map") else [])
        for t in ts:
            if not t.get("to_map"):
                continue
            out.append({
                "from": map_addr, "exit": tuple(ln["exit"]),
                "to": t["to_map"], "enter": tuple(t["to_pos"]),
                "side": ln.get("side"),
                "reused": len(ts) > 1,     # 复用房间：同一出口可能通向不同地图
            })
    return out


def _heuristic(m, dst):
    try:
        g = map_coords.to_global(m, 0, 0)
        t = map_coords.to_global(dst, 0, 0)
        if g and t:
            return abs(g[0] - t[0]) + abs(g[1] - t[1])
    except Exception:
        pass
    return 0


def plan(src_map, dst_map, max_depth=12):
    """A*：返回 [{from, exit, to, enter, side}, ...]；同图返回 []；无路返回 None。"""
    if src_map == dst_map:
        return []
    pq = [(_heuristic(src_map, dst_map), 0, src_map, [])]
    best = {src_map: 0}
    while pq:
        _, cost, cur, path = heapq.heappop(pq)
        if cur == dst_map:
            return path
        if cost > best.get(cur, 1e9) or len(path) >= max_depth:
            continue
        for e in _edges(cur):
            # 复用房间的边不可靠：加惩罚，优先普通边
            nc = cost + (3 if e.get("reused") else 1)
            if nc < best.get(e["to"], 1e9):
                best[e["to"]] = nc
                heapq.heappush(pq, (nc + _heuristic(e["to"], dst_map),
                                    nc, e["to"], path + [e]))
    return None


def _exit_dir(exit_xy):
    """边界出口 -> 朝外方向；内部门返回 None（需要试）。"""
    a, w, h, _ = terrain.load()
    x, y = exit_xy
    if x == 0:
        return "left"
    if x == w - 1:
        return "right"
    if y == 0:
        return "up"
    if y == h - 1:
        return "down"
    return None


def _cross(exit_xy, to_map):
    """站在出口上朝外走一格，直到换到目标地图。"""
    d = _exit_dir(exit_xy)
    for direction in ([d] if d else list(DIRS)):
        action.walk(direction, 1)
        time.sleep(0.9)
        if terrain.load()[0] == to_map:
            return True
    return False


def travel_map(dst_map, dst_x, dst_y, verbose=True):
    """跨图走到目标地图的地块 (dst_x, dst_y)。

    返回 ok / warped / fail / battle / no_route / too_many_battles。
    遇到战斗立即返回 battle（由上层决定是否打完继续）。
    """
    cur = terrain.load()[0]
    if not cur:
        return "fail"
    if cur == dst_map:
        return pathfind.travel(dst_x, dst_y)
    # 跨通道：先跑到 6号/5号，再用实测固定路线
    if dst_map != cur:
        if cur == R6 and dst_map in NORTH:
            if not pathfind.route_6_to_5():
                return "fail"
            return travel_map(dst_map, dst_x, dst_y, verbose)
        if cur in NORTH and dst_map == R6:
            if not pathfind.route_5_to_6():
                return "fail"
            return travel_map(dst_map, dst_x, dst_y, verbose)
        if cur == 0x82e0614 and dst_map in (R5,) | (NORTH - {R5}):
            r = travel_map(R6, 19, 37, verbose)
            if r != "ok":
                return r
            if not pathfind.route_6_to_5():
                return "fail"
            return travel_map(dst_map, dst_x, dst_y, verbose)

    # 直达的复用房间段：优先用实测固定路线
    fixed = FIXED.get((cur, dst_map))
    if fixed:
        if verbose:
            print(f"  使用固定路线 {fixed}", flush=True)
        ok = getattr(pathfind, fixed)()
        if not ok:
            return "fail"
        if terrain.load()[0] != dst_map:
            return "warped"
        return pathfind.travel(dst_x, dst_y)

    route = plan(cur, dst_map)
    if route is None:
        return "no_route"
    for e in route:
        if (e["from"], e["to"]) in FIXED:
            if verbose:
                print(f"  段内固定路线 {FIXED[(e['from'], e['to'])]}", flush=True)
            if not getattr(pathfind, FIXED[(e["from"], e["to"])])():
                return "fail"
            continue
        r = pathfind.travel(e["exit"][0], e["exit"][1])
        if r == "battle":
            return "battle"
        if r not in ("ok", "warped"):
            return "fail"
        if terrain.load()[0] == e["from"]:
            if not _cross(e["exit"], e["to"]):
                return "warped"
        if terrain.load()[0] != e["to"]:
            return "warped"
    if terrain.load()[0] != dst_map:
        return "warped"
    return pathfind.travel(dst_x, dst_y)


if __name__ == "__main__":
    import sys
    src = int(sys.argv[1], 16) if len(sys.argv) > 1 else terrain.load()[0]
    dst = int(sys.argv[2], 16)
    if len(sys.argv) > 4:
        print(travel_map(dst, int(sys.argv[3]), int(sys.argv[4])))
    else:
        for e in plan(src, dst) or []:
            print(hex(e["from"]), e["exit"], "->", hex(e["to"]), e["enter"])
