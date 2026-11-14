"""离线测试：寻路避开草地。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
from unittest.mock import patch
import pathfind

W = H = 10
D = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def make(grass_cells):
    vals = [0] * (W * H)
    for (x, y) in grass_cells:
        vals[y * W + x] = 13          # metatile 13 = 高草
    return vals


def cells_of(start, path):
    x, y = start
    out = [(x, y)]
    for d in path:
        dx, dy = D[d]
        x += dx
        y += dy
        out.append((x, y))
    return out


def plan(vals, start, goal, avoid=True):
    with patch.object(pathfind.terrain, "npc_tiles", lambda: set()):
        return pathfind._plan(vals, W, H, start, goal, avoid_grass=avoid)


# A：竖排草只到 y=8，下方留一条路 -> 应绕开
vals = make([(5, y) for y in range(9)])
p = plan(vals, (1, 5), (8, 5))
assert p, "应该有路"
cells = cells_of((1, 5), p)
grass_hit = [c for c in cells if vals[c[1] * W + c[0]] == 13]
assert not grass_hit, f"路径踩到草: {grass_hit}"
print("A 能绕开草地 ok，路径", len(p), "格")

# B：竖排草堵满 -> 绕不开，必须允许穿草
vals = make([(5, y) for y in range(10)])
p = plan(vals, (1, 5), (8, 5))
assert p, "绕不开时也应回退给路"
cells = cells_of((1, 5), p)
assert any(vals[c[1] * W + c[0]] == 13 for c in cells), "回退路径本应穿草"
print("B 绕不开时回退穿草 ok")

# C：目标本身在草里 -> 仍能到达
vals = make([(5, 5)])
p = plan(vals, (1, 5), (5, 5))
assert p, "目标是草地也必须能到达"
print("C 目标在草里仍可达 ok")

# D：avoid_grass=False 时允许穿草
vals = make([(5, y) for y in range(9)])
p = plan(vals, (1, 5), (8, 5), avoid=False)
cells = cells_of((1, 5), p)
assert len(p) <= 9, f"不避草应走直线，实际 {len(p)}"
print("D 关闭避草时走直 ok", len(p))
print("全部通过")
