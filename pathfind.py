"""快速寻路：BFS 出路径后按同方向段长按连续走。

带障碍学习 + 战斗检测：
  某段没走到应走的格数 -> 把挡路那格记进 _blocked，之后 BFS 绕开。
  每段最多 MAX_RUN 格；走完立刻查战斗，遇敌返回 "battle" 交上层处理。
"""
import sys, time
import log
sys.path.insert(0, "/root/workspace")
import terrain, nav, action, decision, info
from state import coords, player_facing, in_battle, snapshot
from ra import press

DELTA = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
MAX_RUN = 40              # 不穿草的路径可长段赶路
MAX_RUN_GRASS = 6         # 要穿草时必须短段
_blocked = set()


def _grass_set(vals, w, h):
    return {(x, y) for y in range(h) for x in range(w)
            if terrain.is_grass(vals, w, x, y)}


def _plan(vals, w, h, cur, goal, avoid_grass=False):
    """BFS，先带回黑名单，失败再清空黑名单重试。返回 path 或 None。"""
    blocked = _blocked | terrain.npc_tiles()
    if avoid_grass:
        path = nav.bfs_turns(vals, w, h, cur, goal, blocked | _grass_set(vals, w, h))
        if path is not None:
            return path
    path = nav.bfs_turns(vals, w, h, cur, goal, blocked)
    if path is None and _blocked:
        _blocked.clear()
        path = nav.bfs_turns(vals, w, h, cur, goal, terrain.npc_tiles())
    return path


def compress(path):
    """方向列表 -> [(方向, 段长), ...]"""
    segs = []
    for d in path:
        if segs and segs[-1][0] == d:
            segs[-1][1] += 1
        else:
            segs.append([d, 1])
    return [(d, n) for d, n in segs]


def _clear_run(vals, w, h, cur, path):
    """到第一格草之前的步数。"""
    x, y = cur
    n = 0
    for d in path:
        dx, dy = DELTA.get(d, (0, 0))
        x += dx
        y += dy
        if terrain.is_grass(vals, w, x, y):
            break
        n += 1
    return n


def walk_segment(d, n):
    """决策层拉朝向 -> 需要转身就先转 -> 执行层走。"""
    if decision.need_turn(d, info.facing()):
        action.press(d, 0.06)
        time.sleep(0.05)
    return action.walk(d, n)


def goto(gx, gy, max_segs=60, stop_on_battle=True, avoid_grass=True):
    """走到 (gx,gy)。返回 True=到达 / "battle"=中途遇敌 / "dialog"=对话 / False=失败。"""
    last_pos = None
    stuck = 0
    for _ in range(max_segs):
        s = snapshot()
        if stop_on_battle and (s["battle"] or s["dialog"]):
            return "battle" if s["battle"] else "dialog"
        if s["x"] is None:
            return False
        cur = (s["x"] - 7, s["y"] - 7)
        if cur == (gx, gy):
            _blocked.clear()
            return True
        addr, w, h, vals = terrain.load()
        if not vals:
            return False
        path = _plan(vals, w, h, cur, (gx, gy), avoid_grass=avoid_grass)
        if not path:
            return False
        d, n = compress(path)[0]
        clear = _clear_run(vals, w, h, cur, path)
        limit = MAX_RUN_GRASS if clear == 0 else (clear if clear < MAX_RUN else MAX_RUN)
        n = min(n, limit)
        moved = walk_segment(d, n)

        if stop_on_battle:
            s2 = snapshot()
            if s2["battle"] or s2["dialog"]:
                return "battle" if s2["battle"] else "dialog"

        # 连续位置不变 -> 卡死，放弃
        s3 = snapshot()
        now = (s3["x"] - 7, s3["y"] - 7) if s3["x"] is not None else None
        stuck = stuck + 1 if now == last_pos else 0
        last_pos = now
        if stuck >= 3:
            return False

        if moved < n:
            dx, dy = DELTA[d]
            bad = (cur[0] + dx * (moved + 1), cur[1] + dy * (moved + 1))
            if bad != cur and bad != (gx, gy):
                _blocked.add(bad)
    return False


def _leave_grass():
    """站在草地上时走到最近的非草格（避免原地连续遇敌）。"""
    p = coords()
    if not p:
        return False
    x, y = p[0] - 7, p[1] - 7
    addr, w, h, vals = terrain.load()
    if not vals or not terrain.is_grass(vals, w, x, y):
        return False
    for d, (dx, dy) in DELTA.items():
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and terrain.walkable(vals, w, nx, ny) \
                and not terrain.is_grass(vals, w, nx, ny):
            action.walk(d, 1)
            return True
    return False


def _record_link(base_map, exit_xy, verbose=True):
    """换图后记录地图连接。"""
    try:
        import map_links
        new_map = terrain.load()[0]
        p = coords()
        if base_map and new_map and p:
            map_links.add_link(base_map, exit_xy, new_map, (p[0] - 7, p[1] - 7))
            log.info("pathfind", "map_link", from_map=hex(base_map),
                     exit=exit_xy, to_map=hex(new_map),
                     enter=(p[0] - 7, p[1] - 7))
    except Exception as e:
        log.error("pathfind", "map_link_fail", err=str(e))


def travel(gx, gy, max_battles=30, verbose=True, avoid_grass=True):
    """寻路 + 遇敌自动打 + 打完继续。返回 ok / warped / fail / battle_stuck / too_many_battles。"""
    base_hdr = terrain._map_hdr()
    base_map = terrain.load()[0]
    for _ in range(max_battles + 1):
        if in_battle() is not False:
            import auto_battle
            if verbose:
                print("  遇敌 -> 自动战斗", flush=True)
            auto_battle.battle_loop()
            if in_battle() is not False:
                return "battle_stuck"
            _leave_grass()
            continue
        r = goto(gx, gy, avoid_grass=avoid_grass)
        if r is True:
            # 目标在边界 -> 继续朝外走一步触发换图
            a2, w2, h2, _ = terrain.load()
            if a2 and (gx in (0, w2 - 1) or gy in (0, h2 - 1)):
                for d, chk in (("left", gx == 0), ("right", gx == w2 - 1),
                               ("up", gy == 0), ("down", gy == h2 - 1)):
                    if chk:
                        action.walk(d, 1)
                        time.sleep(0.8)
                        break
            if terrain._map_hdr() != base_hdr:
                _record_link(base_map, (gx, gy), verbose)
                return "warped"
            return "ok"
        if r == "battle":
            continue
        if r == "dialog":
            for _ in range(6):
                s = snapshot()
                if s["battle"] or not s["dialog"]:
                    break
                press("b", 0.15)
                time.sleep(0.6)
            continue
        if terrain._map_hdr() != base_hdr:
            return "warped"
        return "fail"
    return "too_many_battles"


def travel_map(dst_map, dst_x, dst_y, max_steps=12, verbose=True):
    """跨地图寻路：每步重新规划（处理复用房间）。返回 ok / no_route / fail。"""
    import map_links
    for step in range(max_steps):
        cur_map = terrain.load()[0]
        if not cur_map:
            return "fail"
        if cur_map == dst_map:
            return "ok" if goto(dst_x, dst_y) is True else "fail"

        route = map_links.route_maps(cur_map, dst_map)
        if not route or len(route) < 2:
            return "no_route"
        nxt = route[1]

        ln = None
        for l in map_links.links_from(cur_map):
            targets = l.get("targets")
            if targets:
                if any(t["to_map"] == nxt for t in targets):
                    ln = l
                    break
            elif l.get("to_map") == nxt:
                ln = l
                break
        if not ln:
            return "no_route"

        ex, ey = ln["exit"]
        if verbose:
            print(f"  跨图{step}: {hex(cur_map)} 出口({ex},{ey}) -> {hex(nxt)}", flush=True)
        r = goto(ex, ey, avoid_grass=False)
        if r == "battle":
            import auto_battle
            auto_battle.battle_loop()
        elif r is not True and r != "dialog":
            return "fail"

        # 门需要「踩入」触发：先走开一格，再走回出口格
        moved = False
        s = snapshot()
        start = (s["x"] - 7, s["y"] - 7) if s["x"] is not None else (ex, ey)
        for d in ("down", "up", "left", "right"):
            action.walk(d, 1)
            time.sleep(0.5)
            s2 = snapshot()
            now = (s2["x"] - 7, s2["y"] - 7) if s2["x"] is not None else start
            if now == start:
                continue          # 没走开（被挡），换方向
            if terrain.load()[0] != cur_map:
                moved = True
                break
            # 走回出口格（踩入）
            opp = {"up": "down", "down": "up", "left": "right", "right": "left"}[d]
            action.walk(opp, 2)
            time.sleep(0.9)
            if terrain.load()[0] != cur_map:
                moved = True
                break
        if not moved:
            return "fail"
    return "fail"
