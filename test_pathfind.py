"""离线逻辑测试：pathfind 的障碍学习（mock snapshot，不碰游戏）。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import time
import pathfind
import action


def snap(x, y, battle=False, dialog=False):
    return {"battle": battle, "dialog": dialog, "turn": 4, "x": x, "y": y,
            "mode": "battle" if battle else "map"}


def run_scenario(coord_seq, facing, battle, bfs_paths, max_segs=1):
    it = iter(coord_seq)

    def fake_snapshot():
        x, y = next(it, coord_seq[-1])
        return snap(x, y, battle=battle)

    calls = {"n": 0}

    def fake_bfs(vals, w, h, cur, goal, blocked):
        i = min(calls["n"], len(bfs_paths) - 1)
        calls["n"] += 1
        return bfs_paths[i]

    pathfind._blocked.clear()
    with patch.object(pathfind, "snapshot", fake_snapshot), \
         patch.object(action, "snapshot", fake_snapshot), \
         patch.object(action, "press", lambda *a, **k: None), \
         patch.object(pathfind.terrain, "load", lambda: (0, 20, 20, [0] * 400)), \
         patch.object(pathfind.terrain, "npc_tiles", lambda: set()), \
         patch.object(pathfind.terrain, "is_grass", lambda *a: False), \
         patch.object(pathfind.nav, "bfs_turns", fake_bfs):
        ok = pathfind.goto(14, 10, max_segs=max_segs)
    return ok


# A: 应走 4 格只走 2 格 -> 学 (13,10)
ok = run_scenario([(17, 17), (17, 17), (19, 17)], "right", False, [["right"] * 4])
assert ok is False, ok
assert set(pathfind._blocked) == {(13, 10)}, pathfind._blocked
print("A 撞墙学习 ok:", pathfind._blocked)

# B: 开局就在战斗 -> 直接返回 battle，不学
pathfind._blocked.clear()
r = run_scenario([(17, 17)], "right", True, [["right"] * 4])
assert r == "battle", r
assert not pathfind._blocked
print("B 战斗中不学 ok")

# C: 黑名单把路堵死 -> 清空重试
pathfind._blocked.clear()
pathfind._blocked[(11, 10)] = time.time()
got = {"first_blocked": None}


def bfs_check(vals, w, h, cur, goal, blocked):
    if got["first_blocked"] is None:
        got["first_blocked"] = set(blocked)
        return None
    return ["right"]


with patch.object(pathfind.terrain, "npc_tiles", lambda: set()), \
     patch.object(pathfind.nav, "bfs_turns", bfs_check):
    path = pathfind._plan([0] * 400, 20, 20, (10, 10), (14, 10))
assert path == ["right"] and not pathfind._blocked
assert (11, 10) in got["first_blocked"]
print("C 堵死清空重试 ok")

# D: 到达即清空
pathfind._blocked[(99, 99)] = time.time()
with patch.object(pathfind, "snapshot", lambda: snap(21, 17)):
    assert pathfind.goto(14, 10, max_segs=1) is True
assert not pathfind._blocked
print("D 到达清空 ok")

# E: 障碍过期后不再生效
pathfind._blocked[(1, 1)] = time.time() - pathfind.BLOCK_TTL - 1
assert (1, 1) not in pathfind._blocked_set()
print("E 障碍 TTL 过期 ok")

# F: NPC 不记为障碍
with patch.object(pathfind.terrain, "npc_tiles", lambda: {(5, 5)}):
    pathfind._note_blocked((5, 5))
assert (5, 5) not in pathfind._blocked
print("F NPC 不记墙 ok")

print("全部通过")
