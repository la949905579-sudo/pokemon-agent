"""离线测试：中间层（注册制 + 裁剪 + 分发）。"""
import sys
sys.path.insert(0, "/root/workspace")
import bridge
import handlers


class MockSource:
    def __init__(self, **kw):
        self.d = kw
    def get(self, k):
        return self.d.get(k)


def test_register_and_route():
    handlers.register_all()
    src = MockSource(me={"lv": 27}, enemy={"types": ["一般"]}, party=[], menu="main",
                     pos=(1, 2), map_id="0x1", party_hp=[1, 2])
    req = bridge.route("battle", src)
    print("A 战斗裁剪:", sorted(req.data.keys()))
    assert set(req.data.keys()) == {"me", "enemy", "party", "menu"}

    req2 = bridge.route("map", src)
    print("B 地图裁剪:", sorted(req2.data.keys()))
    assert set(req2.data.keys()) == {"pos", "map_id", "party_hp"}


def test_dispatch():
    handlers.register_all()
    src = MockSource(me={"lv": 27, "moves": [31], "pp": [10]},
                     enemy={"types": ["草"]}, party=[], menu="main")
    req = bridge.route("battle", src)
    d = bridge.dispatch(req)
    print("C 战斗决策:", d)
    assert d["action"] == "move"


def test_unknown_scene():
    req = bridge.route("shop", MockSource())
    print("D 未注册场景:", req.scene, req.note)
    assert req.scene == "unknown"


def test_custom_scene_plugin():
    """新增功能 = 注册一个场景，不改核心。"""
    def handle_shop(data):
        return {"action": "buy", "why": f"买 {data.get('item')}"}

    bridge.register_scene("shop", ("item",), handle_shop)
    req = bridge.route("shop", MockSource(item="伤药"))
    d = bridge.dispatch(req)
    print("E 插件场景:", d)
    assert d["action"] == "buy"
    bridge.unregister_scene("shop")
    print("F 注销后:", bridge.route("shop", MockSource()).scene)
    assert bridge.route("shop", MockSource()).scene == "unknown"


test_register_and_route()
test_dispatch()
test_unknown_scene()
test_custom_scene_plugin()
print("全部通过")
