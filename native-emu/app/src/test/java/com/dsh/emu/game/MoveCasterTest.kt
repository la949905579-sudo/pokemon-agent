package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * MoveCaster 离线单测：全部用假 Io，不加载 native 库、不碰实机。
 *
 * 覆盖：3 条 fail-closed 拒绝路径（TURN_FLAG / MAIN_CURSOR / 二次回读）、
 * 成功路径（已到位只按 A / 需要移动的序列）、按 A 后未推进即停、取消、越界。
 */
class MoveCasterTest {

    /** 假游戏：方向键按 2×2 规则移动光标；A 键按下后回合推进到 [turnAfterA]。 */
    private class FakeIo(
        var turn: Int = 2,
        var main: Int = 0,
        var cursor: Int = 0,
        var moveOnPress: Boolean = true,
        var changeTurnOnA: Boolean = true,
        var turnAfterA: Int = 4,
        var turnReadFailAfterA: Boolean = false,
        var wrongConfirm: Boolean = false,
        var cancelledNow: Boolean = false,
    ) : MoveCaster.Io {
        val dirs = mutableListOf<MoveCaster.Dir>()
        var aPresses = 0

        /** sleep(CONFIRM_MS) 之后第一次读光标故意读错，模拟二次确认时滞后/不一致。 */
        private var wrongNextRead = false

        override fun readTurn(): Int {
            if (turnReadFailAfterA && aPresses > 0) return -1
            return turn
        }

        override fun readMainCursor(): Int = main

        override fun readMoveCursor(): Int {
            if (wrongNextRead) {
                wrongNextRead = false
                return (cursor + 1) % 4
            }
            return cursor
        }

        override fun pressDir(dir: MoveCaster.Dir, ms: Long) {
            dirs.add(dir)
            if (!moveOnPress) return
            cursor = when (dir) {
                MoveCaster.Dir.UP -> if (cursor >= 2) cursor - 2 else cursor
                MoveCaster.Dir.DOWN -> if (cursor <= 1) cursor + 2 else cursor
                MoveCaster.Dir.LEFT -> if (cursor % 2 == 1) cursor - 1 else cursor
                MoveCaster.Dir.RIGHT -> if (cursor % 2 == 0) cursor + 1 else cursor
            }
        }

        override fun pressA(ms: Long) {
            aPresses++
            if (changeTurnOnA) turn = turnAfterA
        }

        override fun sleep(ms: Long) {
            if (ms == MoveCaster.CONFIRM_MS && wrongConfirm) wrongNextRead = true
        }

        override fun cancelled(): Boolean = cancelledNow
    }

    private fun assertNoKeys(io: FakeIo) {
        assertTrue("不应按方向键：${io.dirs}", io.dirs.isEmpty())
        assertEquals("不应按 A", 0, io.aPresses)
    }

    // ---------- fail-closed：3 条拒绝路径 ----------

    @Test
    fun rejectsWhenTurnFlagIsNotMovesMenu() {
        val io = FakeIo(turn = 1)   // 主菜单
        val r = MoveCaster.cast(0, io)
        assertFalse(r.ok)
        assertEquals(MoveCaster.Reason.TURN_NOT_MOVES, r.reason)
        assertNoKeys(io)
    }

    @Test
    fun rejectsWhenMainCursorIsNotMoves() {
        val io = FakeIo(turn = 2, main = 2)   // 子菜单是换人
        val r = MoveCaster.cast(0, io)
        assertFalse(r.ok)
        assertEquals(MoveCaster.Reason.MAIN_NOT_MOVES, r.reason)
        assertNoKeys(io)
    }

    @Test
    fun rejectsWhenConfirmReadDiffersFromTarget() {
        val io = FakeIo(cursor = 0, wrongConfirm = true)
        val r = MoveCaster.cast(1, io)
        assertFalse(r.ok)
        assertEquals(MoveCaster.Reason.CURSOR_MISMATCH, r.reason)
        assertEquals(listOf(MoveCaster.Dir.RIGHT), io.dirs)   // 移动过，但绝不按 A
        assertEquals(0, io.aPresses)
    }

    // ---------- 成功路径 ----------

    @Test
    fun successWhenCursorAlreadyOnTarget() {
        val io = FakeIo(cursor = 2)
        val r = MoveCaster.cast(2, io)
        assertTrue(r.ok)
        assertEquals(MoveCaster.Reason.OK, r.reason)
        assertTrue("已经在目标上，不应按方向键", io.dirs.isEmpty())
        assertEquals(1, io.aPresses)
        assertEquals(2, r.turnBefore)
        assertEquals(4, r.turnAfter)
    }

    @Test
    fun successMovesStepByStepThenPressA() {
        val io = FakeIo(cursor = 0)
        val r = MoveCaster.cast(3, io)   // 0 左上 -> 3 右下：先右、再下
        assertTrue(r.ok)
        assertEquals(listOf(MoveCaster.Dir.RIGHT, MoveCaster.Dir.DOWN), io.dirs)
        assertEquals(2, r.steps)
        assertEquals(1, io.aPresses)
        assertEquals(0, r.cursorStart)
        assertEquals(3, r.cursorEnd)
    }

    // ---------- 失败即停 ----------

    @Test
    fun stopsWhenTurnDoesNotChangeAfterA() {
        val io = FakeIo(cursor = 0, changeTurnOnA = false)
        val r = MoveCaster.cast(0, io)
        assertFalse(r.ok)
        assertEquals(MoveCaster.Reason.TURN_NOT_CHANGED, r.reason)
        assertEquals("不盲按第二下 A", 1, io.aPresses)
    }

    @Test
    fun stopsWhenTurnUnreadableAfterA() {
        val io = FakeIo(cursor = 0, turnReadFailAfterA = true)
        val r = MoveCaster.cast(0, io)
        assertFalse(r.ok)
        assertEquals(MoveCaster.Reason.TURN_READ_FAIL, r.reason)
        assertEquals("读不到也不重试", 1, io.aPresses)
    }

    @Test
    fun failsWhenCursorNeverReachesTarget() {
        val io = FakeIo(cursor = 0, moveOnPress = false)
        val r = MoveCaster.cast(1, io)
        assertFalse(r.ok)
        assertEquals(MoveCaster.Reason.CURSOR_MOVE_FAIL, r.reason)
        assertEquals(MoveCaster.MAX_STEPS, io.dirs.size)
        assertEquals(0, io.aPresses)
    }

    @Test
    fun cancelledBeforeA() {
        val io = FakeIo(cursor = 0, cancelledNow = true)
        val r = MoveCaster.cast(0, io)
        assertFalse(r.ok)
        assertEquals(MoveCaster.Reason.CANCELLED, r.reason)
        assertEquals(0, io.aPresses)
    }

    // ---------- 参数/边界 ----------

    @Test
    fun rejectsBadTargetAndUnstableCursor() {
        val badTarget = MoveCaster.cast(4, FakeIo())
        assertEquals(MoveCaster.Reason.BAD_TARGET, badTarget.reason)

        val badCursor = FakeIo(cursor = -1)
        val unstable = MoveCaster.cast(1, badCursor)
        assertEquals(MoveCaster.Reason.CURSOR_UNSTABLE, unstable.reason)
        assertNoKeys(badCursor)
    }

    // ---------- 方向选择（2×2，先列后行，与 Python 版一致） ----------

    @Test
    fun nextDirectionMatchesGrid() {
        assertEquals(MoveCaster.Dir.RIGHT, MoveCaster.nextDirection(0, 3))
        assertEquals(MoveCaster.Dir.LEFT, MoveCaster.nextDirection(1, 2))
        assertEquals(MoveCaster.Dir.LEFT, MoveCaster.nextDirection(3, 0))
        assertEquals(MoveCaster.Dir.UP, MoveCaster.nextDirection(2, 0))
        assertNull(MoveCaster.nextDirection(2, 2))
        assertNull(MoveCaster.nextDirection(-1, 2))
        assertNull(MoveCaster.nextDirection(4, 1))
    }
}
