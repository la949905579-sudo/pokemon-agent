package com.dsh.emu.ui

import com.dsh.emu.EmuCore
import com.dsh.emu.MainActivity
import com.dsh.emu.Nlog
import com.dsh.emu.game.BattleMoveMenu
import com.dsh.emu.game.GameState
import com.dsh.emu.game.MoveCaster

/**
 * 横屏点击 → 游戏输入（触屏所见即所得）。
 *
 * 场景判定由 [GameState.scene] 给出，动作分派：
 * - `battle_moves`：点 2×2 招式格 → [BattleMoveAction.cast]（自带逐格回读 + 二次确认）；
 * - `battle_main`：点「战斗」→ 回读主菜单光标、逐格挪到 0 → 按 A，回读确认进入招式菜单；
 * - `battle_intro` / `battle_end`：点任意处 = 短按 A 推进文字；
 * - `map`：对话框打开 → 点下方对话区短按 A 推进；否则点地图位置 → 同图 BFS 走过去
 *   （复用 [walkTo]，路径不可达 / 地图数据没准备好就提示、不盲走）；
 * - 其它场景（动画等）不按键。
 *
 * fail-closed：所有前置状态先回读，不满足就只提示；不补按、不重试。
 * 自动战斗运行时不接点击（两套按键循环会打架）。
 */
internal object Wysiwyg {

    private const val A_MS = 300L
    private const val STEP_MS = 80L
    private const val SETTLE_MS = 280L
    private const val VERIFY_MS = 150L
    private const val VERIFY_TIMES = 8
    private const val MAX_STEPS = 8
    private const val TURN_MAIN_MENU = 1
    private const val TURN_MOVES_MENU = 2

    /** 同一时间只跑一个按键线程（防止连点叠按）。 */
    @Volatile private var busy = false

    /** 横屏点击入口。[gx]/[gy] 是游戏像素坐标（已由 [TouchMap.viewToGame] 换算）。 */
    fun onTap(activity: MainActivity, s: EmuStatus, gx: Int, gy: Int) {
        if (!activity.runningState.value) return
        if (AutoBattle.running.value) {
            activity.statusText.value = "自动战斗中，先关掉再点"
            return
        }
        val scene = GameState.scene()
        when (scene) {
            "battle_moves" -> {
                val idx = TouchMap.moveIndexAt(gx, gy)
                Nlog.info("wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy, "move" to (idx ?: -1))
                if (idx != null) BattleMoveAction.cast(activity, idx)
            }
            "battle_main" -> {
                val fight = TouchMap.isFightTap(gx, gy)
                Nlog.info("wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy, "fight" to fight)
                if (fight) openMoveMenu(activity) else activity.statusText.value = "横屏：点「战斗」开招式"
            }
            "battle_intro", "battle_end" -> {
                Nlog.info("wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy, "action" to "advance")
                pressAAdvance(activity)
            }
            "map" -> {
                if (GameState.inDialog()) {
                    val onBox = TouchMap.isDialogTap(gx, gy)
                    Nlog.info("wysiwyg.tap", "scene" to "dialog", "x" to gx, "y" to gy, "onBox" to onBox)
                    if (onBox) pressAAdvance(activity) else activity.statusText.value = "点下方对话框推进"
                } else {
                    tapMap(activity, s, gx, gy)
                }
            }
            else -> Nlog.info("wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy, "action" to "ignore")
        }
    }

    // ---------- 战斗 ----------

    /**
     * 点「战斗」：回读主菜单光标 → 逐格挪到 0（每步回读）→ 按 A → 回读 TURN_FLAG==2。
     * 任何一步回读失败都停，不补按。
     */
    private fun openMoveMenu(activity: MainActivity) {
        if (!beginBusy()) return
        Thread {
            try {
                if (GameState.turnFlag() != TURN_MAIN_MENU) {
                    hint(activity, "没在主菜单")
                    return@Thread
                }
                var cur = BattleMoveMenu.readMainCursor()
                if (cur !in 0..3) {
                    hint(activity, "读不到主菜单光标")
                    return@Thread
                }
                var steps = 0
                while (cur != 0 && steps < MAX_STEPS) {
                    val dir = MoveCaster.nextDirection(cur, 0) ?: break
                    pressDir(dir, STEP_MS)
                    sleep(SETTLE_MS)
                    val next = BattleMoveMenu.readMainCursor()
                    if (next !in 0..3) {
                        hint(activity, "读不到主菜单光标")
                        return@Thread
                    }
                    cur = next
                    steps++
                }
                if (cur != 0) {
                    hint(activity, "光标没到位")
                    return@Thread
                }
                sleep(120)
                if (BattleMoveMenu.readMainCursor() != 0) {
                    hint(activity, "光标没到位")
                    return@Thread
                }
                EmuCore.setKeys(EmuCore.KEY_A)
                sleep(A_MS)
                EmuCore.setKeys(0)
                var ok = false
                for (i in 0 until VERIFY_TIMES) {
                    if (GameState.turnFlag() == TURN_MOVES_MENU) { ok = true; break }
                    sleep(VERIFY_MS)
                }
                Nlog.info(
                    "wysiwyg.fight", "ok" to ok, "cursor" to cur, "steps" to steps,
                    "turn" to GameState.turnFlag(),
                )
                if (!ok) hint(activity, "没打开招式菜单")
            } catch (e: Exception) {
                Nlog.error("wysiwyg.fight", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    /** 短按 A 推进对话 / 战斗文字（不校验结果：对话框推进没有可靠的单一回读）。 */
    private fun pressAAdvance(activity: MainActivity) {
        if (!beginBusy()) return
        Thread {
            try {
                EmuCore.setKeys(EmuCore.KEY_A)
                sleep(A_MS)
            } catch (e: Exception) {
                Nlog.error("wysiwyg.a", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    // ---------- 地图 ----------

    /** 点地图位置 → 同图 BFS 走过去。坐标用最新回读值，地图数据用最近一帧状态。 */
    private fun tapMap(activity: MainActivity, s: EmuStatus, gx: Int, gy: Int) {
        val tiles = s.mmTiles ?: run {
            Nlog.info("wysiwyg.tap", "scene" to "map", "x" to gx, "y" to gy, "action" to "no_tiles")
            activity.statusText.value = "没有地图数据"
            return
        }
        val w = tiles.firstOrNull()?.size ?: 0
        val h = tiles.size
        if (w <= 0 || h <= 0) {
            activity.statusText.value = "没有地图数据"
            return
        }
        val from = GameState.coords() ?: run {
            activity.statusText.value = "读不到坐标"
            return
        }
        val to = TouchMap.mapTarget(from.x, from.y, gx, gy, w, h) ?: run {
            Nlog.info("wysiwyg.tap", "scene" to "map", "x" to gx, "y" to gy, "action" to "oob")
            activity.statusText.value = "点在地图外"
            return
        }
        Nlog.info(
            "wysiwyg.map",
            "from" to "${from.x},${from.y}",
            "target" to "${to.first},${to.second}",
            "tap" to "$gx,$gy",
        )
        walkTo(
            activity,
            s.copy(mmPx = from.x, mmPy = from.y, mmW = w, mmH = h, mmTiles = tiles),
            to.first, to.second,
        )
    }

    // ---------- 小工具 ----------

    private fun pressDir(dir: MoveCaster.Dir, ms: Long) {
        val mask = when (dir) {
            MoveCaster.Dir.UP -> EmuCore.KEY_UP
            MoveCaster.Dir.DOWN -> EmuCore.KEY_DOWN
            MoveCaster.Dir.LEFT -> EmuCore.KEY_LEFT
            MoveCaster.Dir.RIGHT -> EmuCore.KEY_RIGHT
        }
        try {
            EmuCore.setKeys(mask)
            sleep(ms)
        } finally {
            EmuCore.setKeys(0)
        }
    }

    private fun hint(activity: MainActivity, msg: String) {
        activity.statusText.value = msg
    }

    private fun beginBusy(): Boolean {
        if (busy) return false
        busy = true
        return true
    }

    private fun endBusy() { busy = false }

    private fun sleep(ms: Long) {
        try { Thread.sleep(ms) } catch (_: InterruptedException) {}
    }
}
