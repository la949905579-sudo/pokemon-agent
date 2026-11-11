"""新游戏插件模板：复制这个目录，改 game_id / 内存读取 / 决策。"""


class TemplatePlugin:
    game_id = "template"
    display_name = "模板游戏"

    def __init__(self):
        self.bridge = None

    def attach(self, bridge):
        self.bridge = bridge

    def status(self):
        return {
            "map": "",
            "x": 0,
            "y": 0,
            "team": [],
            "battle": "",
            "log": [],
        }

    def decide(self):
        # 返回按键名列表，如 ["A"]；空列表表示等待
        return []

    def on_event(self, event):
        pass
