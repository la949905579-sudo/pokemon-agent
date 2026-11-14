package com.dsh.emu.ui

import com.dsh.emu.EmuCore
import com.dsh.emu.MainActivity
import com.dsh.emu.Nlog
import com.dsh.emu.game.BattleMoveMenu
import com.dsh.emu.game.GameState
import com.dsh.emu.game.MenuState
import com.dsh.emu.game.MoveCaster
import com.dsh.emu.game.SubmenuState

/**
 * 横屏点击 → 游戏输入（触屏所见即所得）。
 *
 * 场景判定由 [GameState.scene] 给出，动作分派：
 * - `battle_moves`：先按 `gWindows[0]` 几何识别子菜单（见 [SubmenuState]）：
 *   - 背包：点 ◀▶ 翻口袋（回读 pocket）、点道具行回首页逐行挪光标→二次确认→按 A、
 *     点底部「合上背包」→ 按 B；
 *   - 队伍：点大框/行回首页逐行挪光标→二次确认→按 A，点底部「取消」→ 按 B；
 *   - 招式菜单（MAIN_CURSOR==0）：点 2×2 招式格 → [BattleMoveAction.cast]（自带逐格回读）；
 * - `battle_main`：E83!=0 才是真主菜单，点「战斗 / 背包 / 宝可梦 / 逃跑」→ 回读 MAIN_CURSOR、
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
    /** 战斗主菜单「战斗/背包/宝可梦」打开子菜单的等待上限（背包/队伍可能比招式菜单慢）。 */
    private const val OPEN_SUBMENU_MS = 3000L
    /** 「战斗」打开招式菜单的等待上限。 */
    private const val OPEN_MOVES_MS = 2500L
    /** 逃跑的观察窗口（成功=战斗结束；失败=过场后回主菜单）。 */
    private const val ESCAPE_WATCH_MS = 4000L
    /** 子菜单里单步方向键的按住时长：高倍速（4x）下要短，避免连发多走几格；每步后都回读。 */
    private const val NAV_TAP_MS = 40L
    private const val NAV_SETTLE_MS = 260L
    /** 口袋切换动画（约 12 帧）等待上限。 */
    private const val POCKET_WAIT_MS = 2000L
    /** 道具行 / 队伍格子点选后等待界面变化的上限。 */
    private const val ACTION_WAIT_MS = 3000L

    /** 同一时间只跑一个按键线程（防止连点叠按）。 */
    @Volatile private var busy = false

    /** 取消代际：离开横屏/开设置面板时 +1，正在跑的按键序列尽快停手。 */
    @Volatile private var generation = 0

    /**
     * 取消所有横屏触屏动作（不写状态行）：对话/菜单序列 + 招式施放（[BattleMoveAction]）+
     * 地图走位（[WalkControl]），并清掉可能残留的按键掩码。
     * 离开横屏 / 打开设置面板 / 横屏面板里重置时调用（镜像竖屏 closeKeys 的收口口径）。
     */
    fun cancelAll() {
        generation++
        WalkControl.generation++
        BattleMoveAction.cancel()
        try {
            EmuCore.setKeys(0)
        } catch (_: Throwable) {
        }
    }

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
                // 子菜单里弹的「是/否」框（例如换人确认）E83==0：按标准是/否点选，别当子菜单操作。
                if (GameState.battleMenuFlag() == 0) {
                    Nlog.info("wysiwyg.tap", "scene" to "battle_choice", "x" to gx, "y" to gy)
                    battleChoiceTap(activity, gx, gy)
                    return
                }
                // TURN_FLAG==2 同时覆盖「招式菜单」和「背包/队伍子菜单」。
                // 子菜单种类用 gWindows[0] 几何识别：MAIN_CURSOR 会被「背包→选道具→队伍菜单」沿用（仍是 1）。
                when (SubmenuState.readKind()) {
                    SubmenuState.Kind.BAG -> handleBagTap(activity, gx, gy)
                    SubmenuState.Kind.PARTY -> handlePartyTap(activity, gx, gy)
                    null -> {
                        val main = BattleMoveMenu.readMainCursor()
                        if (main == 0) {
                            val idx = TouchMap.moveIndexAt(gx, gy)
                            Nlog.info("wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy, "move" to (idx ?: -1))
                            if (idx != null) BattleMoveAction.cast(activity, idx)
                        } else if (main == 1 || main == 2) {
                            // 兜底：子菜单窗口还没建好/正在收，只认底部取消条。
                            val kind = if (main == 1) SubmenuState.Kind.BAG else SubmenuState.Kind.PARTY
                            val cancel = TouchMap.isSubmenuCancelTap(main, gx, gy)
                            Nlog.info(
                                "wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy,
                                "submenu" to kind.logName, "cancel" to cancel,
                            )
                            if (cancel) cancelSubmenu(activity, kind)
                            else activity.statusText.value = "点底部「取消」返回"
                        } else {
                            Nlog.info(
                                "wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy,
                                "main" to main, "action" to "ignore",
                            )
                        }
                    }
                }
            }
            "battle_main" -> {
                if (GameState.battleMenuFlag() != 0) {
                    val idx = TouchMap.mainMenuIndexAt(gx, gy)
                    Nlog.info(
                        "wysiwyg.tap", "scene" to scene, "x" to gx, "y" to gy,
                        "menu" to (idx ?: -1), "mainMenu" to true,
                    )
                    if (idx != null) battleMainAction(activity, idx)
                } else {
                    // E83==0：战斗里的「是/否」选项框（布局和主菜单 2×2 不重叠，必须无条件进这里）
                    Nlog.info(
                        "wysiwyg.tap", "scene" to "battle_choice", "x" to gx, "y" to gy,
                    )
                    battleChoiceTap(activity, gx, gy)
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
        if (profile != null) {
            // 有任何菜单/选项框在：绝不按 A（A 会默认确认当前选项），只认标准是/否的行点击。
            if (MenuState.isStandardYesNo(profile)) {
                val idx = MenuState.optionIndexAt(profile, gx, gy)
                Nlog.info(
                    "wysiwyg.tap", "scene" to "dialog", "x" to gx, "y" to gy,
                    "option" to (idx ?: -1), "cursor" to profile.cursorPos,
                )
                if (idx != null) chooseDialogOption(activity, idx)
                else activity.statusText.value = "点对话框里的选项"
            } else {
                Nlog.info(
                    "wysiwyg.tap", "scene" to "dialog", "x" to gx, "y" to gy,
                    "option" to -1, "count" to profile.count, "action" to "unsupported",
                )
                activity.statusText.value = "该选项框横屏暂不支持，请竖屏"
            }
            return
        }
        // 纯文字对话（无菜单窗口）：点下方 = 按 A 推进
        val onBox = TouchMap.isDialogTap(gx, gy)
        Nlog.info("wysiwyg.tap", "scene" to "dialog", "x" to gx, "y" to gy, "onBox" to onBox)
        if (onBox) pressAAdvance(activity) else activity.statusText.value = "点下方对话框推进"
    }

    // ---------- 战斗 ----------

    /**
     * 战斗主菜单点选（0=战斗 1=背包 2=宝可梦 3=逃跑）：
     * 回读 MAIN_CURSOR → 逐格挪到目标（每步回读）→ 二次确认 → 按 A → 按目标回读验证。
     * 前提：TURN_FLAG==1 且 E83!=0（真主菜单；E83==0 是战斗内是/否选项框）。
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

    private fun inBattleMainMenu(): Boolean = GameState.inBattleMainMenu()

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

    /** 背包/队伍子菜单：点底部条 → 按 B 返回，回读窗口种类确认已退出（道具选目标的队伍菜单只退回背包）。 */
    private fun cancelSubmenu(activity: MainActivity, kind: SubmenuState.Kind) {
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
                // B 返回有延迟（实测最长约 2.5s）：背包/队伍会先回战斗主菜单；
                // 道具选目标弹出的队伍菜单 B 只退回背包，所以以「窗口种类变了」为准。
                val ok = waitUntil(3600L) {
                    // 读到种类变化才算关掉；读不到（null）不作数，避免把「读失败」当成功。
                    val k = SubmenuState.readKind()
                    (k != null && k != kind) || GameState.turnFlag() == TURN_MAIN_MENU
                }
                Nlog.info(
                    "wysiwyg.submenu", "ok" to ok, "kind" to kind.logName,
                    "turn" to GameState.turnFlag(), "main" to BattleMoveMenu.readMainCursor(),
                )
                if (!ok) hint(activity, "没返回")
            } catch (e: Exception) {
                Nlog.error("wysiwyg.submenu", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    // ---------- 战斗子菜单：背包 / 队伍 ----------

    /**
     * 背包点按：
     * - ◀/▶ 箭头（真机 (8,72)/(72,72)）→ 按 LEFT/RIGHT 翻口袋，回读 pocket；
     * - 道具列表行（win0 内区 x=88..232、行高 16）→ 回首页逐行挪光标 → 二次确认 → 按 A
     *   （有道具＝使用道具/打开目标选择；最后一行「取消」＝合上背包）；
     * - 底部条（y≥114）按实机图标态区分：光标在「取消」行/空口袋（显示「合上背包」）→ 按 B 关闭；
     *   光标在道具行（显示道具图标+说明，游戏里不是按钮）→ 只提示，不关。
     */
    private fun handleBagTap(activity: MainActivity, gx: Int, gy: Int) {
        when {
            TouchMap.BAG_LEFT_ARROW_ZONE.hit(gx, gy) -> {
                Nlog.info("wysiwyg.tap", "scene" to "bag", "x" to gx, "y" to gy, "action" to "pocket_prev")
                switchPocket(activity, -1)
            }
            TouchMap.BAG_RIGHT_ARROW_ZONE.hit(gx, gy) -> {
                Nlog.info("wysiwyg.tap", "scene" to "bag", "x" to gx, "y" to gy, "action" to "pocket_next")
                switchPocket(activity, +1)
            }
            TouchMap.BAG_SCROLL_UP_ZONE.hit(gx, gy) -> {
                Nlog.info("wysiwyg.tap", "scene" to "bag", "x" to gx, "y" to gy, "action" to "scroll_up")
                scrollBag(activity, -1)
            }
            TouchMap.BAG_SCROLL_DOWN_ZONE.hit(gx, gy) -> {
                Nlog.info("wysiwyg.tap", "scene" to "bag", "x" to gx, "y" to gy, "action" to "scroll_down")
                scrollBag(activity, +1)
            }
            TouchMap.BAG_CANCEL_ZONE.hit(gx, gy) -> {
                Nlog.info("wysiwyg.tap", "scene" to "bag", "x" to gx, "y" to gy, "action" to "bottom_bar")
                closeBagByBar(activity)
            }
            else -> {
                val row = TouchMap.bagRowAt(gx, gy)
                Nlog.info("wysiwyg.tap", "scene" to "bag", "x" to gx, "y" to gy, "row" to (row ?: -1))
                if (row != null) chooseBagRow(activity, row)
                else activity.statusText.value = "点道具行 / ◀▶ 翻口袋 / 底部合上背包"
            }
        }
    }

    /** 队伍点按：点大框/行 = 选中该只（换人/用道具目标），点底部「取消」= 按 B 返回。 */
    private fun handlePartyTap(activity: MainActivity, gx: Int, gy: Int) {
        if (TouchMap.PARTY_CANCEL_ZONE.hit(gx, gy)) {
            Nlog.info("wysiwyg.tap", "scene" to "party", "x" to gx, "y" to gy, "action" to "cancel")
            cancelSubmenu(activity, SubmenuState.Kind.PARTY)
            return
        }
        val slot = TouchMap.partySlotAt(gx, gy)
        Nlog.info("wysiwyg.tap", "scene" to "party", "x" to gx, "y" to gy, "slot" to (slot ?: -1))
        if (slot != null) choosePartySlot(activity, slot)
        else activity.statusText.value = "点宝可梦格子 / 底部取消"
    }

    /**
     * 点背包底部条：按实机图标态区分——底部条显示「合上背包」+返回图标（光标在最后一行「取消」/空口袋）
     * 才按 B 合上；显示道具图标+说明（光标在道具行）时游戏里不是按钮，只提示不关。
     *
     * 判断方式（不依赖道具数量地址）：按一次 DOWN 再回读光标——
     * 光标不动 = 已在最后一行 → 合上背包；光标动了 = 不在最后一行 → 按 UP 还原后提示。
     * 注：>6 种道具、列表滚动时 DOWN 可能只滚窗口不动光标，此时会按「合上背包」处理（与旧行为一致）。
     */
    private fun closeBagByBar(activity: MainActivity) {
        if (!beginBusy()) return
        val myGen = generation
        Thread {
            try {
                if (SubmenuState.readKind() != SubmenuState.Kind.BAG) {
                    hint(activity, "没在背包里")
                    return@Thread
                }
                val pocket = SubmenuState.pocket()
                val from = if (pocket < 0) -1 else SubmenuState.bagCursor(pocket)
                if (from < 0) {
                    hint(activity, "读不到背包")
                    return@Thread
                }
                pressMask(EmuCore.KEY_DOWN, NAV_TAP_MS)
                sleep(NAV_SETTLE_MS)
                if (cancelled(myGen)) return@Thread
                val down = if (pocket < 0) -1 else SubmenuState.bagCursor(pocket)
                if (down == from) {
                    // 已在最后一行（「取消」/空口袋）：底部条就是「合上背包」→ 按 B 关
                    EmuCore.setKeys(EmuCore.KEY_B)
                    sleep(A_MS)
                    EmuCore.setKeys(0)
                    val ok = waitUntil(3600L) {
                        val k = SubmenuState.readKind()
                        (k != null && k != SubmenuState.Kind.BAG) || GameState.turnFlag() == TURN_MAIN_MENU
                    }
                    Nlog.info("wysiwyg.bagbar", "ok" to ok, "onCancelRow" to true,
                        "pocket" to pocket, "row" to from, "turn" to GameState.turnFlag())
                    if (!ok) hint(activity, "没合上背包")
                    return@Thread
                }
                // 不在最后一行：底部条是道具说明 → 还原光标，提示点「取消」行
                pressMask(EmuCore.KEY_UP, NAV_TAP_MS)
                sleep(NAV_SETTLE_MS)
                val back = if (pocket < 0) -1 else SubmenuState.bagCursor(pocket)
                Nlog.info("wysiwyg.bagbar", "ok" to false, "onCancelRow" to false,
                    "pocket" to pocket, "row" to from, "restoreRow" to back)
                hint(activity, "这条是道具说明；点「取消」行合上背包")
            } catch (e: Exception) {
                Nlog.error("wysiwyg.bagbar", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    /**
     * 滚动指示箭头（列表右侧上/下箭头）：点它 = 把列表光标挪一格（UP/DOWN），不按 A。
     * 口袋 >6 种道具时列表要滚动，这给横屏一个可见的翻列表入口；到头了只提示。
     */
    private fun scrollBag(activity: MainActivity, dir: Int) {
        if (!beginBusy()) return
        val myGen = generation
        Thread {
            try {
                if (SubmenuState.readKind() != SubmenuState.Kind.BAG) {
                    hint(activity, "没在背包里")
                    return@Thread
                }
                val pocket = SubmenuState.pocket()
                val from = if (pocket < 0) -1 else SubmenuState.bagCursor(pocket)
                if (from < 0) {
                    hint(activity, "读不到背包光标")
                    return@Thread
                }
                pressMask(if (dir < 0) EmuCore.KEY_UP else EmuCore.KEY_DOWN, NAV_TAP_MS)
                sleep(NAV_SETTLE_MS)
                if (cancelled(myGen)) return@Thread
                val to = if (pocket < 0) -1 else SubmenuState.bagCursor(pocket)
                Nlog.info(
                    "wysiwyg.bagscroll", "ok" to (to >= 0 && to != from),
                    "from" to from, "to" to to, "dir" to dir,
                )
                if (to < 0 || to == from) hint(activity, if (dir < 0) "已经到第一行了" else "已经到最后一行了")
            } catch (e: Exception) {
                Nlog.error("wysiwyg.bagscroll", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    /** 背包翻页：只按一次 LEFT/RIGHT，回读 pocket 变化；到最左/最右只提示（不按键）。 */
    private fun switchPocket(activity: MainActivity, dir: Int) {
        if (!beginBusy()) return
        val myGen = generation
        Thread {
            try {
                if (SubmenuState.readKind() != SubmenuState.Kind.BAG) {
                    hint(activity, "没在背包里")
                    return@Thread
                }
                val from = SubmenuState.pocket()
                if (from < 0) {
                    hint(activity, "读不到背包")
                    return@Thread
                }
                val to = from + dir
                if (to !in 0 until SubmenuState.POCKET_COUNT) {
                    hint(activity, if (dir < 0) "已经是最左口袋" else "已经是最右口袋")
                    return@Thread
                }
                pressMask(if (dir < 0) EmuCore.KEY_LEFT else EmuCore.KEY_RIGHT, NAV_TAP_MS)
                sleep(NAV_SETTLE_MS)
                if (cancelled(myGen)) return@Thread
                // 口袋切换动画（约 12 帧）走完才会写 pocket；窗口给到 2s。
                val ok = waitUntil(POCKET_WAIT_MS) { cancelled(myGen) || SubmenuState.pocket() == to }
                Nlog.info(
                    "wysiwyg.bagpocket", "ok" to ok, "from" to from, "to" to to,
                    "pocket" to SubmenuState.pocket(), "dir" to dir,
                )
                if (!ok) hint(activity, "口袋没翻过去")
            } catch (e: Exception) {
                Nlog.error("wysiwyg.bagpocket", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    /**
     * 点背包道具行：先回到第一行（UP 到不动），再逐行 DOWN 到第 [row] 行（每步回读），
     * 二次确认光标仍在目标行才按 A。空行/越界（光标到不了目标行）只提示、绝不按 A。
     * 回顶部再往下走可以避开列表滚动（itemsAbove≠0）导致的「看得见的行 ≠ 行号」问题。
     */
    private fun chooseBagRow(activity: MainActivity, row: Int) {
        if (!beginBusy()) return
        val myGen = generation
        Thread {
            try {
                if (SubmenuState.readKind() != SubmenuState.Kind.BAG) {
                    hint(activity, "没在背包里")
                    return@Thread
                }
                val pocket = SubmenuState.pocket()
                if (pocket < 0) {
                    hint(activity, "读不到背包")
                    return@Thread
                }
                if (SubmenuState.bagCursor(pocket) < 0) {
                    hint(activity, "读不到背包光标")
                    return@Thread
                }
                val cur = moveCursorTo(myGen, row) { SubmenuState.bagCursor(pocket) }
                if (cur != row) {
                    Nlog.warn(
                        "wysiwyg.bagitem", "ok" to false, "reason" to "cursor",
                        "pocket" to pocket, "row" to row, "cursor" to cur,
                    )
                    hint(activity, "这一行没有道具")
                    return@Thread
                }
                sleep(120)
                if (cancelled(myGen)) return@Thread
                if (SubmenuState.readKind() != SubmenuState.Kind.BAG || SubmenuState.bagCursor(pocket) != row) {
                    hint(activity, "光标没稳住")
                    return@Thread
                }
                pressMask(EmuCore.KEY_A, A_MS)
                // A 之后：用道具会关背包/弹目标选择/进入战斗处理，合上背包会关窗口。
                val ok = waitUntil(ACTION_WAIT_MS) {
                    SubmenuState.readKind() != SubmenuState.Kind.BAG ||
                        GameState.turnFlag() != TURN_MOVES_MENU || !GameState.inBattle()
                }
                Nlog.info(
                    "wysiwyg.bagitem", "ok" to ok, "pocket" to pocket, "row" to row,
                    "kind" to (SubmenuState.readKind()?.logName ?: "-"),
                    "turn" to GameState.turnFlag(),
                )
                if (!ok) hint(activity, "点了没反应")
            } catch (e: Exception) {
                Nlog.error("wysiwyg.bagitem", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    /**
     * 点队伍槽位：空位（slot ≥ 队伍数量）只提示；否则回首页逐行 DOWN 到目标槽位（每步回读），
     * 二次确认后按 A（换上场 / 作为道具目标）。读不到就停，不按 A。
     */
    private fun choosePartySlot(activity: MainActivity, slot: Int) {
        if (!beginBusy()) return
        val myGen = generation
        Thread {
            try {
                if (SubmenuState.readKind() != SubmenuState.Kind.PARTY) {
                    hint(activity, "没在队伍菜单")
                    return@Thread
                }
                val count = GameState.partyCount()
                if (count < 0) {
                    hint(activity, "读不到队伍")
                    return@Thread
                }
                if (slot !in 0 until count) {
                    Nlog.info(
                        "wysiwyg.party", "ok" to false, "reason" to "empty_slot",
                        "slot" to slot, "count" to count,
                    )
                    hint(activity, "这个位置是空的")
                    return@Thread
                }
                if (SubmenuState.partyCursor() < 0) {
                    hint(activity, "读不到队伍光标")
                    return@Thread
                }
                val cur = moveCursorTo(myGen, slot) { SubmenuState.partyCursor() }
                if (cur != slot) {
                    Nlog.warn(
                        "wysiwyg.party", "ok" to false, "reason" to "cursor",
                        "slot" to slot, "cursor" to cur,
                    )
                    hint(activity, "光标没到位")
                    return@Thread
                }
                sleep(120)
                if (cancelled(myGen)) return@Thread
                if (SubmenuState.readKind() != SubmenuState.Kind.PARTY || SubmenuState.partyCursor() != slot) {
                    hint(activity, "光标没稳住")
                    return@Thread
                }
                pressMask(EmuCore.KEY_A, A_MS)
                val ok = waitUntil(ACTION_WAIT_MS) {
                    SubmenuState.readKind() != SubmenuState.Kind.PARTY ||
                        GameState.turnFlag() != TURN_MOVES_MENU || !GameState.inBattle()
                }
                Nlog.info(
                    "wysiwyg.party", "ok" to ok, "slot" to slot,
                    "cursor" to SubmenuState.partyCursor(), "turn" to GameState.turnFlag(),
                )
                if (!ok) hint(activity, "点了没反应")
            } catch (e: Exception) {
                Nlog.error("wysiwyg.party", "err" to e.javaClass.simpleName)
            } finally {
                EmuCore.setKeys(0)
                endBusy()
            }
        }.apply { isDaemon = true }.start()
    }

    /**
     * 把列表光标挪到第 [target] 行：先 UP 到第一行（不动为止），再逐行 DOWN [target] 次。
     * 每步都回读；读不到或卡住就返回当前行（调用方据此判断是否到目标）。不按 A。
     */
    private fun moveCursorTo(myGen: Int, target: Int, read: () -> Int): Int {
        var cur = read()
        var guard = 0
        while (cur > 0 && guard < 12) {
            if (cancelled(myGen)) return -1
            pressMask(EmuCore.KEY_UP, NAV_TAP_MS)
            sleep(NAV_SETTLE_MS)
            val next = read()
            if (next < 0) return -1
            if (next == cur) break
            cur = next
            guard++
        }
        guard = 0
        while (cur in 0 until target && guard < target + 2) {
            if (cancelled(myGen)) return -1
            pressMask(EmuCore.KEY_DOWN, NAV_TAP_MS)
            sleep(NAV_SETTLE_MS)
            val next = read()
            if (next < 0) return -1
            if (next == cur) break
            cur = next
            guard++
        }
        return cur
    }

    /** 轮询 [cond]，超时返回最后一次判断结果。 */
    private fun waitUntil(timeoutMs: Long, cond: () -> Boolean): Boolean {
        val deadline = System.currentTimeMillis() + timeoutMs
        while (System.currentTimeMillis() < deadline) {
            if (cond()) return true
            sleep(VERIFY_MS)
        }
        return cond()
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
