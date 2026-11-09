"""遇敌：判断在草地、走回最近草地、九宫格朝草移动。"""
import sys, time, random
sys.path.insert(0, "/root/workspace")
import terrain
from state import coords, in_battle
from ra import press
from collections import deque

DIRS = [(0, -1, "up"), (0, 1, "down"), (-1, 0, "left"), (1, 0, "right")]


def tile_pos():
    p = coords()
    return (p[0] - 7, p[1] - 7) if p else None


def load_map():
    return terrain.load()


def is_grass_here(vals, w, tx, ty):
    return terrain.is_grass(vals, w, tx, ty)


def nearest_grass(vals, w, h, start, blocked=None):
    blocked = blocked or set()
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        if terrain.is_grass(vals, w, cur[0], cur[1]):
            return cur
        for dx, dy, _ in DIRS:
            nx, ny = cur[0] + dx, cur[1] + dy
            if (nx, ny) in prev:
                continue
            if not terrain.walkable(vals, w, nx, ny):
                continue
            if (nx, ny) in blocked:
                continue
            if ((vals[ny * w + nx] >> 12) & 0xF) != ((vals[cur[1] * w + cur[0]] >> 12) & 0xF):
                continue
            prev[(nx, ny)] = cur
            q.append((nx, ny))
    return None


def ensure_grass(max_tries=60):
    """确保站在草地上；不在就用 BFS 走到最近的草格。"""
    for _ in range(max_tries):
        p = tile_pos()
        addr, w, h, vals = load_map()
        if not p or not vals:
            return False
        if is_grass_here(vals, w, p[0], p[1]):
            return True
        npcs = terrain.npc_tiles()
        g = nearest_grass(vals, w, h, p, npcs)
        if not g:
            return False
        # 九宫格已有草 -> 直接朝那个方向走
        moved = False
        for dx, dy, d in DIRS:
            nx, ny = p[0] + dx, p[1] + dy
            if terrain.is_grass(vals, w, nx, ny) and terrain.walkable(vals, w, nx, ny) and (nx, ny) not in npcs:
                press(d, 0.1); time.sleep(0.4); moved = True; break
        if moved:
            continue
        # 否则用 nav 走过去
        import pathfind
        pathfind.goto(g[0], g[1])
        time.sleep(0.3)
    return False


_last_dir = {"d": None}


def step_in_grass():
    """优先选与上一步不同的方向；没有别的草方向时才允许同方向。"""
    p = tile_pos()
    addr, w, h, vals = load_map()
    if not p or not vals:
        return False
    dirs = DIRS[:]
    random.shuffle(dirs)
    preferred = [x for x in dirs if x[2] != _last_dir["d"]]
    fallback = [x for x in dirs if x[2] == _last_dir["d"]]
    for dx, dy, d in preferred + fallback:
        nx, ny = p[0] + dx, p[1] + dy
        if terrain.is_grass(vals, w, nx, ny) and terrain.walkable(vals, w, nx, ny):
            press(d, 0.06); time.sleep(0.42)
            _last_dir["d"] = d
            return True
    return False


def find_encounter(max_steps=40):
    """在草地内走动找野生宝可梦；不在草地会先走回去。"""
    if not ensure_grass():
        return False
    for i in range(max_steps):
        if in_battle() is not False:
            return True
        if i % 5 == 0 and not ensure_grass():
            return False
        if not step_in_grass():
            if not ensure_grass():
                return False
            continue
        time.sleep(0.05)
    return in_battle() is not False


if __name__ == "__main__":
    p = tile_pos()
    addr, w, h, vals = load_map()
    print("pos", p, "grass?", is_grass_here(vals, w, p[0], p[1]) if p and vals else None)
