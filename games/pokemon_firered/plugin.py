"""口袋妖怪 火红 插件：包装现有 info/state 模块，不改动它们。"""
import info
import state


class PokemonFireRedPlugin:
    game_id = "pokemon_firered"
    display_name = "口袋妖怪 火红"

    def __init__(self):
        self.bridge = None
        self._log = []

    def attach(self, bridge):
        self.bridge = bridge

    def status(self):
        try:
            ctx = info.context()
        except Exception:
            return {"map": "", "x": 0, "y": 0, "team": [], "battle": "", "log": list(self._log)}

        scene = str(ctx.get("scene", ""))
        team = []
        try:
            _, lvs = state.party()
            for i, (lv, hp, mhp) in enumerate(lvs or []):
                if lv > 0:
                    team.append({"name": "#%d" % (i + 1), "lv": lv, "hp": hp, "max": mhp})
        except Exception:
            team = []

        battle = scene if "battle" in scene.lower() else ""
        return {
            "map": scene,
            "x": int(ctx.get("x", 0) or 0),
            "y": int(ctx.get("y", 0) or 0),
            "team": team,
            "battle": battle,
            "log": list(self._log[-20:]),
        }

    def decide(self):
        # 第一步只做只读显示，决策仍走现有 battle_loop（后续再迁）
        return []

    def on_event(self, event):
        self._log.append(str(event))
