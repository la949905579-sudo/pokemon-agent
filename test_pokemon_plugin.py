"""Pokemon 插件测试（全离线：导入前替换 info/state，避免真实网络访问）。"""
import sys
import unittest
from unittest import mock

# 必须在导入插件之前替换重模块
_fake_info = mock.MagicMock()
_fake_state = mock.MagicMock()
sys.modules["info"] = _fake_info
sys.modules["state"] = _fake_state

from framework.game_plugin import GamePlugin, validate  # noqa: E402
from games.pokemon_firered import PokemonFireRedPlugin  # noqa: E402


class FakeBridge:
    def rd(self, addr, n): return b"\0" * n
    def wr(self, addr, data): pass
    def press(self, name, dur=0.08): pass
    def frame(self): return 0


class PokemonPluginTest(unittest.TestCase):
    def setUp(self):
        _fake_info.context.reset_mock()
        _fake_state.party.reset_mock()
        _fake_info.context.return_value = {"scene": "map", "x": 0, "y": 0, "turn": 0}
        _fake_state.party.return_value = (0, [])

    def test_contract(self):
        p = PokemonFireRedPlugin()
        self.assertEqual(validate(p), [])
        self.assertIsInstance(p, GamePlugin)
        self.assertEqual(p.game_id, "pokemon_firered")

    def test_status_maps_context(self):
        p = PokemonFireRedPlugin()
        p.attach(FakeBridge())
        _fake_info.context.return_value = {"scene": "map", "x": 12, "y": 8}
        _fake_state.party.return_value = (0x02024284, [(10, 29, 29), (8, 20, 22)])
        s = p.status()
        self.assertEqual(s["map"], "map")
        self.assertEqual(s["x"], 12)
        self.assertEqual(len(s["team"]), 2)
        self.assertEqual(s["team"][0]["lv"], 10)
        self.assertEqual(s["battle"], "")

    def test_status_battle_detected(self):
        _fake_info.context.return_value = {"scene": "battle_main", "x": 0, "y": 0}
        s = PokemonFireRedPlugin().status()
        self.assertIn("battle", s["battle"])

    def test_status_survives_errors(self):
        _fake_info.context.side_effect = RuntimeError("no game")
        try:
            s = PokemonFireRedPlugin().status()
        finally:
            _fake_info.context.side_effect = None
        self.assertEqual(s["x"], 0)
        self.assertEqual(s["team"], [])

    def test_decide_and_events(self):
        _fake_info.context.return_value = {"scene": "map", "x": 0, "y": 0}
        p = PokemonFireRedPlugin()
        self.assertEqual(p.decide(), [])
        p.on_event("save")
        self.assertIn("save", p.status()["log"])


if __name__ == "__main__":
    import sys as _sys
    suite = unittest.defaultTestLoader.loadTestsFromModule(_sys.modules[__name__])
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    if res.wasSuccessful():
        print("全部通过")
    else:
        _sys.exit(1)
