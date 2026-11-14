"""插件接口契约测试（离线，不连实机）。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
import unittest

from framework.game_plugin import GamePlugin, validate
from games._template import TemplatePlugin


class FakeBridge:
    def rd(self, addr, n): return b"\0" * n
    def wr(self, addr, data): pass
    def press(self, name, dur=0.08): pass
    def frame(self): return 0


class GamePluginContractTest(unittest.TestCase):
    def test_template_satisfies_protocol(self):
        p = TemplatePlugin()
        self.assertEqual(validate(p), [])
        self.assertIsInstance(p, GamePlugin)

    def test_template_status_shape(self):
        p = TemplatePlugin()
        p.attach(FakeBridge())
        s = p.status()
        for key in ("map", "x", "y", "team", "battle"):
            self.assertIn(key, s)
        self.assertIsInstance(s["team"], list)

    def test_template_decide_returns_list(self):
        p = TemplatePlugin()
        p.attach(FakeBridge())
        self.assertIsInstance(p.decide(), list)

    def test_validate_reports_missing(self):
        class Bad:
            game_id = ""
            display_name = "x"
        self.assertIn("game_id", validate(Bad()))

    def test_validate_reports_missing_method(self):
        class Bad2:
            game_id = "g"
            display_name = "n"
            def attach(self, b): pass
        missing = validate(Bad2())
        self.assertIn("status", missing)
        self.assertIn("decide", missing)


if __name__ == "__main__":
    import sys
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    if res.wasSuccessful():
        print("全部通过")
    else:
        sys.exit(1)
