"""口袋妖怪 火红 插件：包装现有 info/state 模块，不改动它们。"""
import bdata
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
        detail = {}
        if battle:
            detail = self._battle_detail()
        return {
            "map": scene,
            "x": int(ctx.get("x", 0) or 0),
            "y": int(ctx.get("y", 0) or 0),
            "team": team,
            "battle": battle,
            "battle_detail": detail,
            "log": list(self._log[-20:]),
        }

    def _battle_detail(self):
        out = {}
        try:
            foe = bdata.enemy_info()
            if foe:
                out["foe"] = {"lv": foe.get("lv", 0), "hp": foe.get("hp", 0),
                              "mhp": foe.get("mhp", 0), "species": foe.get("species")}
        except Exception:
            pass
        try:
            me = bdata.my_mon(0)
            if me:
                names = []
                for mid in (me.get("moves") or [])[:4]:
                    if not mid:
                        names.append("")
                    else:
                        entry = bdata.MOVES.get(mid)
                        names.append(entry[0] if entry else "#%d" % mid)
                out["me"] = {"lv": me.get("lv", 0), "hp": me.get("hp", 0),
                             "mhp": me.get("mhp", 0), "moves": names}
        except Exception:
            pass
        return out

    def decide(self):
        # 第一步只做只读显示，决策仍走现有 battle_loop（后续再迁）
        return []

    def on_event(self, event):
        self._log.append(str(event))
