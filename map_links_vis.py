"""把 map_links.json 画成地图连接图（节点 + 箭头）。"""
import sys, math
sys.path.insert(0, "/root/workspace")
import map_links
from PIL import Image, ImageDraw, ImageFont

FONT = "/system/fonts/NotoSansCJK-Regular.ttc"
try:
    f_big = ImageFont.truetype(FONT, 15)
    f_small = ImageFont.truetype(FONT, 10)
except Exception:
    f_big = f_small = ImageFont.load_default(size=12)

NAMES = {
    0x82e0614: "枯叶市",
    0x82e9260: "6号道路",
    0x82df30c: "华蓝市",
    0x82d5844: "精灵中心",
    0x82d5cbc: "华蓝道馆",
    0x82e833c: "5号道路",
    0x83192f0: "地下通道入口(华蓝侧)",
    0x831989c: "地下通道",
}


def name_of(addr):
    return NAMES.get(addr, f"{addr:08x}")


def draw(out="map_links.png"):
    links = list(map_links._LINKS)
    if not links:
        print("没有连接数据")
        return
    maps = []
    for ln in links:
        if ln["map"] not in maps:
            maps.append(ln["map"])
        if ln["to_map"] not in maps:
            maps.append(ln["to_map"])

    W, H = 800, 600
    img = Image.new("RGB", (W, H), (250, 250, 252))
    d = ImageDraw.Draw(img)
    d.text((20, 15), f"地图连接（{len(maps)} 张地图，{len(links)} 条连接）",
           fill=(20, 20, 30), font=f_big)

    # 环形布局
    cx, cy, R = W / 2, H / 2 + 20, min(W, H) * 0.32
    pos = {}
    for i, m in enumerate(maps):
        ang = 2 * math.pi * i / max(len(maps), 1) - math.pi / 2
        x = cx + R * math.cos(ang)
        y = cy + R * math.sin(ang)
        pos[m] = (x, y)

    # 边
    for ln in links:
        x1, y1 = pos[ln["map"]]
        x2, y2 = pos[ln["to_map"]]
        ang = math.atan2(y2 - y1, x2 - x1)
        # 缩短到节点边缘
        L = 18
        sx, sy = x1 + L * math.cos(ang), y1 + L * math.sin(ang)
        ex, ey = x2 - L * math.cos(ang), y2 - L * math.sin(ang)
        d.line([sx, sy, ex, ey], fill=(90, 90, 110), width=2)
        # 箭头
        for s in (0.4, -0.4):
            d.line([ex, ey, ex - L * math.cos(ang - s), ey - L * math.sin(ang - s)],
                   fill=(90, 90, 110), width=2)
        # 标签（出口坐标）
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        d.text((mx - 18, my - 14), f"{tuple(ln['exit'])}", fill=(60, 60, 90), font=f_small)

    # 节点
    for m in maps:
        x, y = pos[m]
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(205, 230, 250),
                  outline=(70, 70, 90), width=2)
        label = name_of(m)
        tw = d.textlength(label, font=f_small)
        d.text((x - tw / 2, y + 20), label, fill=(20, 20, 40), font=f_small)

    img.save(out)
    print(f"saved {out}")


if __name__ == "__main__":
    draw(sys.argv[1] if len(sys.argv) > 1 else "map_links.png")
