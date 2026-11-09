"""换人模块：战斗内部队伍顺序 + 换人动作。"""
"""自动战斗：B 跳对话 -> 读数据 -> 选招 -> 释放。"""
import sys, time
import log, struct
sys.path.insert(0, "/root/workspace")
from state import rd, in_battle, turn_state, menu_kind, probe_menu, snapshot
import action
import decision
import info
from ra import press
from bdata import my_mon, enemy_info, MOVES

from addresses import MOVE_CURSOR


def advance_b(timeout=20):
    """有对话框就按 B 跳过，直到主菜单（E82=1）。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if in_battle() is False:
            return "end"
        if turn_state() == 1:
            return "main"
        press("b", 0.3)
        time.sleep(0.6)
    return "stuck"


def move_to(target):
    for _ in range(8):
        d = rd(MOVE_CURSOR, 1)
        if not d:
            return False
        cur = d[0]
        if cur == target:
            return True
        cr, cc = cur // 2, cur % 2
        tr, tc = target // 2, target % 2
        if cc != tc:
            press("right" if tc > cc else "left", 0.2); time.sleep(0.35)
        elif cr != tr:
            press("down" if tr > cr else "up", 0.2); time.sleep(0.35)
    return False


_order = None   # 战斗内部队伍顺序（纯内存，不落盘）
_field = {"t": 0.0, "sp": None, "slot": None}   # 场上 species 缓存
_switch_blocked = False   # 换人被拒（束缚等），本场不再尝试


def switch_blocked():
    return _switch_blocked


def reset_switch_blocked():
    global _switch_blocked
    _switch_blocked = False


def reset_party_order():
    """新战斗开始时调用：清掉上一场的顺序和换人被拒标记。"""
    global _order, _switch_blocked
    _order = None
    _field.update({"t": 0.0, "sp": None, "slot": None})
    _switch_blocked = False


def _init_active():
    """新进程初始化场上槽位：优先读内存里的场上 species（主菜单时可靠）。"""
    try:
        s = snapshot()
        if s["turn"] == 1 and menu_kind() == "main":
            d = rd(0x020244DE, 2)
            sp = struct.unpack("<H", d)[0] if d and len(d) == 2 else None
            if sp:
                for i in range(6):
                    m = my_mon(i)
                    if m and m["species"] == sp:
                        return i
    except Exception:
        pass
    for i in range(6):
        m = my_mon(i)
        if m and m["hp"] > 0:
            return i
    return None


def _raw_order():
    """纯内存的界面顺序（不校验内存），首次访问按队伍初始化。"""
    global _order
    if _order is None:
        active = _init_active()
        if active is None:
            active = next((i for i in range(6)
                           if (my_mon(i) or {}).get("hp", 0) > 0), 0)
        _order = [active] + [i for i in range(6) if i != active]
    return _order


def _set_active(slot):
    order = _raw_order()
    if order[0] != slot:
        order.remove(slot)
        order.insert(0, slot)


def _read_field_species(ttl=0.6):
    """场内 species（0x02023BE4+0），带短缓存；读不到返回 None。"""
    global _field
    now = time.time()
    if ttl > 0 and now - _field["t"] < ttl:
        return _field["sp"]
    from addresses import MY_BATTLE
    d = rd(MY_BATTLE, 2)
    sp = struct.unpack("<H", d)[0] if len(d) == 2 and any(d) else None
    if sp != _field["sp"]:
        _field["slot"] = None
    _field["sp"] = sp
    _field["t"] = now
    return sp


def _slot_for_species(sp):
    """species -> 队伍槽位；同种多只时取界面顺序里最靠前的那只。"""
    if _field.get("sp") == sp and _field.get("slot") is not None:
        return _field["slot"]
    slot = None
    for i in _raw_order():
        m = my_mon(i)
        if m and m.get("species") == sp:
            slot = i
            break
    _field["slot"] = slot
    return slot


def invalidate_field():
    """换人/开战后调用：让下一次 active_slot 强制重读内存。"""
    _field["t"] = 0.0


def party_order():
    """界面顺序：order[0] = 当前出场，order[1..5] = 右侧 5 只。

    不再纯靠进程内跟踪：每次调用都用场上 species 校正 order[0]（0.6s 缓存），
    濒死换人、强制换人等任何漏更新的路径都会被这里修正。
    右侧顺序仍靠进程内维护（战斗队伍数组是加密的，读不到明文）。
    """
    active_slot()
    return _raw_order()


def active_slot():
    """当前场上槽位：以内存 species 为唯一依据，order 只做兜底。"""
    if not in_battle():
        return _raw_order()[0]
    sp = _read_field_species()
    if sp:
        slot = _slot_for_species(sp)
        if slot is not None:
            _set_active(slot)
            return slot
    return _raw_order()[0]


def ensure_active():
    """强制重读场上 species 并校正 order[0]（换人后调用）。"""
    sp = _read_field_species(ttl=0)
    if not sp:
        return None
    slot = _slot_for_species(sp)
    if slot is not None:
        _set_active(slot)
    return slot


def _cursor_for_slot(slot):
    """队伍槽位 -> 菜单光标（order 下标）。"""
    order = _raw_order()
    return order.index(slot) if slot in order else None


def _field_slot_any():
    """队伍列表左侧那只（已倒下的也算）——用于强制换人时的基准。"""
    d = rd(0x020244DE, 2)
    sp = struct.unpack("<H", d)[0] if d and len(d) == 2 else None
    if not sp:
        return None
    for i in range(6):
        m = my_mon(i)
        if m and m["species"] == sp:
            return i
    return None


def _move_party_cursor(slot):
    """把光标移到「队伍槽位 slot」对应的菜单位置。单步走，每步读光标。"""
    target = _cursor_for_slot(slot)
    if target is None:
        return False
    for _ in range(12):
        d = rd(0x0203B0A9, 1)
        if not d:
            return False
        if d[0] == target:
            return True
        press("down" if target > d[0] else "up", 0.08)
        time.sleep(0.28)
    return False


def _move_main_cursor(target):
    """主菜单是 2x2：0 战斗 1 背包 / 2 宝可梦 3 逃跑。"""
    for _ in range(8):
        d = rd(0x02023FF8, 1)
        if not d:
            return False
        cur = d[0]
        if cur == target:
            return True
        cr, cc = cur // 2, cur % 2
        tr, tc = target // 2, target % 2
        if cc != tc:
            press("right" if tc > cc else "left", 0.08)
        else:
            press("down" if tr > cr else "up", 0.08)
        time.sleep(0.28)
    return False


# 按键/光标动作统一走 action 层（这里只保留兼容别名）
_move_party_cursor = action.move_party_cursor
_move_main_cursor = action.move_main_cursor


def _pick_and_switch(target, verbose, label):
    """决策出目标槽位 -> 交给 action 执行换人 -> 成功后更新战斗内部顺序。"""
    pos = _cursor_for_slot(target)      # 必须在点选前算好（点选后顺序还没换）
    if pos is None:
        return False
    ok = action.pick_and_switch(pos)
    if not ok:
        # 换人被拒（束缚类招式等）：标记本场不再尝试，并关掉残留对话
        global _switch_blocked
        _switch_blocked = True
        if verbose:
            print(f"  {label}: 换人被拒（可能被束缚），本场不再换人", flush=True)
        from state import in_dialog
        for _ in range(3):
            if not in_dialog():
                break
            action.tap_a()
            time.sleep(0.6)
    if ok:
        # 换人 = 左边那只与选中的交换位置（战斗内部顺序），战斗结束才重置
        o = _raw_order()
        if 0 <= pos < len(o):
            o[0], o[pos] = o[pos], o[0]
        invalidate_field()
    log.info("switch", label, target=target, pos=pos, ok=ok)
    if verbose:
        print(f"  {label} {'-> #' + str(target) if ok else '失败'}", flush=True)
    return ok


def switch_from_main(target, verbose=True, label="换首发"):
    """战斗主菜单 -> 打开宝可梦 -> 选中 target 槽位换上场。"""
    if not action.open_party_menu():
        log.error("switch", "open_menu_fail", target=target)
        return False
    # 实测：选「宝可梦」后直接是「替换/概况/取消」界面，状态判定为 party_option
    action.wait_until(lambda: info.scene() in (info.PARTY, info.PARTY_OPTION), 2.0)
    if info.scene() not in (info.PARTY, info.PARTY_OPTION):
        if verbose:
            print("  换首发: 没进队伍菜单", flush=True)
        return False
    # 实测：选项界面方向键仍能移动队伍光标，直接选目标即可（按 B 反而会退出整个菜单）
    return _pick_and_switch(target, verbose, label)


def handle_force_switch(verbose=True):
    """强制换人：按克制/等级策略选择。"""
    e = enemy_info()
    party = [my_mon(i) for i in range(6)]
    target = decision.choose_switch(party, e)
    if target is None:
        return None
    # 强制换人：游戏已经按队伍顺序派了下一只，这里只是把目标换上来
    if not _pick_and_switch(target, verbose, "强制换人"):
        return None
    time.sleep(0.8)
    got = active_slot()
    if got is not None and got != target and verbose:
        print(f"  警告: 期望 #{target} 上场，实际 #{got}", flush=True)
    return target


def do_switch(target=None, verbose=True):
    """从战斗主菜单手动换人；target 为空时按克制/等级策略选。"""
    if target is None:
        e = enemy_info()
        party = [my_mon(i) for i in range(6)]
        target = decision.choose_switch(party, e)
    if target is None:
        return False
    if menu_kind() != "party":
        if not action.move_main_cursor(2):
            return False
        action.tap_a()
        time.sleep(1.0)                        # 进入队伍
    if not _pick_and_switch(target, verbose, "手动换人"):
        return False
    return True


