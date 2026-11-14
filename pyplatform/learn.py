"""学招处理：升级学招/「忘记哪个招式」界面（属于决策，不属于执行层）。

原放在 action.py，2026-11-10 迁出：
  - action 只负责按键/光标
  - 这里负责选「替换哪一招」并驱动 action
"""
import sys, time
sys.path.insert(0, "/root/workspace")

from state import snapshot

import action
import log


def learn_moves_guard(max_rounds=10):
    """战斗后处理升级学招/提示：遇到「是/否」选「是」，遇到普通对话按 A 推进。

    返回处理的提示次数。
    """
    from state import menu_kind
    handled = 0
    for _ in range(max_rounds):
        s = snapshot()
        if s["battle"]:
            break
        # 「忘记哪个招式？」界面：按优先级选择替换目标
        #   1) 变化技（0 威力）
        #   2) 一般属性技能（全攻击时）
        #   3) 威力最低的（全本属性时）
        if s["dialog"] and menu_kind() == "moves":
            log.info("learn", "forget_event", reason="检测到学招界面")
            from bdata import my_mon, MOVES
            from switch import active_slot
            slot = active_slot()
            m = my_mon(slot if slot is not None else 0)
            target = None
            reason = ""
            if m:
                moves = m.get("moves", [])
                info = [MOVES.get(mid, ("未知", "一般", 0)) for mid in moves]
                # 1) 变化技
                for i, (_, _, pw) in enumerate(info):
                    if pw <= 0:
                        target, reason = i, "替换变化技"
                        break
                # 2) 一般属性技能
                if target is None:
                    for i, (_, typ, pw) in enumerate(info):
                        if typ == "一般":
                            target, reason = i, "替换一般属性技"
                            break
                # 3) 威力最低
                if target is None and info:
                    target = min(range(len(info)), key=lambda i: info[i][2])
                    reason = f"替换威力最低({info[target][2]})"
            if target is not None:
                log.info("action", "forget_move_replace", slot=target, reason=reason)
                action.move_move_cursor(target)
                action.tap_a()
            else:
                log.info("action", "forget_move_cancel", reason="无合适替换")
                action.tap_b()
            time.sleep(0.7)
            handled += 1
            continue
        if s["choice"]:
            action.choose_option(0)        # 「要学习吗？」选「是」
            time.sleep(0.6)
            handled += 1
            continue
        if s["dialog"]:
            action.advance_dialog()
            time.sleep(0.5)
            continue
        break
    return handled


