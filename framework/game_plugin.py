"""游戏插件接口（契约）。

每个游戏一个目录：games/<game_id>/plugin.py，实现本协议。
平台（runner / 下屏 UI / 桥）只认这个接口，不知道具体游戏的内存细节。
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class GamePlugin(Protocol):
    """游戏插件协议（鸭子类型，不强制继承）。"""

    game_id: str
    """唯一标识，如 "pokemon_firered"。"""

    display_name: str
    """下屏显示名，如 "口袋妖怪 火红"。"""

    def attach(self, bridge) -> None:
        """注入平台桥（提供 rd/wr/press/frame）。"""

    def status(self) -> dict:
        """返回下屏要显示的状态。

        约定字段（都可选）：
          map: str       地图/场景名
          x: int, y: int 坐标
          team: list     队伍 [{name, lv, hp, max}]
          battle: str    战斗描述（空表示不在战斗）
          log: list[str] 事件日志
        """

    def decide(self) -> list:
        """返回下一步要按的键（如 ["UP", "A"]），空列表表示等待。"""

    def on_event(self, event: str) -> None:
        """平台事件回调（可选实现），如 "save"/"load"/"battle_start"。"""


def validate(plugin) -> list:
    """检查插件是否满足必需属性，返回缺失项列表（空 = 合格）。"""
    missing = []
    for attr in ("game_id", "display_name"):
        if not getattr(plugin, attr, None):
            missing.append(attr)
    for meth in ("attach", "status", "decide"):
        if not callable(getattr(plugin, meth, None)):
            missing.append(meth)
    return missing
