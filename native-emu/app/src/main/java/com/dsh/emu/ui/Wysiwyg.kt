package com.dsh.emu.ui

import com.dsh.emu.EmuCore
import com.dsh.emu.MainActivity
import com.dsh.emu.Nlog
import com.dsh.emu.game.BattleMoveMenu
import com.dsh.emu.game.GameState
import com.dsh.emu.game.MenuState
import com.dsh.emu.game.MoveCaster

/**
 * 横屏点击 → 游戏输入（触屏所见即所得）。
 *
 * 场景判定由 [GameState.scene] 给出，动作分派：
 * - `battle_moves`：MAIN_CURSOR==0 时点 2×2 招式格 → [BattleMoveAction.cast]（自带逐格回读）；
 *   MAIN_CURSOR==1/2（背包/队伍子菜单）时点底部「取消/合上」条 → 按 B 退出；
 * - `battle_main`：E83==1 才是真主菜单，点「战斗 / 背包 / 宝可梦 / 逃跑」→ 回读 MAIN_CURSOR、
 *   逐格挪到目标 → 二次确认 → 按 A → 按项回读验证；E83==0 是战斗里的「是/否」选项框，
 *   走 [MenuState] 标准是/否点选（不支持就不按 A）；
 * - `battle_intro` / `battle_end`：点任意处 = 短按 A 推进文字；
 * - `map`：有对话框时——标准「是/否」框点选项行（回读光标后再按 A）；有选项框但非标准框时
 *   只提示不按 A（避免误确认）；纯文字对话框点下方 = 推进；没有对话框 → 点地图位置同图 BFS；
 * - 其它场景（动画等）不按键。
 *
 * fail-closed：所有前置状态先回读，不满足就只提示；不补按、不重试。
 * 自动战斗运行时不接点击（两套按键循环会打架）。
 * 离开横屏 / 打开设置面板时 [cancel]：已在跑的按键序列尽快停手。
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
    private const val BATTLE_MENU_MAIN = 1
    /** 战斗主菜单「战斗/背包/宝可梦」打开子菜单的等待上限（背包/队伍可能比招式菜单慢）。 */
    private const val OPEN_SUBMENU_MS = 3000L
    /** 「战斗」打开招式菜单的等待上限。 */
    private const val OPEN_MOVES_MS = 2500L
    /** 逃跑的观察窗口（成功=战斗结束；失败=过场后回主菜单）。 */
    private const val ESCAPE_WATCH_MS = 4000L

    /** 同一时间只跑一个按键线程（防止连点叠按）。 */
    @Volatile private var busy = false

    /** 取消代际：离开横屏/开设置面板时 +1，正在跑的按键序列尽快停手。 */
    @Volatile private var generation = 0

    /** 取消当前所有横屏按键序列（不写状态行）。 */
    fun cancel() { generation++ }

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
                // TURN_FLAG==2 同时覆盖「招式菜单」和「背包/队伍子菜单」，用 MAIN_CURSOR 区分。
                val main = BattleMoveMenu.readMainCursor()
                if (main == 0) {
                    val idx = TouchMap.moveIndexAt(gx, gy)
                    Nlog.info("wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy, "move" to (idx ?: -1))
                    if (idx != null) BattleMoveAction.cast(activity, idx)
                } else if (main == 1 || main == 2) {
                    val cancel = TouchMap.isSubmenuCancelTap(main, gx, gy)
                    Nlog.info(
                        "wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy,
                        "submenu" to (if (main == 1) "bag" else "party"), "cancel" to cancel,
                    )
                    if (cancel) cancelSubmenu(activity, main) else activity.statusText.value = "点底部「取消」返回"
                } else {
                    Nlog.info("wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy, "main" to main, "action" to "ignore")
                }
            }
            "battle_main" -> {
                val idx = TouchMap.mainMenuIndexAt(gx, gy)
                val isMainMenu = GameState.battleMenuFlag() == BATTLE_MENU_MAIN
                Nlog.info(
                    "wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy,
                    "menu" to (idx ?: -1), "mainMenu" to isMainMenu,
                )
                if (idx != null) {
                    if (isMainMenu) battleMainAction(activity, idx)
                    else battleChoiceTap(activity, gx, gy)   // E83==0：战斗里的是/否选项框
                }
            }
            "battle_intro", "battle_end" -> {
                Nlog.info("wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy, "action" to "advance")
                pressAAdvance(activity)
            }
            "map" -> {
                if (GameState.inDialog()) handleDialogTap(activity, gx, gy)
                else tapMap(activity, s, gx, gy)
            }
            else -> Nlog.info("wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy, "action" to "ignore")
        }
    }

    // ---------- 地图上的对话框 ----------

    /**
     * 对话框点击：
     * - 标准「是/否」框：点选项行 → 回读光标逐行挪到目标再按 A；
     * - 有选项框但非标准布局：只提示（不按 A —— A 会默认确认当前选项）；
     * - 纯文字对话框：点下方对话区按 A 推进。
     */
    private fun handleDialogTap(activity: MainActivity, gx: Int, gy: Int) {
        val profile = MenuState.read()
        val yesNo = profile != null && MenuState.isStandardYesNo(profile)
        if (yesNo) {
            val idx = MenuState.optionIndexAt(profile!!, gx, gy)
            Nlog.info(
                "wysiwyg.tap", "scene" to "dialog", "x" to gx, "y" to gy,
                "option" to (idx ?: -1), "cursor" to profile.cursorPos,
            )
            if (idx != null) chooseDialogOption(activity, idx)
            else activity.statusText.value = "点对话框里的选项"
            return
        }
        if (profile != null && MenuState.insideWindow(profile, gx, gy)) {
            Nlog.info(
                "wysiwyg.tap", "scene" to "dialog", "x" to gx, "y" to gy,
                "option" to -1, "count" to profile.count, "action" to "unsupported",
            )
            activity.statusText.value = "该选项框横屏暂不支持，请竖屏"
            return
        }
        val onBox = TouchMap.isDialogTap(gx, gy)
        Nlog.info("wysiwyg.tap", "scene" to "dialog", "x" to gx, "y" to gy, "onBox" to onBox)
        if (onBox) pressAAdvance(activity) else activity.statusText.value = "点下方对话框推进"
    }

    // ---------- 战斗 ----------

    /**
     * 战斗主菜单点选（0=战斗 1=背包 2=宝可梦 3=逃跑）：
     * 回读 MAIN_CURSOR → 逐格挪到目标（每步回读）→ 二次确认 → 按 A → 按目标回读验证。
     * 前提：TURN_FLAG==1 且 E83==1（真主菜单，不是是/否选项框）。
     */
    private fun battleMainAction(activity: MainActivity, target: Int) {
        if (!beginBusy()) return
        val myGen = generation
        Thread {
            try {
                if (!inBattleMainMenu()) {
                    hint(activity, "没在主菜单")
                    return@Thread
                }
                var cur = BattleMoveMenu.readMainCursor()
                if (cur !in 0..3) {
                    hint(activity, "读不到主菜单光标")
                    return@Thread
                }
                var steps = 0
                while (cur != target && steps < MAX_STEPS) {
                    if (cancelled(myGen)) return@Thread
                    val dir = MoveCaster.nextDirection(cur, target) ?: break
                    pressDir(dir, STEP_MS)
                    sleep(SETTLE_MS)
                    if (cancelled(myGen)) return@Thread
                    val next = BattleMoveMenu.readMainCursor()
                    if (next !in 0..3) {
                        hint(activity, "读不到主菜单光标")
                        return@Thread
                    }
                    cur = next
                    steps++
                }
                if (cur != target) {
                    Nlog.warn(
                        "wysiwyg.battlemenu", "ok" to false, "reason" to "cursor",
                        "target" to target, "cursor" to cur, "steps" to steps,
                    )
                    hint(activity, "光标没到位")
                    return@Thread
                }
                sleep(120)
                if (cancelled(myGen)) return@Thread
                if (!inBattleMainMenu() || BattleMoveMenu.readMainCursor() != target) {
                    hint(activity, "光标没到位")
                    return@Thread
                }
                EmuCore.setKeys(EmuCore.KEY_A)
                sleep(A_MS)
                EmuCore.setKeys(0)
                val ok = verifyBattleMenu(target)
                Nlog.info(
                    "wysiwyg.battlemenu", "ok" to ok, "target" to target, "cursor" to cur,
                    "steps" to steps, "turn" to GameState.turnFlag(),
                    "main" to BattleMoveMenu.readMainCursor(),
                    "battle" to (if (GameState.inBattle()) 1 else 0),
                )
                if (!ok) hint(activity, "菜单没打开")
            } catch (e: Exception) {
                Nlog.error("wysiwyg.battlemenu", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    /** 战斗里的「是/否」选项框（E83==0）：标准是/否框可点选；否则只提示不按 A。 */
    private fun battleChoiceTap(activity: MainActivity, gx: Int, gy: Int) {
        val profile = MenuState.read()
        if (profile != null && MenuState.isStandardYesNo(profile)) {
            val idx = MenuState.optionIndexAt(profile, gx, gy)
            Nlog.info(
                "wysiwyg.tap", "scene" to "battle_choice", "x" to gx, "y" to gy,
                "option" to (idx ?: -1), "cursor" to profile.cursorPos,
            )
            if (idx != null) chooseDialogOption(activity, idx)
            else activity.statusText.value = "点对话框里的选项"
            return
        }
        Nlog.info("wysiwyg.tap", "scene" to "battle_choice", "x" to gx, "y" to gy, "action" to "unsupported")
        activity.statusText.value = "该选项框横屏暂不支持，请竖屏"
    }

    private fun inBattleMainMenu(): Boolean =
        GameState.turnFlag() == TURN_MAIN_MENU && GameState.battleMenuFlag() == BATTLE_MENU_MAIN

    /**
     * 按目标项回读验证：
     * - 0/1/2：等 TURN_FLAG==2 且 MAIN_CURSOR==目标（战斗 2.5s、背包/宝可梦 3s）；
     * - 3（逃跑）：成功=战斗结束；失败=过场后回主菜单 —— 两者都算「已处理」，只按观察到的变化判定。
     */
    private fun verifyBattleMenu(target: Int): Boolean {
        if (target == 3) {
            val deadline = System.currentTimeMillis() + ESCAPE_WATCH_MS
            while (System.currentTimeMillis() < deadline) {
                if (!GameState.inBattle()) return true
                if (GameState.turnFlag() != TURN_MAIN_MENU) return true
                sleep(VERIFY_MS)
            }
            return false
        }
        val limitMs = if (target == 0) OPEN_MOVES_MS else OPEN_SUBMENU_MS
        val deadline = System.currentTimeMillis() + limitMs
        while (System.currentTimeMillis() < deadline) {
            if (GameState.turnFlag() == TURN_MOVES_MENU && BattleMoveMenu.readMainCursor() == target) {
                return true
            }
            sleep(VERIFY_MS)
        }
        return false
    }

    /** 背包/队伍子菜单：点底部「取消/合上」条 → 按 B 返回主菜单，回读确认已退出。 */
    private fun cancelSubmenu(activity: MainActivity, menuMain: Int) {
        if (!beginBusy()) return
        val myGen = generation
        Thread {
            try {
                if (GameState.turnFlag() != TURN_MOVES_MENU) {
                    hint(activity, "没在子菜单")
                    return@Thread
                }
                EmuCore.setKeys(EmuCore.KEY_B)
                sleep(A_MS)
                EmuCore.setKeys(0)
                if (cancelled(myGen)) return@Thread
                var ok = false
                for (i in 0 until VERIFY_TIMES) {
                    sleep(VERIFY_MS)
                    if (GameState.turnFlag() == TURN_MAIN_MENU) {
                        ok = true
                        break
                    }
                }
                Nlog.info(
                    "wysiwyg.submenu", "ok" to ok, "kind" to (if (menuMain == 1) "bag" else "party"),
                    "turn" to GameState.turnFlag(), "main" to BattleMoveMenu.readMainCursor(),
                )
                if (!ok) hint(activity, "没返回战斗菜单")
            } catch (e: Exception) {
                Nlog.error("wysiwyg.submenu", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    /** 短按 A 推进对话 / 战斗文字（不校验结果：对话框推进没有可靠的单一回读）。 */
    private fun pressAAdvance(activity: MainActivity) {
        if (!beginBusy()) return
        val myGen = generation
        Thread {
            try {
                if (cancelled(myGen)) return@Thread
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

    // ---------- 对话选项 ----------

    /**
     * 点「是/否」的某一行：回读光标 → 逐行 UP/DOWN 挪到目标（每步回读）→ 二次确认 → 按 A。
     * 任何一步读不到 / 光标没到位就停，不按 A（fail-closed）。
     */
    private fun chooseDialogOption(activity: MainActivity, target: Int) {
        if (!beginBusy()) return
        val myGen = generation
        Thread {
            try {
                var p = MenuState.read()
                if (p == null || !MenuState.isStandardYesNo(p)) {
                    hint(activity, "对话选项读不到")
                    return@Thread
                }
                var cur = p.cursorPos
                var steps = 0
                while (cur != target && steps < MAX_STEPS) {
                    if (cancelled(myGen)) return@Thread
                    val step = MenuState.step(cur, target)
                    if (step == 0) break
                    pressMask(if (step > 0) EmuCore.KEY_DOWN else EmuCore.KEY_UP, STEP_MS)
                    sleep(SETTLE_MS)
                    if (cancelled(myGen)) return@Thread
                    val next = MenuState.read()
                    if (next == null || !MenuState.isStandardYesNo(next)) {
                        hint(activity, "对话选项读不到")
                        return@Thread
                    }
                    if (next.cursorPos == cur) {
                        // 没动：反向再试一次（不同菜单 wrap 行为不同）；仍不动就停
                        pressMask(if (step > 0) EmuCore.KEY_UP else EmuCore.KEY_DOWN, STEP_MS)
                        sleep(SETTLE_MS)
                        val back = MenuState.read()
                        if (back == null || !MenuState.isStandardYesNo(back) || back.cursorPos == cur) {
                            Nlog.warn(
                                "wysiwyg.dialog", "ok" to false, "reason" to "cursor",
                                "target" to target, "cursor" to cur, "steps" to steps,
                            )
                            hint(activity, "光标没到位")
                            return@Thread
                        }
                        p = back
                    } else {
                        p = next
                    }
                    cur = p.cursorPos
                    steps++
                }
                if (cur != target) {
                    Nlog.warn(
                        "wysiwyg.dialog", "ok" to false, "reason" to "cursor",
                        "target" to target, "cursor" to cur, "steps" to steps,
                    )
                    hint(activity, "光标没到位")
                    return@Thread
                }
                // 二次确认：等光标稳定后再读一次，仍是目标才按 A。
                sleep(120)
                if (cancelled(myGen)) return@Thread
                val confirm = MenuState.read()
                if (confirm == null || !MenuState.isStandardYesNo(confirm) || confirm.cursorPos != target) {
                    Nlog.warn("wysiwyg.dialog", "ok" to false, "reason" to "confirm", "target" to target)
                    hint(activity, "光标没到位")
                    return@Thread
                }
                EmuCore.setKeys(EmuCore.KEY_A)
                sleep(A_MS)
                EmuCore.setKeys(0)
                Nlog.info(
                    "wysiwyg.dialog", "ok" to true, "target" to target,
                    "cursor" to cur, "steps" to steps, "count" to p.count,
                )
            } catch (e: Exception) {
                Nlog.error("wysiwyg.dialog", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    /** 按住单个按键掩码 ms 毫秒（finally 一定松开）。 */
    private fun pressMask(mask: Int, ms: Long) {
        try {
            EmuCore.setKeys(mask)
            sleep(ms)
        } finally {
            EmuCore.setKeys(0)
        }
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

    private fun cancelled(myGen: Int): Boolean = myGen != generation

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
