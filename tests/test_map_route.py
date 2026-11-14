"""离线测试：跨图 A* 规划（只读连接表，不碰游戏）。"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
import map_route

R6, VT, R5, ST = 0x82e9260, 0x82e0614, 0x82e833c, 0x83192f0


def test_same_map():
    assert map_route.plan(R6, R6) == []
    print("A 同图返回空 ok")


def test_simple():
    r = map_route.plan(R6, VT)
    assert r and len(r) == 1, r
    assert r[0]["exit"] == (12, 39) and r[0]["to"] == VT, r
    print("B 6号 -> 枯叶 单段 ok", r[0]["exit"])


def test_reused_marked():
    r = map_route.plan(R6, R5)
    assert r and any(e["reused"] for e in r), r
    print("C 复用房间边被标记 ok")


def test_no_route():
    assert map_route.plan(0x1234567, R6) is None
    print("D 无路返回 None ok")


def test_fixed_table():
    assert map_route.FIXED[(R6, R5)] == "route_6_to_5"
    assert map_route.FIXED[(R5, R6)] == "route_5_to_6"
    print("E 固定路线回退表 ok")


test_same_map()
test_simple()
test_reused_marked()
test_no_route()
test_fixed_table()
print("全部通过")
