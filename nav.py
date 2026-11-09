"""自适应导航：BFS + 卡住就把那一格当障碍，重新规划。
用法: python3 nav.py <tile_x> <tile_y>
"""
import sys, time
sys.path.insert(0, "/root/workspace")
import terrain
from ra import press
from state import coords, in_battle
from collections import deque

DIRS = [(0, -1, "up"), (0, 1, "down"), (-1, 0, "left"), (1, 0, "right")]
DELTA = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def step(d):
    """走一格；第一次可能只是转身，所以最多按两次。"""
    for _ in range(2):
        b = coords()
        if b is None:
            return False
        press(d, 0.06)
        time.sleep(0.45)
        a = coords()
        if a and a != b:
            return True
    return False


def bfs(vals, w, h, start, goal, blocked):
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for dx, dy, d in DIRS:
            nx, ny = cur[0] + dx, cur[1] + dy
            if (nx, ny) in prev:
                continue
            if not terrain.walkable(vals, w, nx, ny):
                continue
            # 只在同一高度层移动：水边/悬崖的碰撞位也是 0，但跨层走不过去
            if ((vals[ny * w + nx] >> 12) & 0xF) != ((vals[cur[1] * w + cur[0]] >> 12) & 0xF):
                continue
            if (nx, ny) in blocked:
                continue
            prev[(nx, ny)] = (cur, d)
            q.append((nx, ny))
    if goal not in prev:
        return None
    path = []
    cur = goal
    while prev[cur] is not None:
        p, d = prev[cur]
        path.append(d)
        cur = p
    return list(reversed(path))


def bfs_turns(vals, w, h, start, goal, blocked, turn_penalty=1.6):
    """带转弯惩罚的寻路：同样步数下优先少转弯。

    状态 = (x, y, 上一步方向)，转弯额外增加 turn_penalty 成本。
    返回方向列表（和 bfs 一致），无路返回 None。
    """
    import heapq

    def walkable(x, y):
        if not (0 <= x < w and 0 <= y < h):
            return False
        if not terrain.walkable(vals, w, x, y):
            return False
        return True

    start_state = (start[0], start[1], None)
    dist = {start_state: 0.0}
    prev = {start_state: None}
    pq = [(0.0, start_state)]
    goal_state = None

    while pq:
        cost, (x, y, d) = heapq.heappop(pq)
        if cost > dist.get((x, y, d), 1e18):
            continue
        if (x, y) == goal:
            goal_state = (x, y, d)
            break
        for dx, dy, nd in DIRS:
            nx, ny = x + dx, y + dy
            if not walkable(nx, ny) or (nx, ny) in blocked:
                continue
            # 同高度层才能走
            if ((vals[ny * w + nx] >> 12) & 0xF) != ((vals[y * w + x] >> 12) & 0xF):
                continue
            turn = turn_penalty if (d is not None and d != nd) else 0.0
            nc = cost + 1.0 + turn
            st = (nx, ny, nd)
            if nc < dist.get(st, 1e18):
                dist[st] = nc
                prev[st] = ((x, y, d), nd)
                heapq.heappush(pq, (nc, st))

    if goal_state is None:
        return None
    path = []
    cur = goal_state
    while prev[cur] is not None:
        p, d = prev[cur]
        path.append(d)
        cur = p
    return list(reversed(path))


def goto(gx, gy, max_steps=200):
    blocked = set()
    for i in range(max_steps):
        if in_battle():
            return "battle"
        p = coords()
        if p is None:
            print("读不到坐标")
            return False
        cur = (p[0] - 7, p[1] - 7)
        if cur == (gx, gy):
            print(f"到达地块 ({gx},{gy})")
            return True
        addr, w, h, vals = terrain.load()
        if not vals:
            print("读不到地图")
            return False
        path = bfs(vals, w, h, cur, (gx, gy), blocked | terrain.npc_tiles())
        if not path:
            print(f"从 {cur} 到 ({gx},{gy}) 无路可走，已绕开 {len(blocked)} 格")
            return False
        d = path[0]
        if step(d):
            continue
        dx, dy = DELTA[d]
        blocked.add((cur[0] + dx, cur[1] + dy))
        print(f"在 {cur} 想往 {d} 走但没走动，标记 {cur[0]+dx},{cur[1]+dy}")
    print("步数用尽")
    return False


if __name__ == "__main__":
    goto(int(sys.argv[1]), int(sys.argv[2]))
