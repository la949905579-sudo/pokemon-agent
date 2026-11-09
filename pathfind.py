"""快速寻路：BFS 出路径后按同方向段长按连续走。

带障碍学习 + 战斗检测：
  某段没走到应走的格数 -> 把挡路那格记进 _blocked，之后 BFS 绕开。
  每段最多 MAX_RUN 格；走完立刻查战斗，遇敌返回 "battle" 交上层处理。
"""
import sys, time
import log
sys.path.insert(0, "/root/workspace")
import terrain, nav, action, decision, info
from state import coords, player_facing, in_battle, snapshot, in_dialog
from ra import press

DELTA = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
MAX_RUN = 40              # 不穿草的路径可长段赶路
MAX_RUN_GRASS = 6         # 要穿草时必须短段
_blocked = {}          # (x,y) -> 过期时刻；带 TTL，NPC/临时障碍不会永久生效
BLOCK_TTL = 600        # 秒（NPC 挡路用更短的 60s）


def _grass_set(vals, w, h):
    return {(x, y) for y in range(h) for x in range(w)
            if terrain.is_grass(vals, w, x, y)}


def _blocked_set(now=None):
    """当前有效的障碍集合（过期自动忽略）。"""
    now = time.time() if now is None else now
    return {p for p, t in _blocked.items() if t > now}


def _note_blocked(p, ttl=BLOCK_TTL, force=False):
    """记障碍；NPC 默认不记，但连续撞上时 force=True 记短期（60s）。"""
    if not force:
        try:
            if p in terrain.npc_tiles():
                return
        except Exception:
            pass
    _blocked[p] = time.time() + ttl


def _plan(vals, w, h, cur, goal, avoid_grass=False):
    """BFS，先带回黑名单，失败再清空黑名单重试。返回 path 或 None。"""
    # NPC 会移动，不当作永久障碍（撞上会触发对话，由上层处理）
    blocked = _blocked_set()
    if avoid_grass:
        path = nav.bfs_turns(vals, w, h, cur, goal, blocked | _grass_set(vals, w, h))
        if path is not None:
            return path
    path = nav.bfs_turns(vals, w, h, cur, goal, blocked)
    if path is None and _blocked:
        _blocked.clear()
        path = nav.bfs_turns(vals, w, h, cur, goal, set())
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
    """走到 (gx,gy)（带计时日志）。"""
    t0 = time.time()
    r = _goto_impl(gx, gy, max_segs, stop_on_battle, avoid_grass)
    log.info("pathfind", "goto", goal=(gx, gy), result=str(r),
             ms=int((time.time() - t0) * 1000))
    return r


def travel(gx, gy, max_battles=30, verbose=True, avoid_grass=True):
    """同图 + 遇敌自动打（带计时日志）。"""
    t0 = time.time()
    r = _travel_impl(gx, gy, max_battles, verbose, avoid_grass)
    log.info("pathfind", "travel", goal=(gx, gy), result=str(r),
             ms=int((time.time() - t0) * 1000))
    return r


def _goto_impl(gx, gy, max_segs=60, stop_on_battle=True, avoid_grass=True):
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
            # 二次确认：防坐标抖动/换图瞬态误判“到达”
            time.sleep(0.06)
            s2 = snapshot()
            if s2.get("x") is not None and (s2["x"] - 7, s2["y"] - 7) == (gx, gy):
                _blocked.clear()
                return True
            continue
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
            # 连续撞同一格（多为 NPC 挡路）：临时记 60s，换路重试
            if path:
                dx, dy = DELTA[path[0]]
                _note_blocked((cur[0] + dx, cur[1] + dy), ttl=60, force=True)
                stuck = 0
                continue
            return False

        if moved < n:
            dx, dy = DELTA[d]
            bad = (cur[0] + dx * (moved + 1), cur[1] + dy * (moved + 1))
            if bad != cur and bad != (gx, gy):
                _note_blocked(bad)
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


def _travel_impl(gx, gy, max_battles=30, verbose=True, avoid_grass=True):
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


# ---------------- 固定跨图路线（实测验证过的） ----------------

def _route_step(name, gx, gy, d, expect_map, verbose=True):
    """固定路线单步：走到出口 -> 处理对话/战斗 -> 朝外走一格。"""
    if terrain.load()[0] != expect_map:
        if verbose:
            print(f"    跳过 {name}（当前 {hex(terrain.load()[0])}）", flush=True)
        return True
    for _ in range(4):
        r = goto(gx, gy, avoid_grass=False)
        if r == "battle":
            import auto_battle
            auto_battle.battle_loop()
            continue
        if r == "dialog":
            for _ in range(6):
                if not in_dialog():
                    break
                action.tap_b()
                time.sleep(0.6)
            continue
        if r is True:
            action.walk(d, 1)
            time.sleep(1.0)
            if verbose:
                print(f"    {name}: {hex(terrain.load()[0])}", flush=True)
            return True
        return False
    return False


def route_5_to_6(verbose=True):
    """5 号道路 -> 房间 -> 通道 -> 房间 -> 6 号道路（固定路线）。"""
    if verbose:
        print("  路线: 5号道路 -> 通道 -> 6号道路", flush=True)
    steps = [
        ("5号道路门", (31, 32), "up", 0x82e833c),
        ("房间进通道", (7, 4), "left", 0x83192f0),
        ("通道底部", (3, 60), "left", 0x831989c),
        ("房间出6号", (6, 8), "down", 0x83192f0),
    ]
    for name, (gx, gy), d, expect in steps:
        _route_step(name, gx, gy, d, expect, verbose)
    return terrain.load()[0] == 0x82e9260


def route_6_to_5(verbose=True):
    """6 号道路 -> 房间 -> 通道 -> 房间 -> 5 号道路（固定路线）。"""
    if verbose:
        print("  路线: 6号道路 -> 通道 -> 5号道路", flush=True)
    steps = [
        ("6号道路门", (19, 14), "up", 0x82e9260),
        ("房间进通道", (7, 4), "left", 0x83192f0),
        ("通道顶部", (4, 3), "right", 0x831989c),
        ("房间出5号", (6, 8), "down", 0x83192f0),
    ]
    for name, (gx, gy), d, expect in steps:
        _route_step(name, gx, gy, d, expect, verbose)
    return terrain.load()[0] == 0x82e833c
