"""战斗主循环：看 info -> 经 decision -> 交 action。"""
import struct, sys, time
sys.path.insert(0, "/root/workspace")
import info, action, decision
from bdata import my_mon, enemy_info
import switch
import switch as _sw

import watchdog
import log
from watchdog import _watchdog, wait_round_end

_flee_blocked = False   # 本场逃跑失败过（训练家战），不再尝试
_active_switch_failed = False  # 本场主动换人失败过，不再尝试
_opening_checked = False       # 开场换人只判断一次
_zero_hp_pushes = 0          # 敌方 0 血推进次数（防死循环）
from state import in_battle
import state

def _enemy_moves():
    from addresses import EN_BATTLE
    d = state.rd(EN_BATTLE + 0x0C, 8)
    return list(struct.unpack("<4H", d)) if len(d) == 8 else []


def _u16(addr):
    d = state.rd(addr, 2)
    return struct.unpack("<H", d)[0] if len(d) == 2 else None


def _emit_round(cb, r, slot, m, idx, why, e, fired, res):
    """本回合观测交给回调（回调异常不影响战斗）。"""
    try:
        from addresses import MY_BATTLE, EN_BATTLE, MOVE_LAST
        cur = my_mon(slot) or {}
        raw_en = state.rd(EN_BATTLE + 0x0C, 8)
        rec = {
            "r": r, "slot": slot, "species": m.get("species"), "lv": m.get("lv"),
            "hp": m.get("hp"), "moves": list(m.get("moves") or []),
            "pp_before": list(m.get("pp") or []), "pp_after": cur.get("pp"),
            "idx": idx, "why": why, "fired": fired, "result": res,
            "foe": {k: (e or {}).get(k) for k in ("species", "lv", "hp", "mhp")},
            "field_species": _u16(MY_BATTLE),
            "d4c": _u16(MOVE_LAST),
            "foe_moves": list(struct.unpack("<4H", raw_en)) if len(raw_en) == 8 else [],
        }
        rec["slot_ok"] = rec["field_species"] == rec["species"]
        cb(rec)
    except Exception as ex:
        log.error("battle", "on_round_fail", err=str(ex))


def battle_loop(max_rounds=12, verbose=True, allow_switch=True, on_round=None):
    """薄协调层：看 info 的场景，用 decision 决定，交给 action 执行。"""
    global _flee_blocked, _active_switch_failed, _opening_checked, _zero_hp_pushes
    lv_before = {i: (my_mon(i) or {}).get("lv") for i in range(6)}
    if info.scene() == info.BATTLE_INTRO:
        # 刚进战斗：游戏会按队伍顺序派第一只健康的，重置内部顺序
        switch.reset_party_order()
        _flee_blocked = False
        _active_switch_failed = False
        _opening_checked = False
        _zero_hp_pushes = 0

    for r in range(max_rounds):
        if in_battle() is False:
            watchdog._wd["last"] = None
            watchdog._wd["count"] = 0
            # 战斗结束：先看等级有没有变化（判断是否升级）
            lv_after = {i: (my_mon(i) or {}).get("lv") for i in range(6)}
            levelups = [(i, lv_before.get(i), lv_after.get(i))
                        for i in range(6)
                        if lv_before.get(i) is not None and lv_after.get(i) is not None
                        and lv_after.get(i) > lv_before.get(i)]
            if levelups:
                for slot, b, a in levelups:
                    log.info("battle", "levelup", slot=slot, before=b, after=a)
                if verbose:
                    print(f"  升级! {levelups}", flush=True)
                # 升级后学招提示更多：加强检测（多轮 + 稍等）
                time.sleep(0.8)
                handled = action.learn_moves_guard(max_rounds=20)
                log.info("battle", "learn_handled", count=handled)
                return "win_levelup"
            action.learn_moves_guard()
            return "win"
        sc = info.scene()
        e_now = enemy_info()
        slot_now = switch.active_slot()
        m_now = my_mon(slot_now) if slot_now is not None else None
        key = (sc, e_now.get("hp") if e_now else None,
               m_now.get("hp") if m_now else None)
        if _watchdog(key):
            if verbose:
                print("  看门狗: 状态无进展，尝试按 A 推进", flush=True)
            action.tap_a()
            time.sleep(0.8)
            if _watchdog(key, limit=3):
                if verbose:
                    print("  看门狗: 仍未推进，按 B 退出子菜单", flush=True)
                action.tap_b()
                time.sleep(0.8)

        if sc == info.ANIM:
            # 动画一般自己结束；但对话/特性播报会停在 turn=4 等按键
            if not action.wait_until(lambda: info.scene() != info.ANIM, 1.2):
                action.advance_dialog()
            continue

        if sc == info.BATTLE_INTRO:
            action.advance_dialog()
            continue

        if sc == info.CHOICE:
            # 「要使用下一只宝可梦吗？」-> 选「是」
            action.choose_option(0)
            action.wait_until(lambda: info.scene() != info.CHOICE, 2.0)
            continue

        if sc == info.PARTY_OPTION:
            # 濒死/强制换人：界面顺序 = 队伍原始槽位（0-5），不是 party_order
            party = [my_mon(i) for i in range(6)]
            e = enemy_info()
            active_now = switch.active_slot()
            healthy = [m for m in party
                       if m and m.get("hp", 0) > 0 and m.get("slot") != active_now]
            if not healthy:
                return "fainted"
            target = max(healthy, key=lambda m: decision.score_switch(m, e))["slot"]
            if verbose:
                print(f"  濒死换人: 选槽位 {target}", flush=True)
            action.move_party_cursor(target)
            action.tap_a()
            time.sleep(0.8)
            action.wait_until(lambda: info.scene() != info.PARTY_OPTION, 3.0)
            if info.scene() == info.PARTY_OPTION:
                # 还在界面：可能打开了「放出/概况/取消」，选放出
                action.choose_option(0)
                action.wait_until(lambda: info.scene() != info.PARTY_OPTION, 2.0)
            switch.ensure_active()   # 濒死换人不走 _pick_and_switch，这里校正出场槽位
            continue

        if sc == info.PARTY:
            if switch.switch_blocked():
                # 本场换人已被拒（束缚等），退出队伍菜单继续打
                if verbose:
                    print("  换人被拒，退出队伍菜单继续战斗", flush=True)
                action.tap_b()
                time.sleep(0.6)
                continue
            party = [my_mon(i) for i in range(6)]
            e = enemy_info()
            target = decision.choose_switch(party, e)
            if target is None:
                return "fainted"
            if not switch._pick_and_switch(target, verbose, "换人"):
                # 换人被拒：不返回 stuck，退出菜单继续打
                action.tap_b()
                time.sleep(0.6)
                continue
            continue

        if sc in (info.BATTLE_MAIN, info.BATTLE_MOVES):
            # 槽位自检：换人流程后 order 可能过期，按场上 species 校正
            switch.ensure_active()
            # 记录我方异常状态（睡眠/麻痹不影响出招流程，游戏会自己处理）
            st = state.status_flags(0)
            if st and (st.get("sleep") or st.get("freeze") or st.get("paralysis")):
                log.info("battle", "status", sleep=st.get("sleep"),
                         freeze=st.get("freeze"), paralysis=st.get("paralysis"))

            # 敌方 HP 为 0：可能在换下一只/结算动画中，按 A 推进
            e_check = enemy_info()
            if e_check and e_check.get("hp") == 0:
                _zero_hp_pushes += 1
                if _zero_hp_pushes > 8:
                    log.error("battle", "enemy_zero_stuck")
                    return "stuck"
                if verbose:
                    print(f"  敌方倒下，推进结算({_zero_hp_pushes})", flush=True)
                action.tap_a()
                time.sleep(0.8)
                continue
            _zero_hp_pushes = 0

            # 首发固定为队首（游戏机制），不做开场换人；
            # 队首不利时由下面的「主动换人」在第一回合处理。

            # 数据异常：战斗数据结构读不到（可能被束缚/状态混乱）-> 换人试探
            if sc == info.BATTLE_MAIN and state.status_flags(0) is None \
                    and not _active_switch_failed and not switch.switch_blocked():
                log.error("battle", "data_invalid_try_switch")
                active_x = switch.active_slot()
                if active_x is not None:
                    tgt_x = 1 if active_x != 1 else 2
                    if switch.switch_from_main(tgt_x, verbose, "数据异常试探"):
                        continue
                    _active_switch_failed = True

            # 开场换人：队首评分低于最佳候选 -> 第一回合直接换（不浪费一回合出招）
            if allow_switch and not _opening_checked and not switch.switch_blocked() and not state.trapped() and not _active_switch_failed:
                _opening_checked = True
                active0 = switch.active_slot()
                party_a = [my_mon(i) for i in range(6)]
                e_a = enemy_info()
                tgt0 = decision.should_switch_opening(party_a, e_a, active0)
                if tgt0 is not None:
                    if sc == info.BATTLE_MOVES:
                        action.close_menu()
                    if verbose:
                        print(f"  开场换人: 槽{active0} -> 槽{tgt0}", flush=True)
                    if switch.switch_from_main(tgt0, verbose, "开场换人"):
                        continue
                    _active_switch_failed = True

            # 主动换人：被克制 / 血量低 / 有更好目标（每回合检查）
            # 血量极低（<15%）时是紧急情况，即使之前换人失败过也要再试
            slot_now = switch.active_slot()
            m_now = my_mon(slot_now) if slot_now is not None else None
            # 血量低于 50% 视为「紧急」，即使之前换人失败过也再试
            urgent_low = bool(m_now and m_now.get("mhp")
                              and m_now.get("hp", 0) / m_now["mhp"] < 0.5)
            if allow_switch and not switch.switch_blocked() and not state.trapped() \
                    and (not _active_switch_failed or urgent_low):
                active = switch.active_slot()
                party_now = [my_mon(i) for i in range(6)]
                e_now = enemy_info()
                tgt = decision.should_switch(party_now, e_now, active)
                if tgt is not None:
                    if sc == info.BATTLE_MOVES:
                        action.close_menu()
                    if verbose:
                        print(f"  主动换人: 槽{active} -> 槽{tgt}", flush=True)
                    if switch.switch_from_main(tgt, verbose, "主动换人"):
                        continue
                    _active_switch_failed = True
                    if verbose:
                        print("  主动换人失败，本场不再尝试", flush=True)

            # 逃跑检查：等级差太大 / 血量极低 / 被克制且血少
            if not _flee_blocked and not state.trapped():
                slot_f = switch.active_slot()
                m_f = my_mon(slot_f) if slot_f is not None else None
                e_f = enemy_info()
                if m_f and e_f and decision.should_flee(
                        m_f, e_f, [my_mon(i) for i in range(6)],
                        enemy_species=e_f.get("species"),
                        trapped=switch.switch_blocked() or state.trapped()):
                    if sc == info.BATTLE_MOVES:
                        action.close_menu()
                    if verbose:
                        print(f"  逃跑: 我方Lv{m_f['lv']} {m_f['hp']}/{m_f['mhp']}"
                              f" vs 敌方Lv{e_f['lv']}", flush=True)
                    action.run_away()
                    time.sleep(0.8)
                    if in_battle() is not False:
                        # 逃不掉（训练家战）：关掉提示，本场不再尝试
                        for _ in range(4):
                            action.tap_a()
                            time.sleep(0.5)
                            if in_battle() is False:
                                break
                        if in_battle() is not False:
                            _flee_blocked = True
                            if verbose:
                                print("  逃跑失败（可能是训练家战），本场不再尝试", flush=True)
                    continue

            slot = switch.active_slot()
            m = my_mon(slot) if slot is not None else None
            e = enemy_info()
            if not m or not e:
                return "nodata"
            idx, why = decision.choose_move(m, e["types"])
            # 没有可用攻击招（全是变化招 / PP 耗尽）：优先换一只能打的
            if not decision.has_attack_move(m):
                cands = [mm for mm in (my_mon(i) for i in range(6))
                         if mm and mm.get("hp", 0) > 0 and mm["slot"] != slot
                         and decision.has_attack_move(mm)]
                tgt_n = decision.choose_switch(cands, e) if cands else None
                if tgt_n is not None and allow_switch and not _active_switch_failed \
                        and not switch.switch_blocked() and not state.trapped():
                    if sc == info.BATTLE_MOVES:
                        action.close_menu()
                    if verbose:
                        print(f"  无可用攻击招: 槽{slot} -> 槽{tgt_n}", flush=True)
                    if switch.switch_from_main(tgt_n, verbose, "无攻击招换人"):
                        continue
                    _active_switch_failed = True
            foe_mv = _enemy_moves()
            threat = decision.threat_score(foe_mv, m.get("types"))
            log.info("battle", "round", r=r,
                     me=f"Lv{m.get('lv',0)} {m.get('hp',0)}/{m.get('mhp','?')}",
                     foe=f"Lv{e.get('lv',0)} {e.get('hp',0)}/{e.get('mhp','?')}",
                     idx=idx, why=why, threat=threat, foe_moves=foe_mv)
            if verbose:
                print(f"回合{r}: 我方#{slot} Lv{m['lv']} {m['hp']}/{m['mhp']} "
                      f"vs 敌方Lv{e['lv']} {e['hp']}/{e['mhp']} -> {why}", flush=True)
            if sc == info.BATTLE_MAIN:
                if not action.open_move_menu():
                    continue
            fired = action.use_move(idx)
            if not fired:
                # 闭环：出招没生效（turn 没变）-> 重试一次
                if verbose:
                    print("  闭环: 出招未生效，重试", flush=True)
                if sc != info.BATTLE_MOVES:
                    action.open_move_menu()
                fired = action.use_move(idx)
                if not fired and verbose:
                    print("  闭环: 重试仍失败，交给看门狗", flush=True)
            if fired:
                res = wait_round_end()
                if verbose and res == "timeout":
                    print("  闭环: 等回合完成超时", flush=True)
                if on_round:
                    _emit_round(on_round, r, slot, m, idx, why, e, fired, res)
            continue

        # 其它子菜单：先退出来
        action.tap_b()
        time.sleep(0.6)

    # 轮次用完仍卡着：退回主菜单，必要时逃跑，避免卡死在子菜单
    try:
        action.close_menu()
        if in_battle() is not False:
            action.run_away()
    except Exception:
        pass
    return "timeout"


if __name__ == "__main__":
    print("start", menu_kind())
    print("result", battle_loop())
