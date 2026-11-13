"""emu_bridge 离线单测：mock socket，不连实机。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import socket
import unittest
from unittest import mock

import emu_bridge


class FakeSocket:
    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []

    def sendall(self, data):
        self.sent.append(data.decode().strip())

    def recv(self, n):
        if not self.replies:
            return b""
        return (self.replies.pop(0) + "\n").encode()

    def close(self):
        pass

    def settimeout(self, t):
        pass


class EmuBridgeTest(unittest.TestCase):
    def setUp(self):
        emu_bridge._conn = None

    def tearDown(self):
        emu_bridge._conn = None

    def _patch(self, replies):
        fake = FakeSocket(replies)
        return mock.patch("socket.create_connection", return_value=fake), fake

    def test_ping(self):
        p, fake = self._patch(["pong"])
        with p:
            self.assertTrue(emu_bridge.ping())
        self.assertEqual(fake.sent, ["ping"])

    def test_rd(self):
        p, fake = self._patch(["ok aabbccdd"])
        with p:
            self.assertEqual(emu_bridge.rd(0x0202C000, 4), b"\xaa\xbb\xcc\xdd")
        self.assertEqual(fake.sent, ["read 202c000 4"])

    def test_rd_short_raises(self):
        p, _ = self._patch(["ok aa", "ok aa"])
        with p:
            with self.assertRaises(Exception):
                emu_bridge.rd(0x100, 4, retries=1)

    def test_wr(self):
        p, fake = self._patch(["ok"])
        with p:
            emu_bridge.wr(0x0202C000, b"\x01\x02")
        self.assertEqual(fake.sent, ["write 202c000 0102"])

    def test_press_single_and_combo(self):
        p, fake = self._patch(["ok", "ok"])
        with p:
            emu_bridge.press("A", 0.1)
            emu_bridge.press("UP+A", 0.2)
        self.assertEqual(fake.sent, ["press 1 100", "press 65 200"])

    def test_press_unknown_key(self):
        with self.assertRaises(ValueError):
            emu_bridge.press("XYZ")

    def test_frame(self):
        p, _ = self._patch(["ok 12345"])
        with p:
            self.assertEqual(emu_bridge.frame(), 12345)


if __name__ == "__main__":
    import sys
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    if res.wasSuccessful():
        print("全部通过")
    else:
        sys.exit(1)
