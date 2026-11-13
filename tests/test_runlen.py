"""离线测试：无草长段、穿草短段。"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest.mock import patch
import pathfind

W = H = 40


def run(grass_cells, segs=3):
    lens = []
    vals = [0] * (W * H)
    for (x, y) in grass_cells:
        vals[y * W + x] = 13
    def snap():
        return {"battle": False, "dialog": False, "turn": 4,
                "x": 8, "y": 8, "mode": "map"}

    with patch.object(pathfind, "snapshot", snap), \
         patch.object(pathfind, "terrain") as terr, \
         patch.object(pathfind.nav, "bfs_turns", lambda *a, **k: ["right"] * 31), \
         patch.object(pathfind, "walk_segment", lambda d, n: (lens.append(n) or n)), \
         patch.object(pathfind, "press", lambda *a, **k: None):
        terr.load.return_value = (0, W, H, vals)
        terr.is_grass.side_effect = lambda v, w, x, y: v[y * w + x] == 13
        terr.npc_tiles.return_value = set()
        pathfind.goto(90, 8, max_segs=segs)
    return lens


lens = run([])                      # 全无草
assert lens and max(lens) > pathfind.MAX_RUN_GRASS, lens
print("A 无草走长段 ok", lens)

lens = run([(20, 1)])               # 起点 (1,1) 向右走，第 19 步才踩到 (20,1)
# 前 18 格无草 -> 一段走到草前；之后才进草（mock 坐标固定，每轮都算到这 18 格）
assert lens and lens[0] == 18, lens
print("B 走到草前才降频 ok", lens)
print("全部通过")
