"""场景处理器：把「裁剪后的数据」翻译成「决策」。

独立于 bridge 核心：增删场景只改这个文件 + register_scene。
处理器不直接操作按键（那是 action 的事），只产出决策结果。
"""
import sys
sys.path.insert(0, "/root/workspace")

import bridge
import bdata
import decision_battle
import decision_map


class InfoSource:
    """把 info 模块包装成 get(key) 接口，供 bridge.collect 使用。"""

    def get(self, key):
        import info
        from state import coords
        if key == "pos":
            return coords()
        if key == "map_id":
            import terrain
            a, w, h, _ = terrain.load()
            return hex(a) if a else None
        if key == "party":
            return [bdata.my_mon(i) for i in range(6)]
        if key == "party_hp":
            return [m["hp"] if m else None for m in (bdata.my_mon(i) for i in range(6))]
        if key == "me":
            import auto_battle
            slot = auto_battle.active_slot()
            return bdata.my_mon(slot) if slot is not None else None
        if key == "enemy":
            return bdata.enemy_info()
        if key == "menu":
            from state import menu_kind
            return menu_kind()
        if key == "options":
            return None
        if key == "dialog_kind":
            return "dialog" if __import__("state").in_dialog() else None
        return None


# ---------------- 各场景处理器 ----------------

def handle_battle(data):
    """战斗：选最优招式（多段/克制已由 decision 处理）。"""
    me = data.get("me")
    enemy = data.get("enemy")
    if not me or not enemy:
        return {"action": "none", "why": "缺战斗数据"}
    idx, why = decision_battle.choose_move(me, enemy.get("types"))
    return {"action": "move", "target": idx, "why": why}


def handle_map(data):
    """地图：这里只做占位，具体移动由寻路模块负责。"""
    pos = data.get("pos")
    return {"action": "walk", "why": f"地图 {pos} 继续走"}


def handle_dialog(data):
    """对话：推进。"""
    return {"action": "advance", "why": "推进对话"}


def handle_choice(data):
    """选项：选第一个（是/放出）。"""
    return {"action": "choose", "target": 0, "why": "选项第一项"}


# ---------------- 注册 ----------------

def register_all():
    """注册内置场景（增删功能就改这里）。"""
    bridge.register_scene("battle", ("me", "enemy", "party", "menu"), handle_battle)
    bridge.register_scene("map", ("pos", "map_id", "party_hp"), handle_map)
    bridge.register_scene("dialog", ("pos", "dialog_kind"), handle_dialog)
    bridge.register_scene("choice", ("pos", "options"), handle_choice)


def unregister_all():
    for s in list(bridge.registered_scenes()):
        bridge.unregister_scene(s)
