"""地图决策模块（纯逻辑）。

由中间层在「地图场景」下激活：转身 / 走路 / 草里降频。
"""
import sys
sys.path.insert(0, "/root/workspace")

def need_turn(direction, facing):
    """朝向与行进方向不一致时需要先转身。"""
    return bool(facing and facing != direction)


def walk_plan(direction, facing):
    """走一步的计划：方向 + 是否先转身。"""
    return {"direction": direction, "turn": need_turn(direction, facing)}


def choose_next_step(path):
    """寻路：取路径的第一步方向。"""
    return path[0] if path else None


# ---------------- 寻路决策（纯计算，输入地图数据） ----------------
GRASS_ID = 13
MAX_RUN = 40
MAX_RUN_GRASS = 6


def grass_tiles(vals, w, h):
    """所有草地格子集合。"""
    return {(x, y) for y in range(h) for x in range(w)
            if (vals[y * w + x] & 0x3FF) == GRASS_ID}


def clear_run(vals, w, h, start, path, delta):
    """沿路径往前，到第一格草之前有多少格。"""
    x, y = start
    k = 0
    for d in path:
        dx, dy = delta[d]
        x += dx
        y += dy
        if (vals[y * w + x] & 0x3FF) == GRASS_ID:
            break
        k += 1
    return k


def run_limit(clear, max_run=MAX_RUN, max_grass=MAX_RUN_GRASS):
    """这一段的长度上限：草前长段，进草降频。"""
    if clear <= 0:
        return max_grass
    if clear < max_run:
        return clear
    return max_run
