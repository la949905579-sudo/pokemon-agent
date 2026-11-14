"""执行层：只执行动作（按键、光标移动）。

约束：
  - 不判断场景、不做策略（那些在 info / decision 层）
  - 每个动作尽量「按一次 → 读一次状态」，不盲按
"""
import sys, time
sys.path.insert(0, "/root/workspace")
from ra import press, send
from state import rd, snapshot
from addresses import PARTY_CURSOR, MAIN_CURSOR, MOVE_CURSOR
import log


def tap_a():
    press("a", 0.25)


def tap_b():
    press("b", 0.25)


def read_cursor(addr):
    d = rd(addr, 1)
    return d[0] if d else None


def move_cursor_to(target, addr=PARTY_CURSOR, max_steps=12, settle=0.28):
    """把光标移到 target：每次只走一步，走完读光标。"""
    for _ in range(max_steps):
        cur = read_cursor(addr)
        if cur is None:
            return False
        if cur == target:
            return True
        press("down" if target > cur else "up", 0.08)
        time.sleep(settle)
    return False


def move_party_cursor(target):
    """队伍/换人菜单光标（0-5）。"""
    return move_cursor_to(target, PARTY_CURSOR)


def move_main_cursor(target):
    """战斗主菜单 2x2：0 战斗 1 背包 / 2 宝可梦 3 逃跑。"""
    for _ in range(8):
        cur = read_cursor(MAIN_CURSOR)
        if cur is None:
            return False
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


def wait_until(pred, timeout=4.0, step=0.25):
    """轮询直到 pred() 成立或超时。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if pred():
            return True
        time.sleep(step)
    return False


def pick_and_switch(target_pos):
    """光标移到 target_pos -> A 选中 -> A 替换，每一步都验证。

    返回 True 表示检测到换人动画（turn==4），此时才算真的换上了。
    验证失败立即返回 False，不再盲按（避免按错菜单项）。
    """
    from state import party_cursor

    # 1) 移动光标，验证到位
    if not move_party_cursor(target_pos):
        return False
    if party_cursor() != target_pos:
        return False

    # 2) 按 A 选中（出现「替换/概况/取消」），再按 A 替换
    tap_a()
    time.sleep(0.4)

    # 3) 验证换人动画开始
    tap_a()
    ok = wait_until(lambda: snapshot()["turn"] == 4, 1.5)
    if not ok:
        # 再试一次（选项可能刚好没开）
        tap_a()
        ok = wait_until(lambda: snapshot()["turn"] == 4, 1.5)

    # 4) 等动画结束 / 回到可操作
    wait_until(lambda: snapshot()["turn"] == 1 or not snapshot()["battle"], 6.0)
    return ok


def close_menu(max_tries=3):
    """按 B 退出菜单，直到回到战斗主菜单。"""
    from state import menu_kind
    for _ in range(max_tries):
        if menu_kind() == "main":
            return True
        tap_b()
        time.sleep(0.7)
    return menu_kind() == "main"


# ---------------- 战斗动作 ----------------
# 招式菜单 2x2：0 左上 1 右上 2 左下 3 右下
DELTA = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def move_move_cursor(index):
    """招式菜单光标（2x2）。"""
    for _ in range(8):
        cur = read_cursor(MOVE_CURSOR)
        if cur is None:
            return False
        if cur == index:
            return True
        cr, cc = cur // 2, cur % 2
        tr, tc = index // 2, index % 2
        if cc != tc:
            press("right" if tc > cc else "left", 0.08)
        else:
            press("down" if tr > cr else "up", 0.08)
        time.sleep(0.28)
    return False


def open_move_menu():
    """战斗主菜单 -> 战斗 -> 招式菜单。"""
    if not move_main_cursor(0):
        return False
    tap_a()
    return wait_until(lambda: snapshot()["turn"] == 2, 2.0)


def use_move(index, max_retries=3):
    """选中第 index 个招式并出招（带重试）。

    返回 True 表示「回合确实推进了」（turn 从 2 变化），而不是只按了键。
    可靠性措施：
      1. 移动光标后二次确认（光标有滞后帧）
      2. 未到位 -> 重新移动（最多 max_retries 轮）
      3. 按 A 后等 turn 变化，超时则重按一次
    """
    for attempt in range(max_retries):
        if not move_move_cursor(index):
            log.error("action", "cursor_move_fail", idx=index, attempt=attempt)
            continue
        # 二次确认
        time.sleep(0.1)
        cur = read_cursor(MOVE_CURSOR)
        if cur != index:
            log.error("action", "cursor_mismatch", want=index, got=cur, attempt=attempt)
            continue
        before = snapshot()["turn"]
        log.info("action", "use_move", idx=index, cursor=cur, turn=before, attempt=attempt)
        tap_a()
        # 等 turn 变化（最多约 1.2s）
        for _ in range(8):
            time.sleep(0.15)
            t = snapshot()["turn"]
            if t != before:
                log.info("action", "use_move_ok", idx=index, turn=t)
                return True
        # 超时：不盲按 A（菜单可能不对，按 A 会误选）——记录后交给上层重新判断场景
        cur_turn = snapshot()["turn"]
        log.error("action", "use_move_timeout", idx=index,
                  before=before, now=cur_turn, attempt=attempt)
        return False
    return False


def choose_option(index):
    """选项菜单选第 index 项（0 起）：是/否、放出/概况/取消。

    没有找到选项光标地址，用「先 UP 到顶，再 DOWN index 次」定位；
    会多按几次 UP，但不会改变结果。
    """
    for _ in range(4):
        press("up", 0.08)
        time.sleep(0.12)
    for _ in range(index):
        press("down", 0.08)
        time.sleep(0.12)
    tap_a()
    return True


def advance_dialog(times=1):
    """按 A 推进对话。"""
    for _ in range(times):
        tap_a()
        time.sleep(0.2)


def run_away():
    """逃跑：主菜单光标移到 3 按 A。"""
    if not move_main_cursor(3):
        return False
    tap_a()
    return True


def open_party_menu():
    """战斗主菜单 -> 宝可梦（进入队伍/换人界面）。"""
    if not move_main_cursor(2):
        return False
    tap_a()
    time.sleep(0.8)
    return True


# ---------------- 地图动作 ----------------

def turn(direction):
    """只转身，不走格（0.06 秒实测只转身）。"""
    press(direction, 0.06)
    time.sleep(0.15)


STEP_TIME = 0.12      # 每格按住时长（按住 B 跑步，2026-11-09 标定）
BASE_TIME = 0.06      # 第一格的额外延迟（实测）


def walk(direction, steps):
    """按「时长驱动」移动：一次长按 base + step*n，再按坐标微调。

    实测：0.09s->1 格、0.18->1 格、0.27->2 格、0.36->3 格，
    近似 0.06 + 0.09*n。长按后会读坐标，少了补按、多了反向退。
    """
    s0 = snapshot()
    start = (s0["x"], s0["y"]) if s0["x"] is not None else None
    dx, dy = DELTA[direction]
    back = {"up": "down", "down": "up", "left": "right", "right": "left"}[direction]

    # 短距离（<=2 格）不跑步：跑步速度太快、时长难控，容易走过头再往回补，导致左右横移
    use_run = steps > 2
    if use_run:
        send(0, 1)                   # 按住 B：跑步（实测快 50%）
        time.sleep(0.05)
    press(direction, BASE_TIME + STEP_TIME * steps)
    if use_run:
        send(0, 0)                   # 松开 B
    time.sleep(0.18)
    s = snapshot()
    if start and s["x"] is not None:
        moved = (s["x"] - start[0]) * dx + (s["y"] - start[1]) * dy
    else:
        moved = steps

    # 微调：走少了补按；走多了只退一次，退过头就放弃（避免左右来回振荡）
    stall = 0
    reversed_once = False
    for _ in range(2):
        if moved == steps:
            break
        if s["battle"] or s["dialog"]:
            break
        prev = moved
        if moved > steps:
            if reversed_once:        # 已经反退过一次，不再振荡
                break
            reversed_once = True
            press(back, STEP_TIME)
        else:
            if reversed_once:        # 刚反退过又变少，说明在来回晃，放弃
                break
            press(direction, STEP_TIME)
        time.sleep(0.12)
        s = snapshot()
        if start and s["x"] is not None:
            moved = (s["x"] - start[0]) * dx + (s["y"] - start[1]) * dy
        else:
            moved += 1 if moved < steps else -1
        stall = stall + 1 if moved == prev else 0
        if stall >= 1:
            break
    log.debug("action", "walk", dir=direction, want=steps, got=min(moved, steps))
    return max(0, min(moved, steps))
