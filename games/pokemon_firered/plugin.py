"""口袋妖怪 火红 插件：包装现有 info/state 模块，不改动它们。"""
import json
import os

import bdata
import info
import state
import terrain


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
        minimap = self._minimap(int(ctx.get("x", 0) or 0), int(ctx.get("y", 0) or 0))
        return {
            "map": scene,
            "x": int(ctx.get("x", 0) or 0),
            "y": int(ctx.get("y", 0) or 0),
            "team": team,
            "battle": battle,
            "battle_detail": detail,
            "minimap": minimap,
            "log": list(self._log[-20:]),
        }

    _mm_cache = {}

    def _minimap(self, px, py):
        """当前地图的格子布局（按地图地址缓存，避免每次重复 locate_map）。"""
        try:
            addr, w, h = terrain.locate_map()
            if not addr or not w or not h:
                return getattr(self, "_mm_last", {})
            if addr not in self._mm_cache:
                path = os.path.normpath(os.path.join(
                    os.path.dirname(__file__), "maps", "map_%x.json" % addr))
                tiles = None
                if os.path.exists(path):
                    with open(path) as f:
                        raw = json.load(f).get("tiles")
                    # maps/*.json 存的是原始碰撞位（0=可走、非 0=挡）；推送前归一化成
                    # 1=可走，与 Kotlin `MapData` / MapWalker 的约定一致（UI 按 1=可走渲染）。
                    if raw:
                        tiles = [[1 if v == 0 else 0 for v in row] for row in raw]
                self._mm_cache[addr] = tiles
            out = {"w": w, "h": h, "px": px, "py": py, "tiles": self._mm_cache[addr]}
            self._mm_last = out
            return out
        except Exception:
            return getattr(self, "_mm_last", {})

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
