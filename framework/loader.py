"""按 game_id 加载游戏插件（约定：games/<id>/plugin.py 里叫 Plugin 或唯一插件类）。"""
import importlib

from framework.game_plugin import validate


def load(game_id):
    mod = importlib.import_module("games.%s.plugin" % game_id)
    cls = getattr(mod, "Plugin", None)
    if cls is None:
        candidates = [v for k, v in vars(mod).items()
                      if isinstance(v, type) and getattr(v, "game_id", None)]
        if len(candidates) != 1:
            raise ImportError("无法确定 %s 的插件类（找到 %d 个）" % (game_id, len(candidates)))
        cls = candidates[0]
    plugin = cls()
    missing = validate(plugin)
    if missing:
        raise TypeError("插件 %s 缺少: %s" % (game_id, ", ".join(missing)))
    return plugin


def available():
    """列出可发现的插件 id。"""
    import os
    root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "games")
    out = []
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            p = os.path.join(root, name, "plugin.py")
            if os.path.isfile(p):
                out.append(name)
    return out
