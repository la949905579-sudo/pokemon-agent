"""信息获取层：只读内存，回答「现在是什么场景」。

这一层不决策、不按键，只把内存翻译成「场景 + 上下文」，供决策层使用。
场景划分依据实测：
  E82=0 开场 / 1 主菜单或选项框 / 2 子菜单 / 4 动画
  选项框：E83=0（见 snapshot 的 choice）；主菜单：E83=1
  二级菜单（放出/概况/取消）也在 turn=2，靠 menu_kind 区分招式菜单
"""
import sys
sys.path.insert(0, "/root/workspace")
from state import (rd, coords, in_battle, in_dialog, turn_state, menu_kind,
                   cursor, party_cursor, bag_cursor, player_facing, snapshot)

# ---- 场景常量 ----
MAP = "map"                  # 地图上（可读坐标）
BATTLE_INTRO = "battle_intro"    # 战斗开场对话
BATTLE_MAIN = "battle_main"      # 战斗主菜单（战斗/背包/宝可梦/逃跑）
BATTLE_MOVES = "battle_moves"    # 招式选择
BATTLE_SUBMENU = "battle_submenu"  # 其它战斗子菜单
PARTY = "party"                  # 队伍列表（换人界面）
PARTY_OPTION = "party_option"    # 队伍里的「放出/概况/取消」
CHOICE = "choice"                # 是/否 选项框（如「要使用下一只宝可梦吗？」）
ANIM = "anim"                    # 动画/结算中
UNKNOWN = "unknown"


# ---------------- 扩展接口：接入新场景 ----------------
_scene_hooks = []      # [(priority, name, detector)]


def register_scene(name, detector, priority=0):
    """注册一个新场景检测器。

    detector() -> bool；命中时 scene() 返回 name。
    新界面先用它接入跑通，稳定后再固化进 scene() 的内置分支。
    priority 越大越先检测。
    """
    _scene_hooks.append((priority, name, detector))
    _scene_hooks.sort(key=lambda x: -x[0])
    return name


def unregister_scene(name):
    global _scene_hooks
    _scene_hooks = [h for h in _scene_hooks if h[1] != name]


def registered_scenes():
    return [h[1] for h in _scene_hooks]


def scene():
    """当前场景字符串（先查注册的扩展场景，再走内置判定）。"""
    for _, name, fn in _scene_hooks:
        try:
            if fn():
                return name
        except Exception:
            continue
    s = snapshot()
    if not s["battle"]:
        return MAP
    t = s["turn"]
    if t == 0:
        return BATTLE_INTRO
    if t == 4:
        # 濒死/强制换人时游戏也会给 turn=4，但此时有队伍光标（换人界面）
        from state import party_cursor
        if party_cursor() is not None and menu_kind() == "party":
            return PARTY_OPTION
        return ANIM
    if t == 1:
        if s.get("choice"):
            return CHOICE
        if menu_kind() == "party":
            return PARTY
        return BATTLE_MAIN
    if t == 2:
        k = menu_kind()
        if k == "moves":
            return BATTLE_MOVES
        if s.get("choice") or k == "party":
            return PARTY_OPTION
        return BATTLE_SUBMENU
    return UNKNOWN


def context():
    """场景 + 光标等上下文，给决策层用。"""
    sc = scene()
    s = snapshot()
    ctx = {"scene": sc, "x": s["x"], "y": s["y"], "turn": s["turn"]}
    if sc in (BATTLE_MAIN, BATTLE_MOVES, PARTY, PARTY_OPTION, CHOICE, BATTLE_SUBMENU):
        ctx["main_cursor"] = cursor()
        ctx["party_cursor"] = party_cursor()
    return ctx


def trapped():
    """我方场上是否被束缚（无法换人/逃跑）。"""
    from state import trapped as _t
    return _t()


def sleeping():
    """我方场上宝可梦是否处于睡眠状态。"""
    from state import sleep_turns
    v = sleep_turns()
    return bool(v and v > 0)


def sleep_remaining():
    """睡眠剩余回合（None=读不到，0=没睡）。"""
    from state import sleep_turns
    return sleep_turns()


def battle_status(slot=0):
    """战斗状态字段解析：{sleep, poison, burn, freeze, paralysis, toxic}。"""
    from state import status_flags
    return status_flags(slot)


def paralyzed(slot=0):
    """指定一方是否麻痹（0=我方，1=敌方）。"""
    f = battle_status(slot)
    return bool(f and f["paralysis"])


def consistent_snapshot(max_tries=3):
    """一致性快照：读前读后坐标和回合数不变，才算一次可信读取。

    防止「读坐标时游戏正好在换人/动画」导致决策层用拼接的旧数据。
    """
    from state import snapshot as _snap, coords as _coords, turn_state as _turn
    data = _snap()
    for _ in range(max_tries):
        p0, t0 = _coords(), _turn()
        data = _snap()
        p1, t1 = _coords(), _turn()
        if p0 == p1 and t0 == t1:
            return data
    return data      # 尽力而为：读不到稳定值就返回最后一次


def facing():
    """当前角色朝向：up / down / left / right；读不到返回 None。"""
    return player_facing()


def on_map():
    return scene() == MAP


def in_battle_scene():
    return scene() in (BATTLE_INTRO, BATTLE_MAIN, BATTLE_MOVES, BATTLE_SUBMENU,
                       PARTY, PARTY_OPTION, CHOICE, ANIM)
