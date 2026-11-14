package com.dsh.emu.ui

import androidx.compose.runtime.mutableStateOf
import com.dsh.emu.EmuCore
import com.dsh.emu.MainActivity
import com.dsh.emu.Nlog
import com.dsh.emu.game.AutoBattlePlanner
import com.dsh.emu.game.GameState
import com.dsh.emu.game.Species

/**
 * 自动战斗开关（设置页）后台循环。
 *
 * 流程（fail-closed，不盲按）：
 * - `scene()==battle_moves`（招式菜单已展开）→ 用 [AutoBattlePlanner] 选最优招式 →
 *   `BattleMoveAction.cast` 施放 → 等回合推进；
 * - `battle_main`（主菜单）→ 短按 A 打开招式菜单（带冷却，不连发）；
 * - `battle_intro` / `battle_end` → 短按 A 推进文字；
 * - 动画/地图/其它 → 只等待，不按键。
 *
 * 安全：同一时间只有一个循环；连续 3 次施放失败自动停止；ROM 载入 / 重置 / 退出 /
 * 手动关闭时 `cancel()`（静默）或 `stop()`（写状态行）。
 */
object AutoBattle {

    /** 循环节拍。 */
    private const val TICK_MS = 300L
    /** A 键按住时长（与 MoveCaster.A_MS 同量级）。 */
    private const val A_MS = 320L
    /** A 键冷却：避免在开场文字里连按。 */
    private const val A_COOLDOWN_MS = 650L
    /** 施放后等回合推进的上限。 */
    private const val WAIT_TURN_MS = 4000L
    /** 连续失败上限。 */
    private const val MAX_FAILS = 3

    /** 是否在自动战斗中（Compose 状态，设置页/状态行读取）。 */
    val running = mutableStateOf(false)

    @Volatile private var generation = 0
    @Volatile private var thread: Thread? = null
    @Volatile private var lastAAt = 0L

    fun toggle(activity: MainActivity) {
        if (running.value) stop(activity) else start(activity)
    }

    fun start(activity: MainActivity) {
        if (running.value) return
        if (!activity.romReadyState.value) {
            activity.statusText.value = "先载入 ROM"
            return
        }
        val myGen = ++generation
        lastAAt = 0L
        running.value = true
        activity.statusText.value = "自动战斗：开（A 推进菜单，自动选招）"
        thread = Thread { runLoop(activity, myGen) }.apply {
            isDaemon = true
            name = "auto-battle"
            start()
        }
    }

    /** 手动关闭 / 自停：写状态行。 */
    fun stop(activity: MainActivity?, reason: String = "关") {
        if (!running.value && reason == "关") return
        generation++
        running.value = false
        try { EmuCore.setKeys(0) } catch (_: Throwable) {}
        activity?.statusText?.value = "自动战斗：$reason"
    }

    /** 静默取消（ROM 载入 / 重置 / 退出）：不写状态行。 */
    fun cancel() {
        generation++
        running.value = false
    }

    private fun runLoop(activity: MainActivity, myGen: Int) {
        var fails = 0
        while (myGen == generation) {
            try {
                if (!activity.runningState.value) break
                when (GameState.scene()) {
                    "battle_moves" -> {
                        val plan = planForBattle()
                        if (plan == null) {
                            stop(activity, "无可用招式，已停止")
                            return
                        }
                        BattleMoveAction.cast(activity, plan.slotIndex)
                        if (waitTurnEnds(myGen)) fails = 0 else {
                            fails++
                            if (fails >= MAX_FAILS) {
                                stop(activity, "施放连续失败，已停止")
                                return
                            }
                        }
                    }
                    "battle_main" -> pressA()
                    "battle_intro", "battle_end" -> pressA()
                    else -> sleep(TICK_MS)   // 动画 / 地图：只等，不按
                }
            } catch (e: Exception) {
                Nlog.error("auto.battle", "err" to e.javaClass.simpleName)
                sleep(TICK_MS)
            }
        }
    }

    private fun planForBattle(): AutoBattlePlanner.Plan? {
        val enemyTypes = Species.typesOf(GameState.enemySpecies())
        val mySpecies = GameState.mySpecies()
        val active = GameState.party()
            .firstOrNull { it.species == mySpecies && it.hp > 0 }
            ?: GameState.party().firstOrNull { it.hp > 0 }
        val moves = GameState.myMoves()
        val pp = active?.pp ?: emptyList()
        return AutoBattlePlanner.plan(moves, pp, enemyTypes)
    }

    /** 等这一回合结束（离开招式菜单或战斗结束）；超时返回 false。 */
    private fun waitTurnEnds(myGen: Int): Boolean {
        val deadline = System.currentTimeMillis() + WAIT_TURN_MS
        while (System.currentTimeMillis() < deadline) {
            if (myGen != generation) return false
            if (GameState.scene() != "battle_moves") return true
            sleep(80L)
        }
        return false
    }

    /** 短按 A（冷却内不重复按），推进对话 / 打开招式菜单。 */
    private fun pressA() {
        val now = System.currentTimeMillis()
        if (now - lastAAt < A_COOLDOWN_MS) {
            sleep(TICK_MS)
            return
        }
        lastAAt = now
        try {
            EmuCore.setKeys(EmuCore.KEY_A)
            sleep(A_MS)
        } finally {
            try { EmuCore.setKeys(0) } catch (_: Throwable) {}
        }
        sleep(TICK_MS)
    }

    private fun sleep(ms: Long) {
        try { Thread.sleep(ms) } catch (_: InterruptedException) {}
    }
}
