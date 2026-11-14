"""实时读游戏状态：角色坐标 + 队伍。
用法:
  python3 state.py          # 坐标 + 队伍（约 1 秒）
  python3 state.py pos      # 只读坐标（几十毫秒）
"""
from memory import rd
from addresses import *  # noqa
import socket, struct, sys, time

HOST, PORT = "127.0.0.1", 55355
X_ADDR, Y_ADDR = 0x02036e48, 0x02036e4a

def coords():
    d = rd(X_ADDR, 4)
    if len(d) < 4:
        return None
    return struct.unpack_from("<hh", d, 0)

TILE_OFF = 7   # 地块坐标 = 原始坐标 - 7（对外一律用「地块」）


def to_tile(raw):
    """原始坐标 -> 地块坐标。"""
    return (raw[0] - TILE_OFF, raw[1] - TILE_OFF)


def to_raw(tile):
    """地块坐标 -> 原始坐标。"""
    return (tile[0] + TILE_OFF, tile[1] + TILE_OFF)


PARTY_RANGE = (0x24000, 0x28000)   # PARTY_ADDR 从 addresses.py 取（唯一真源）

def find_party(buf):
    """返回 (offset, [(lv,hp,maxhp)...]) 或 (None, [])。
    特征：6只、等级1-100、hp<=maxhp<=999、PID 非零且互不相同，且地址落在已知区间。"""
    lo, hi = PARTY_RANGE
    for off in range(lo, min(hi, len(buf) - 601), 2):
        pids = set(); lvs = []
        ok = True
        for i in range(6):
            o = off + i * 100
            lv = buf[o + 0x54]
            hp, mhp = struct.unpack_from("<HH", buf, o + 0x56)
            pid = struct.unpack_from("<I", buf, o)[0]
            if not (1 <= lv <= 100 and 1 <= hp <= mhp <= 999 and pid != 0) or pid in pids:
                ok = False; break
            pids.add(pid); lvs.append((lv, hp, mhp))
        if ok:
            return off, lvs
    return None, []

def _read_party_at(addr):
    d = rd(addr, 600)
    if len(d) < 600:
        return None
    out = []
    for i in range(6):
        o = i * 100
        lv = d[o + 0x54]
        hp, mhp = struct.unpack_from("<HH", d, o + 0x56)
        pid = struct.unpack_from("<I", d, o)[0]
        if not (1 <= lv <= 100 and 0 <= hp <= mhp <= 999 and pid != 0):
            return None
        out.append((lv, hp, mhp))
    return out

def party():
    fixed = _read_party_at(PARTY_ADDR)
    if fixed:
        return PARTY_ADDR, fixed
    buf = bytearray()
    for a in range(0x02000000, 0x02040000, 4096):
        d = rd(a, 4096)
        buf.extend(d if len(d) == 4096 else b"\0" * 4096)
    off, lvs = find_party(buf)
    return off, lvs

BATTLE_FLAG = 0x02024018
DIALOG_FLAG = 0x03000F9C

def in_dialog():
    """对话框打开时为 1，关闭时为 0。"""
    d = rd(DIALOG_FLAG, 1)
    if not d:
        return None
    return d[0] != 0

def in_battle():
    """战斗初始化时这块缓冲区会被写非零；战斗结束回零。

    读不到时重试一次，仍读不到返回 None（调用方应把 None 当作「未知」，
    不能当成「战斗结束」）。
    """
    for _ in range(2):
        d = rd(BATTLE_FLAG, 1)
        if d:
            return d[0] != 0
        time.sleep(0.03)
    return None

if __name__ == "__main__":
    x = coords()
    if not x:
        print("读不到：模拟器可能不在前台")
        sys.exit(1)
    print(f"位置  x={x[0]}  y={x[1]}")
    print(f"战斗  {'是' if in_battle() else '否'}")
    print(f"对话框 {'是' if in_dialog() else '否'}")

    if len(sys.argv) > 1 and sys.argv[1] == "pos":
        sys.exit(0)
    off, mons = party()
    if not mons:
        print("队伍：没扫到")
    else:
        print(f"队伍 (offset {off:#x})")
        for i, (lv, hp, mhp) in enumerate(mons, 1):
            print(f"  #{i}  Lv{lv:<3d} HP {hp:3d}/{mhp}")

TURN_FLAG = 0x02023E82   # 1=主菜单(玩家输入) 2=招式菜单 4=事件/动画 0=开场消息

def turn_state():
    d = rd(TURN_FLAG, 1)
    return d[0] if d else None

def wait_turn(timeout=12, poll=0.15):
    """等到主菜单出现（玩家回合）。返回 True 表示现在可以安全按键。"""
    import time as _t
    t0 = _t.time()
    while _t.time() - t0 < timeout:
        if turn_state() == 1:
            return True
        _t.sleep(poll)
    return False

PARTY_MENU_FLAG = 0x03000928   # 队伍/换人菜单打开时非零，招式菜单时为 0

def party_menu_open():
    d = rd(PARTY_MENU_FLAG, 4)
    if not d:
        return None
    return struct.unpack("<I", d)[0] != 0

BAG_CURSOR = 0x0203AD08     # 背包菜单：道具光标（0=第一件道具，依次往下）

def bag_cursor():
    d = rd(BAG_CURSOR, 1)
    return d[0] if d else None

def menu_kind():
    """返回 map / main / moves / party / bag / anim / start / unknown。"""
    if in_battle() is False:
        return "map"
    st = turn_state()
    if st == 1:
        # 只看 B0A9 不行：主菜单时它还残留着上次队伍光标（实测 =1），会误判成换人界面。
        # 队伍列表一定是从主菜单"宝可梦"(2) 进入的，此时 FF8 保留 2。
        b = rd(PARTY_CURSOR, 1)
        mc = rd(MAIN_CURSOR, 1)
        if b is not None and mc is not None and b[0] <= 5 and mc[0] == 2:
            return "party"
        return "main"
    if st == 2:
        # 子菜单里 0x02023FF8 保留着"从主菜单哪个选项打开"的值
        mc = rd(MAIN_CURSOR, 1)
        mc = mc[0] if mc else None
        if mc == 0:
            return "moves"
        if mc == 1:
            return "bag"
        if mc == 2:
            return "party"
        return "submenu"
    if st == 4:
        # 濒死/强制换人时游戏也是 turn=4，但会弹出队伍列表（有光标）
        b = rd(PARTY_CURSOR, 1)
        if b is not None and b[0] <= 5:
            return "party"
        return "anim"
    if st == 0:
        return "start"
    return f"unknown({st})"

def probe_menu(tries=2):
    """用方向键试探当前菜单：主菜单会动 FF8，队伍列表会动 B0A9。

    强制换人时 FF8=0，和主菜单读数完全一样，只能按一下看谁在动。
    试探后按反方向还原，不改变选择。
    """
    import time
    from ra import press
    for d, back in (("right", "left"), ("down", "up")):
        for _ in range(tries):
            f0 = rd(MAIN_CURSOR, 1)
            b0 = rd(PARTY_CURSOR, 1)
            if not f0 or not b0:
                break
            press(d, 0.08)
            time.sleep(0.22)
            f1 = rd(MAIN_CURSOR, 1)
            b1 = rd(PARTY_CURSOR, 1)
            press(back, 0.08)
            time.sleep(0.22)
            if f1 is not None and f1 != f0:
                return "main"
            if b1 is not None and b1 != b0:
                return "party"
    return "unknown"


MAIN_CURSOR = 0x02023FF8   # 主菜单：0=战斗 1=背包 2=宝可梦 3=逃跑
MOVE_CURSOR = 0x02023FFC   # 招式菜单：0=左上 1=右上 2=左下 3=右下

def cursor():
    """当前菜单光标位置；不在菜单时返回 None。"""
    k = menu_kind()
    if k == "main":
        return rd(MAIN_CURSOR, 1)[0]
    if k == "moves":
        return rd(MOVE_CURSOR, 1)[0]
    if k == "party":
        return rd(PARTY_CURSOR, 1)[0]
    if k == "bag":
        return rd(BAG_CURSOR, 1)[0]
    return None

PARTY_CURSOR = 0x0203B0A9   # 队伍/换人菜单：0-5，对应队伍第 1-6 只

def party_cursor():
    """队伍光标（0-5）。战斗换人菜单里 0x03000928 可能为 0，所以不再依赖它，
    直接读光标值并做范围校验。"""
    d = rd(PARTY_CURSOR, 1)
    if not d:
        return None
    v = d[0]
    return v if 0 <= v <= 5 else None

BATTLE_MON0 = 0x02023BE4     # 我方场上宝可梦战斗数据（species 在 +0x00）
BATTLE_MON1 = 0x02023C3C     # 敌方场上宝可梦战斗数据（每只结构 0x58）
STATUS1_OFF = 0x4C           # status1 状态字段（1 字节）

# status1 位定义（Gen3）
ST_SLEEP = 0x07      # 低 3 位 = 剩余睡眠回合
ST_POISON = 0x08
ST_BURN = 0x10
ST_FREEZE = 0x20
ST_PARALYSIS = 0x40
ST_TOXIC = 0x80


def status1(slot=0):
    """战斗状态字段：slot 0=我方场上，1=敌方场上。读不到返回 None。

    会先校验结构的 species 字段：战斗结束后该区域可能残留旧数据，
    species 异常（0 或超大）时返回 None，表示「当前没有可信战斗数据」。
    """
    base = BATTLE_MON0 if slot == 0 else BATTLE_MON1
    d = rd(base, STATUS1_OFF + 1)
    if not d or len(d) < STATUS1_OFF + 1:
        return None
    sp = struct.unpack("<H", d[:2])[0]
    if sp == 0 or sp > 400:      # 无效 species -> 残留数据
        return None
    # 物种校验：必须是我方队伍里任意一只（不依赖 party_order，避免不同步误判）
    if slot == 0:
        try:
            from bdata_shared import party_species
            if sp not in party_species(rd, PARTY_ADDR):
                return None
        except Exception:
            pass
    return d[STATUS1_OFF]


def sleep_turns(slot=0):
    """睡眠剩余回合（0=没睡，None=读不到）。"""
    s = status1(slot)
    return (s & ST_SLEEP) if s is not None else None


TRAPPED_OFF = 0x22           # 束缚标志（+0x22 bit 8 = 0x100 置位表示被束缚）


def trapped():
    """我方场上是否被束缚（无法换人/无法逃跑）。

    实测：无束缚时 +0x22 = 3，束缚中 = 258(0x102)。
    只在战斗内有效（战斗外是残留数据）。
    """
    if in_battle() is False:
        return False
    d = rd(BATTLE_MON0 + TRAPPED_OFF, 2)
    if not d or len(d) < 2:
        return False
    v = struct.unpack("<H", d)[0]
    # 只有 bit8 是实测可靠的束缚（Wrap 类，258 = 0x102）。
    # bit2/3 曾被当成「被困」，但实测 +0x22=1037（含 0x0D）时换人正常，
    # 是误判；真被拒时由 switch 的失败兜底（_switch_blocked）处理。
    return bool(v & 0x100)


def status_flags(slot=0):
    """解析状态：返回 {sleep, poison, burn, freeze, paralysis, toxic}。"""
    s = status1(slot)
    if s is None:
        return None
    return {
        "sleep": s & ST_SLEEP,
        "poison": bool(s & ST_POISON),
        "burn": bool(s & ST_BURN),
        "freeze": bool(s & ST_FREEZE),
        "paralysis": bool(s & ST_PARALYSIS),
        "toxic": bool(s & ST_TOXIC),
    }


FACING_ADDR = 0x02036E38 + 0x18   # 玩家对象 +0x18 低字节

def player_facing():
    """返回 up/down/left/right，读不到返回 None。"""
    d = rd(FACING_ADDR, 1)
    if not d:
        return None
    return {0x11: "down", 0x22: "up", 0x33: "left", 0x44: "right"}.get(d[0])


def snapshot():
    """轻量状态快照：只读 4 处内存（约 40-80ms）。

    返回 dict：
      mode:   map / battle / battle_dialog
      battle: 是否在战斗中
      dialog: 是否有对话框（含 NPC 对话）
      turn:   E82 回合状态（战斗内用）
      x, y:   地图坐标（战斗中也保留，地图外为 None）

    用途：放在所有动作之前做守卫，不必再分别调用 coords/in_battle/in_dialog。
    """
    raw_b = rd(BATTLE_FLAG, 1)
    raw_d = rd(DIALOG_FLAG, 1)
    raw_t = rd(TURN_FLAG, 2)      # E82 = 回合状态，E83 = 是否弹出「是/否」选项框
    raw_p = rd(X_ADDR, 4)
    battle = bool(raw_b and raw_b[0])
    dialog = bool(raw_d and raw_d[0] == 1)
    turn = raw_t[0] if raw_t else None
    # 选项框（如濒死时「要使用下一只宝可梦吗？」是/否）：E82=1 且 E83=0；主菜单时 E83=1
    choice = bool(battle and turn == 1 and raw_t and len(raw_t) > 1 and raw_t[1] == 0)
    if raw_p and len(raw_p) == 4:
        x, y = struct.unpack_from("<hh", raw_p, 0)
    else:
        x = y = None
    if not battle:
        mode = "map"
    elif choice:
        mode = "choice"
    else:
        mode = "battle_dialog" if dialog else "battle"
    return {"mode": mode, "battle": battle, "dialog": dialog,
            "choice": choice, "turn": turn, "x": x, "y": y}
