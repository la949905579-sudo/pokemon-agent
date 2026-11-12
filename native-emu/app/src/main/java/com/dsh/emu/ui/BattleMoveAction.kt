package com.dsh.emu.ui

import com.dsh.emu.EmuCore
import com.dsh.emu.MainActivity
import com.dsh.emu.Nlog
import com.dsh.emu.game.Addresses
import com.dsh.emu.game.GameState
import com.dsh.emu.game.Memo
import com.dsh.emu.game.MoveCaster

/**
 * 战斗页「点击招式」的运行时适配：把 [MoveCaster] 的注入接口接到 JNI 内存/按键，
 * 并管线程、互斥、取消与日志。
 *
 * 约束：
 * - 单线程：同一时间只允许一次施放，连点直接忽略（busy）；
 * - 代际取消：[cancel] 由 closeKeys()（切页 / 开按键面板 / 载 ROM）调用，取消后不再按键；
 * - finally 必须 setKeys(0)，不能把方向键/A 留在按下状态；
 * - 失败只写 statusText（临时行，2.8s 样式）和 Nlog，不 Toast、不弹窗。
 */
object BattleMoveAction {
    /** 取消代际：与 MainActivity 的 WalkControl 分开，互不影响。 */
    @Volatile
    private var generation = 0

    @Volatile
    private var busy = false

    /** 取消正在进行的施放（closeKeys 路径调用）。 */
    fun cancel() {
        generation++
    }

    /** 点击第 [index] 个招式（0..3）。从 Compose 主线程调用，立即返回。 */
    fun cast(activity: MainActivity, index: Int) {
        if (busy) return
        val myGen = ++generation
        busy = true
        Thread {
            var res: MoveCaster.Result? = null
            try {
                val io = object : MoveCaster.Io {
                    override fun readTurn(): Int = GameState.turnFlag()

                    // 适配层直接读光标地址：按任务卡边界 GameState 不改；
                    // Compose 层仍只消费 EmuStatus，不碰内存。
                    override fun readMainCursor(): Int = Memo.u8(Addresses.MAIN_CURSOR)
                    override fun readMoveCursor(): Int = Memo.u8(Addresses.MOVE_CURSOR)
                    override fun pressDir(dir: MoveCaster.Dir, ms: Long) = press(maskOf(dir), ms, myGen)
                    override fun pressA(ms: Long) = press(EmuCore.KEY_A, ms, myGen)
                    override fun sleep(ms: Long) { interruptibleSleep(ms, myGen) }
                    override fun cancelled(): Boolean = myGen != generation
                }
                res = MoveCaster.cast(index, io)
            } catch (e: Exception) {
                // 只接 Exception，不吞 OOM；异常也要清键并记 ERROR。
                Nlog.error(
                    "battle.move", "idx" to index, "ok" to false,
                    "reason" to "exception", "err" to e.javaClass.simpleName,
                )
            } finally {
                EmuCore.setKeys(0)
                busy = false
            }
            val r = res ?: return@Thread
            logResult(r)
            // 已取消时不弹失败提示（A 已按下但取消导致回合没推进的情况只记日志）。
            if (!r.ok && r.reason != MoveCaster.Reason.CANCELLED && myGen == generation) {
                hintOf(r.reason)?.let { hint ->
                    activity.runOnUiThread { activity.statusText.value = hint }
                }
            }
        }.apply { isDaemon = true }.start()
    }

    /** 按住 keys 掩码 ms 毫秒；取消后尽快松开（统一在 finally 清键）。 */
    private fun press(keys: Int, ms: Long, myGen: Int) {
        if (myGen != generation) return
        try {
            EmuCore.setKeys(keys)
            interruptibleSleep(ms, myGen)
        } finally {
            EmuCore.setKeys(0)
        }
    }

    private fun maskOf(dir: MoveCaster.Dir): Int = when (dir) {
        MoveCaster.Dir.UP -> EmuCore.KEY_UP
        MoveCaster.Dir.DOWN -> EmuCore.KEY_DOWN
        MoveCaster.Dir.LEFT -> EmuCore.KEY_LEFT
        MoveCaster.Dir.RIGHT -> EmuCore.KEY_RIGHT
    }

    /** 可中断 sleep：每 20ms 看一次代际，取消后尽快停。 */
    private fun interruptibleSleep(ms: Long, myGen: Int): Boolean {
        var left = ms
        while (left > 0) {
            if (myGen != generation) return false
            val chunk = if (left < 20L) left else 20L
            try {
                Thread.sleep(chunk)
            } catch (_: InterruptedException) {
                return false
            }
            left -= chunk
        }
        return myGen == generation
    }

    private fun logResult(r: MoveCaster.Result) {
        val fields = arrayOf<Pair<String, Any?>>(
            "idx" to r.index,
            "ok" to r.ok,
            "reason" to r.reason.name.lowercase(),
            "turn_before" to r.turnBefore,
            "turn_after" to r.turnAfter,
            "cursor_start" to r.cursorStart,
            "cursor_end" to r.cursorEnd,
            "steps" to r.steps,
            "ms" to r.elapsedMs,
        )
        // 取消属正常收尾（用户切页/收面板），不算失败；其余失败一律 WARN。
        if (r.ok || r.reason == MoveCaster.Reason.CANCELLED) Nlog.info("battle.move", *fields)
        else Nlog.warn("battle.move", *fields)
    }

    /** 失败原因 → 临时行文案（短句）。 */
    private fun hintOf(reason: MoveCaster.Reason): String? = when (reason) {
        MoveCaster.Reason.TURN_NOT_MOVES, MoveCaster.Reason.MAIN_NOT_MOVES -> "招式菜单未展开"
        MoveCaster.Reason.CURSOR_UNSTABLE,
        MoveCaster.Reason.CURSOR_MISMATCH,
        MoveCaster.Reason.CURSOR_MOVE_FAIL -> "光标没到位"
        MoveCaster.Reason.TURN_NOT_CHANGED, MoveCaster.Reason.TURN_READ_FAIL -> "没出招，已停止"
        MoveCaster.Reason.BAD_TARGET -> "这招不可用"
        MoveCaster.Reason.OK, MoveCaster.Reason.CANCELLED -> null
    }
}
