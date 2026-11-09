"""把当前地图画成 PNG：碰撞/草/NPC/玩家/规划路径，带中文图例和网格线。只读。

用法：
    python3 mapdraw.py                # 只画当前地图
    python3 mapdraw.py 12,39          # 画当前地图 + 到 (12,39) 的规划路径
    python3 mapdraw.py 12,39 out.png  # 指定输出文件
"""
import sys
sys.path.insert(0, "/root/workspace")
import terrain
from state import coords
from PIL import Image, ImageDraw, ImageFont

CELL, PAD = 22, 60
FONT_PATH = "/system/fonts/NotoSansCJK-Regular.ttc"

# 颜色
C_WALL = (40, 44, 52)
C_WALK = (248, 248, 250)
C_GRASS = (120, 200, 120)
C_HEDGE = (90, 160, 90)     # 绿化带（灌木丛）
C_STUMP = (210, 170, 60)    # 小树苗（需居合斩）
C_NPC = (240, 150, 60)
C_PLAYER = (230, 60, 60)
C_PATH = (80, 140, 240)
C_GOAL = (240, 60, 200)
C_GRID = (215, 215, 220)
C_FENCE = (150, 150, 155)   # 栅栏
C_TREE = (70, 120, 70)      # 树
C_BUILD = (180, 150, 120)   # 建筑物
C_DOOR = (250, 220, 120)    # 门（踩上去换图，但 collide=1）
FENCE_IDS = {231, 244, 245, 246, 247}
TREE_IDS = {20, 21, 22, 28, 29, 30, 31, 32}
DOOR_IDS = {61, 710, 717, 718, 719}
HEDGE_IDS = {318}
STUMP_IDS = {317}
BUILD_IDS = {68, 69, 70, 76, 77, 78, 84, 85, 86, 103,
             400, 401, 402, 408, 409, 410, 219, 220, 221, 227, 228, 229}


def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default(size=size)


def draw(goal=None, out="map_now.png", show_grid=True):
    a, w, h, vals = terrain.load()
    p = coords()
    if not vals or not p:
        print("读不到地图数据")
        return None
    tx, ty = p[0] - 7, p[1] - 7
    npcs = terrain.npc_tiles()

    # 规划路径（可选）
    path = None
    if goal is not None:
        try:
            import pathfind
            path = pathfind._plan(vals, w, h, (tx, ty), tuple(goal), avoid_grass=True)
        except Exception as e:
            print("路径规划失败:", e)

    W = w * CELL + PAD * 2
    H = h * CELL + PAD * 2
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f_title = load_font(16)
    f_leg = load_font(11)
    f_tile = load_font(9)

    # 标题
    d.text((PAD, 10), f"地图 {hex(a) if a else '?'}  {w}x{h}  玩家({tx},{ty})", fill=(30, 30, 30), font=f_title)

    # 网格
    ox, oy = PAD, PAD
    for y in range(h):
        for x in range(w):
            px, py = ox + x * CELL, oy + y * CELL
            metatile = vals[y * w + x] & 0x3FF
            if metatile in DOOR_IDS:
                color = C_DOOR
            elif not terrain.walkable(vals, w, x, y):
                if metatile in FENCE_IDS:
                    color = C_FENCE
                elif metatile in TREE_IDS:
                    color = C_TREE
                elif metatile in HEDGE_IDS:
                    color = C_HEDGE
                elif metatile in STUMP_IDS:
                    color = C_STUMP
                elif metatile in BUILD_IDS:
                    color = C_BUILD
                else:
                    color = C_WALL
            elif terrain.is_grass(vals, w, x, y):
                color = C_GRASS
            else:
                color = C_WALK
            d.rectangle([px, py, px + CELL - 1, py + CELL - 1], fill=color)
            if show_grid and color != C_WALL:
                d.rectangle([px, py, px + CELL - 1, py + CELL - 1], outline=C_GRID)

    # 路径（方向列表 -> 坐标点）
    if path:
        DELTA = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
        pts = []
        cx, cy = tx, ty
        pts.append(((cx + 0.5) * CELL + ox, (cy + 0.5) * CELL + oy))
        for step_dir in path:
            dx, dy = DELTA.get(step_dir, (0, 0))
            cx += dx
            cy += dy
            pts.append(((cx + 0.5) * CELL + ox, (cy + 0.5) * CELL + oy))
        if len(pts) >= 2:
            d.line(pts, fill=C_PATH, width=3)

    # NPC
    for (nx, ny) in npcs:
        if 0 <= nx < w and 0 <= ny < h:
            px, py = ox + nx * CELL, oy + ny * CELL
            d.rectangle([px + 5, py + 5, px + CELL - 6, py + CELL - 6], fill=C_NPC)

    # 目标
    if goal is not None:
        gx, gy = goal
        if 0 <= gx < w and 0 <= gy < h:
            px, py = ox + gx * CELL, oy + gy * CELL
            d.rectangle([px + 4, py + 4, px + CELL - 5, py + CELL - 5], outline=C_GOAL, width=2)

    # 玩家
    px, py = ox + tx * CELL, oy + ty * CELL
    d.ellipse([px + 4, py + 4, px + CELL - 5, py + CELL - 5], fill=C_PLAYER)

    # 图例
    lx, ly = PAD, H - 42
    items = [("可走", C_WALK), ("墙", C_WALL), ("栅栏", C_FENCE), ("树", C_TREE), ("绿化带", C_HEDGE), ("小树苗", C_STUMP), ("建筑", C_BUILD), ("门", C_DOOR), ("草", C_GRASS), ("NPC", C_NPC),
             ("玩家", C_PLAYER), ("路径", C_PATH), ("目标", C_GOAL)]
    for i, (name, col) in enumerate(items):
        bx = lx + i * 80
        d.rectangle([bx, ly, bx + 12, ly + 12], fill=col, outline=(150, 150, 150))
        d.text((bx + 16, ly - 1), name, fill=(40, 40, 40), font=f_leg)

    img.save(out)
    print(f"saved {out} ({W}, {H})")
    if path:
        print(f"路径长度 {len(path)} 格")
    return out


if __name__ == "__main__":
    goal = None
    out = "map_now.png"
    if len(sys.argv) > 1 and sys.argv[1] != "none":
        goal = tuple(int(v) for v in sys.argv[1].split(","))
    if len(sys.argv) > 2:
        out = sys.argv[2]
    draw(goal=goal, out=out)
