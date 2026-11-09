"""离线测试：带转弯惩罚的寻路。"""
import sys
sys.path.insert(0, "/root/workspace")
import nav

# 构造 20x20 全可走地图（metatile 8，elev 3）
W = H = 20
vals = [0x3008 for _ in range(W * H)]


def turns(path):
    return sum(1 for i in range(1, len(path)) if path[i] != path[i - 1])


def test_prefers_straight():
    """宽敞空间：应该尽量直线走，转弯次数少。"""
    p = nav.bfs_turns(vals, W, H, (2, 2), (15, 10), set())
    assert p is not None
    t = turns(p)
    print(f"A 转弯次数: {t}, 路径长: {len(p)}")
    assert t <= 2, t     # 最多一个转弯（先横后竖）


def test_obstacle_detour():
    """中间有墙：需要绕行，但转弯仍应尽量少。"""
    blocked = set()
    for y in range(0, 15):
        blocked.add((10, y))       # 竖墙
    p = nav.bfs_turns(vals, W, H, (2, 5), (16, 5), blocked)
    assert p is not None
    print(f"B 绕墙：路径长 {len(p)}, 转弯 {turns(p)}")
    # 路径不能穿墙：逐格还原坐标检查
    x, y = 2, 5
    for d in p:
        dx, dy = nav.DELTA[d]
        x, y = x + dx, y + dy
        assert (x, y) not in blocked, (x, y)
    assert (x, y) == (16, 5), (x, y)


def test_no_path():
    """完全封死 -> None。"""
    blocked = {(x, 10) for x in range(W)}
    p = nav.bfs_turns(vals, W, H, (2, 2), (15, 15), blocked)
    print("C 封死 ->", p, "OK" if p is None else "FAIL")
    assert p is None


test_prefers_straight()
test_obstacle_detour()
test_no_path()
print("全部通过")
