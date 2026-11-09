"""画已知地图的连接关系图（节点 + 有向边），输出 PNG。"""
import sys
sys.path.insert(0, "/root/workspace")
from PIL import Image, ImageDraw, ImageFont

FONT = "/system/fonts/NotoSansCJK-Regular.ttc"
f_big = ImageFont.truetype(FONT, 15)
f_small = ImageFont.truetype(FONT, 11)
f_tiny = ImageFont.truetype(FONT, 10)

W, H = 900, 720
img = Image.new("RGB", (W, H), (250, 250, 252))
d = ImageDraw.Draw(img)

CITY = (205, 230, 250)      # 城市/道路
ROOM = (255, 228, 190)      # 小房间/通道
SUB = (225, 240, 225)       # 子地点（中心/道馆）
EDGE = (90, 90, 100)


def node(x, y, w, h, name, sub, color=CITY):
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=color,
                        outline=(70, 70, 80), width=2)
    tw = d.textlength(name, font=f_big)
    d.text((x + (w - tw) / 2, y + 8), name, font=f_big, fill=(20, 20, 30))
    if sub:
        tw2 = d.textlength(sub, font=f_small)
        d.text((x + (w - tw2) / 2, y + 28), sub, font=f_small, fill=(70, 70, 80))
    return (x, y, w, h)


def arrow(x1, y1, x2, y2, label=None, dx=6, dy=4):
    d.line([x1, y1, x2, y2], fill=EDGE, width=2)
    # 箭头
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 9
    for s in (0.45, -0.45):
        d.line([x2, y2, x2 - L * math.cos(ang - s), y2 - L * math.sin(ang - s)],
               fill=EDGE, width=2)
    if label:
        mx, my = (x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy
        d.text((mx, my), label, font=f_tiny, fill=(60, 60, 90))


# ---- 节点 ----
node(330, 30, 260, 52, "华蓝市", "0x82df30c  48×40")
node(70, 30, 200, 52, "精灵中心(华蓝)", "0x82d5844  15×10", SUB)
node(640, 30, 200, 52, "道馆(小霞)", "0x82d5cbc  17×20", SUB)

rB = node(330, 140, 260, 46, "被偷的房间", "0x831a3a0  10×9", ROOM)
d.text((rB[0] + 8, rB[1] + 48), "下方 (3,7) ↔ 华蓝市 (30,12)", font=f_tiny, fill=(60, 60, 90))
d.ellipse([rB[0] - 12, rB[1] + 14, rB[0] - 4, rB[1] + 22], fill=(220, 40, 40))
d.text((rB[0] - 80, rB[1] + 10), "你在这里", font=f_tiny, fill=(200, 30, 30))
node(330, 232, 260, 52, "5 号道路", "0x82e833c  48×40")
node(330, 340, 260, 52, "房间 A", "0x83192f0  13×10", ROOM)
node(650, 240, 200, 46, "地下通道", "0x831989c  8×63", ROOM)
node(330, 448, 260, 52, "6 号道路", "0x82e9260  24×40")
node(330, 556, 260, 52, "枯叶市", "0x82e0614  48×40")
node(70, 556, 200, 52, "精灵中心(枯叶)", "0x82d5844  15×10", SUB)

# ---- 边 ----
arrow(460, 82, 460, 140, "南边 (31,8) 往下")
arrow(460, 186, 460, 232, "北边出口")
arrow(460, 284, 460, 340, "北边出界 → 华蓝")
arrow(590, 366, 650, 286, "(7,4) 往左 / (4,3) 往右", dx=-40, dy=6)

arrow(460, 392, 460, 448, "(3,7) 往下")
arrow(460, 500, 460, 556, "北边 (24,0) 出界")

# 子地点连线
d.line([330, 56, 270, 56], fill=EDGE, width=2)
d.text((272, 40), "(22,20) 往上", font=f_tiny, fill=(60, 60, 90))
d.line([590, 56, 640, 56], fill=EDGE, width=2)
d.text((595, 40), "(31,22) 往上", font=f_tiny, fill=(60, 60, 90))
d.line([330, 582, 270, 582], fill=EDGE, width=2)
d.text((272, 566), "(15,5) 进门", font=f_tiny, fill=(60, 60, 90))

# ---- 图例 ----
d.text((640, 120), "图例", font=f_big, fill=(30, 30, 40))
d.rectangle([640, 148, 668, 168], fill=CITY, outline=(70, 70, 80))
d.text((676, 150), "城市 / 道路", font=f_small, fill=(40, 40, 50))
d.rectangle([640, 178, 668, 198], fill=ROOM, outline=(70, 70, 80))
d.text((676, 180), "室内 / 通道", font=f_small, fill=(40, 40, 50))
d.rectangle([640, 208, 668, 228], fill=SUB, outline=(70, 70, 80))
d.text((676, 210), "中心 / 道馆", font=f_small, fill=(40, 40, 50))

d.text((330, 20), "", font=f_tiny, fill=(0, 0, 0))
img.save("/root/workspace/map_graph.png")
print("saved /root/workspace/map_graph.png", img.size)
