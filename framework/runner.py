"""通用主循环：读状态 → 决策 → 执行 → 推送状态。

与具体游戏无关；游戏差异全部由 GamePlugin 承担。
"""
import time


class Runner:
    def __init__(self, plugin, bridge, push=None, interval=0.1):
        self.plugin = plugin
        self.bridge = bridge
        self.push = push          # callable(status: dict) -> None
        self.interval = interval
        self.steps = 0
        self.running = False
        self.last_status = {}
        self.last_keys = []

    def step(self):
        """跑一轮：状态 -> 决策 -> 按键 -> 推送。返回 (status, keys)。"""
        status = self.plugin.status() or {}
        self.last_status = status
        if self.push:
            try:
                self.push(status)
            except Exception:
                pass
        keys = list(self.plugin.decide() or [])
        self.last_keys = keys
        for k in keys:
            self.bridge.press(k)
        self.steps += 1
        return status, keys

    def run(self, max_steps=None):
        self.running = True
        try:
            while self.running:
                self.step()
                if max_steps is not None and self.steps >= max_steps:
                    break
                time.sleep(self.interval)
        finally:
            self.running = False
        return self.steps

    def stop(self):
        self.running = False
