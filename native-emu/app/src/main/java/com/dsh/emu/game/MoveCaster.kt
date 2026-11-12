package com.dsh.emu.game

/**
 * 招式菜单「点击施放」的纯逻辑。
 *
 * 前提（主持拍板）：招式菜单已展开——`TURN_FLAG==2` 且 `MAIN_CURSOR==0`；
 * 不做「主菜单→自动打开招式菜单」。点击 2×2 招式格（0 左上 / 1 右上 / 2 左下 / 3 右下）后：
 * fail-closed 守卫 → 逐格短按方向（每步回读）→ 二次确认光标==目标 → 按 A → 等回合推进。
 *
 * 内存读取与按键全部通过 [Io] 注入：线上由 `ui/BattleMoveAction` 接 JNI，
 * 单测用假实现（不加载 native 库、不碰实机）。
 *
 * 失败即停：任何守卫不满足 / 光标没到位 / 按 A 后回合没推进 → 返回失败，不补按、不重试。
 */
object MoveCaster {

    /** 2×2 招式格上的方向。 */
    enum class Dir { UP, DOWN, LEFT, RIGHT }

    /** 失败原因（写进 Nlog / statusText 的 reason）。 */
    enum class Reason {
        OK,
        BAD_TARGET,        // 目标不在 0..3
        TURN_NOT_MOVES,    // TURN_FLAG != 2（不在招式菜单）
        MAIN_NOT_MOVES,    // MAIN_CURSOR != 0（子菜单不是招式）
        CURSOR_UNSTABLE,   // 起始光标读不到 / 越界
        CURSOR_MOVE_FAIL,  // MAX_STEPS 步内没走到目标
        CURSOR_MISMATCH,   // 二次回读 != 目标
        TURN_READ_FAIL,    // 按 A 后 TURN_FLAG 读不到
        TURN_NOT_CHANGED,  // 按 A 后 TURN_FLAG 仍 == 2
        CANCELLED,         // 代际取消（切页/开按键面板/载 ROM）
    }

    data class Result(
        val ok: Boolean,
        val reason: Reason,
        val index: Int,
        val turnBefore: Int,
        val turnAfter: Int,
        val cursorStart: Int,
        val cursorEnd: Int,
        val steps: Int,
        val elapsedMs: Long,
    )

    /** 注入接口：线上接 JNI，单测接假实现。全部同步调用。 */
    interface Io {
        /** TURN_FLAG：1=主菜单 2=招式 4=动画 0=开场；读不到返回 -1。 */
        fun readTurn(): Int

        /** MAIN_CURSOR：子菜单里保留「从主菜单哪个选项打开」，0=招式。读不到返回 -1。 */
        fun readMainCursor(): Int

        /** MOVE_CURSOR：0..3；读不到返回 -1。 */
        fun readMoveCursor(): Int

        /** 按住方向键 ms 毫秒（实现必须保证最终松开）。 */
        fun pressDir(dir: Dir, ms: Long)

        /** 按住 A ms 毫秒（实现必须保证最终松开）。 */
        fun pressA(ms: Long)

        fun sleep(ms: Long)

        /** 已被取消：返回 true 后本轮不再按键。 */
        fun cancelled(): Boolean
    }

    const val TURN_MOVES_MENU = 2
    const val MAIN_CURSOR_MOVES = 0
    const val STEP_MS = 80L          // 菜单按住会连发（0.3s 能跳 2 格），必须短按
    const val SETTLE_MS = 280L       // 每步后等光标稳定
    const val CONFIRM_MS = 120L      // 二次确认前的额外等待
    const val A_MS = 300L            // A 键至少 250ms 游戏才识别
    const val POLL_MS = 150L
    const val POLL_TIMES = 8         // 最多 ~1.2s 等回合推进
    const val MAX_STEPS = 8

    /**
     * 从 [from] 走到 [to] 的下一步方向（与 Python action.move_move_cursor 一致：
     * 先横向对齐列，再纵向对齐行）。越界或已到位返回 null。
     */
    fun nextDirection(from: Int, to: Int): Dir? {
        if (from !in 0..3 || to !in 0..3 || from == to) return null
        val fr = from / 2
        val fc = from % 2
        val tr = to / 2
        val tc = to % 2
        return if (fc != tc) {
            if (tc > fc) Dir.RIGHT else Dir.LEFT
        } else {
            if (tr > fr) Dir.DOWN else Dir.UP
        }
    }

    /** 点击第 [target] 个招式（0..3）。 */
    fun cast(target: Int, io: Io): Result {
        val t0 = System.nanoTime()
        var turnBefore = -1
        var cursorStart = -1
        var cursorEnd = -1
        var steps = 0

        fun result(ok: Boolean, reason: Reason, turnAfter: Int = -1): Result = Result(
            ok = ok, reason = reason, index = target,
            turnBefore = turnBefore, turnAfter = turnAfter,
            cursorStart = cursorStart, cursorEnd = cursorEnd,
            steps = steps, elapsedMs = (System.nanoTime() - t0) / 1_000_000,
        )

        if (target !in 0..3) return result(false, Reason.BAD_TARGET)

        // 守卫 1：招式菜单已展开（TURN_FLAG==2，MAIN_CURSOR==0）——不满足则一个键都不按。
        turnBefore = io.readTurn()
        if (turnBefore != TURN_MOVES_MENU) return result(false, Reason.TURN_NOT_MOVES)
        if (io.readMainCursor() != MAIN_CURSOR_MOVES) return result(false, Reason.MAIN_NOT_MOVES)

        // 守卫 2：起始光标必须可读且在 2×2 范围内。
        var cur = io.readMoveCursor()
        cursorStart = cur
        cursorEnd = cur
        if (cur !in 0..3) return result(false, Reason.CURSOR_UNSTABLE)

        // 逐格移动：每按一下都回读，绝不用预计算序列盲按（菜单按住会连发）。
        while (cur != target && steps < MAX_STEPS) {
            if (io.cancelled()) return result(false, Reason.CANCELLED)
            val dir = nextDirection(cur, target) ?: return result(false, Reason.CURSOR_MOVE_FAIL)
            io.pressDir(dir, STEP_MS)
            steps++
            io.sleep(SETTLE_MS)
            if (io.cancelled()) return result(false, Reason.CANCELLED)
            cur = io.readMoveCursor()
            cursorEnd = cur
            if (cur !in 0..3) return result(false, Reason.CURSOR_MOVE_FAIL)
        }
        if (cur != target) return result(false, Reason.CURSOR_MOVE_FAIL)

        // 守卫 3：二次确认——稳定一段时间后再读，必须仍是目标。
        io.sleep(CONFIRM_MS)
        if (io.cancelled()) return result(false, Reason.CANCELLED)
        cur = io.readMoveCursor()
        cursorEnd = cur
        if (cur != target) return result(false, Reason.CURSOR_MISMATCH)

        // 执行前最后一次确认：窗口内可能被对话框/动画顶掉，任一不满足就不按 A。
        turnBefore = io.readTurn()
        if (turnBefore != TURN_MOVES_MENU) return result(false, Reason.TURN_NOT_MOVES)
        if (io.readMainCursor() != MAIN_CURSOR_MOVES) return result(false, Reason.MAIN_NOT_MOVES)
        if (io.cancelled()) return result(false, Reason.CANCELLED)

        // 执行：按 A 选招，再等 TURN_FLAG 离开 2（进入动画/结算）。
        io.pressA(A_MS)
        var turnAfter = io.readTurn()
        if (turnAfter == -1) return result(false, Reason.TURN_READ_FAIL, turnAfter)
        if (turnAfter != TURN_MOVES_MENU) return result(true, Reason.OK, turnAfter)
        repeat(POLL_TIMES) {
            io.sleep(POLL_MS)
            val t = io.readTurn()
            if (t == -1) return result(false, Reason.TURN_READ_FAIL, t)
            turnAfter = t
            if (t != TURN_MOVES_MENU) return result(true, Reason.OK, t)
        }
        return result(false, Reason.TURN_NOT_CHANGED, turnAfter)
    }
}
