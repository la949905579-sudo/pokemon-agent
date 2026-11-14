"""runner / loader 离线测试。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
import unittest

from framework import loader
from framework.runner import Runner


class FakePlugin:
    game_id = "fake"
    display_name = "Fake"

    def __init__(self):
        self.calls = []
        self.steps = 0

    def attach(self, bridge):
        self.bridge = bridge

    def status(self):
        return {"map": "map", "x": self.steps, "y": 0, "team": [], "battle": ""}

    def decide(self):
        self.steps += 1
        return ["A"] if self.steps % 2 else []

    def on_event(self, event):
        pass


class FakeBridge:
    def __init__(self):
        self.presses = []

    def press(self, name, dur=0.08):
        self.presses.append(name)


class RunnerTest(unittest.TestCase):
    def test_step_calls_plugin_and_bridge(self):
        p = FakePlugin()
        b = FakeBridge()
        pushed = []
        r = Runner(p, b, push=pushed.append)
        status, keys = r.step()
        self.assertEqual(p.steps, 1)
        self.assertEqual(status["x"], 0)     # status() 在 decide() 之前
        self.assertEqual(keys, ["A"])
        self.assertEqual(b.presses, ["A"])
        self.assertEqual(len(pushed), 1)

    def test_run_max_steps(self):
        p = FakePlugin()
        r = Runner(p, FakeBridge(), interval=0)
        n = r.run(max_steps=3)
        self.assertEqual(n, 3)
        self.assertEqual(p.steps, 3)

    def test_push_failure_does_not_break_loop(self):
        def bad_push(_):
            raise RuntimeError("down")
        r = Runner(FakePlugin(), FakeBridge(), push=bad_push, interval=0)
        self.assertEqual(r.run(max_steps=2), 2)

    def test_stop(self):
        p = FakePlugin()
        r = Runner(p, FakeBridge(), interval=0)
        r.running = True
        r.stop()
        self.assertFalse(r.running)


class LoaderTest(unittest.TestCase):
    def test_available_contains_template(self):
        self.assertIn("_template", loader.available())

    def test_load_template(self):
        p = loader.load("_template")
        self.assertEqual(p.game_id, "template")
        self.assertEqual(p.decide(), [])

    def test_load_unknown_raises(self):
        with self.assertRaises(ImportError):
            loader.load("no_such_game")


if __name__ == "__main__":
    import sys
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    if res.wasSuccessful():
        print("全部通过")
    else:
        sys.exit(1)
