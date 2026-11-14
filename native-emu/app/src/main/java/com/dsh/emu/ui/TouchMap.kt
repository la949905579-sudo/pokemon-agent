package com.dsh.emu.ui

/**
 * 横屏「触屏所见即所得」的坐标映射与固定热区表（纯逻辑，可单测）。
 *
 * 分三层：
 *  1. 视图像素 → 游戏像素：EmuView 等比居中（letterbox）渲染的逆变换；
 *  2. 游戏像素 → 场景热区：固定热区表（FireRed/叶绿 240×160 界面，真机截图实测标定）；
 *  3. 游戏像素 → 地图目标格:镜头把玩家脚下 tile 保持在屏幕锚点，按 16px 换算（同图，越界返回 null）。
 *
 * 热区表只在本文件维护；场景判断、回读与按键在 [Wysiwyg]（fail-closed）。
 * 布局前提：ROM 菜单布局固定（叶绿 2024 官译修正版实测），换 ROM / 改分辨率需重新标定。
 */
internal object TouchMap {

    const val GAME_W = 240
    const val GAME_H = 160

    /** 一个 tile 的像素。 */
    const val TILE_PX = 16

    /** 玩家脚下 tile 中心在屏幕上的位置（真机标定：BG 滚动 (208,248) → tile 边界 y≡8 mod 16，
     *  玩家精灵脚底落在 y=88 的 tile 边界上 → tile 72..88，中心 80；x 居中 120）。 */
    const val ANCHOR_X = 120
    const val ANCHOR_Y = 80

    /** 游戏内像素点（可带小数）。 */
    data class Point(val x: Float, val y: Float)

    /** 轴对齐热区，右/下开区间。 */
    data class Zone(val l: Int, val t: Int, val r: Int, val b: Int) {
        fun hit(x: Int, y: Int): Boolean = x >= l && x < r && y >= t && y < b
        val cx: Int get() = (l + r) / 2
        val cy: Int get() = (t + b) / 2
    }

    /**
     * 招式菜单 2×2 四格（编号同 [com.dsh.emu.game.MoveCaster]：0=左上 1=右上 2=左下 3=右下）。
     * 标定依据：真机截图里菜单窗口 y=112..159、招式列表 x=0..157，右列 PP/属性窗从 x=157 起。
     */
    val MOVE_ZONES: List<Zone> = listOf(
        Zone(4, 114, 78, 136),    // 0 左上
        Zone(82, 114, 155, 136),  // 1 右上
        Zone(4, 136, 78, 157),    // 2 左下
        Zone(82, 136, 155, 157),  // 3 右下
    )

    /**
     * 战斗主菜单 2×2（编号同 [BattleMoveMenu] 的 MAIN_CURSOR：0=战斗 1=背包 2=宝可梦 3=逃跑）。
     * 标定依据：真机截图里选项窗口 x=120..239、y=112..159；2×2 分格见下。
     * v1 只接「战斗」（其它项没有可靠回读，按 fail-closed 只提示不按键）。
     */
    val MAIN_ZONES: List<Zone> = listOf(
        Zone(122, 114, 180, 136),  // 0 战斗（左上）
        Zone(180, 114, 236, 136),  // 1 背包（右上）
        Zone(122, 136, 180, 156),  // 2 宝可梦（左下）
        Zone(180, 136, 236, 156),  // 3 逃跑（右下）
    )

    /** 战斗主菜单项名字（提示文案用）。 */
    val MAIN_NAMES: List<String> = listOf("战斗", "背包", "宝可梦", "逃跑")

    /** 对话/文本框区域：屏幕下半部（点=推进一句）。 */
    val DIALOG_ZONE = Zone(0, 104, GAME_W, GAME_H)

    /**
     * 战斗子菜单底部取消条（横屏没有 B 键，点这条 = 按 B 取消，避免被困在子菜单里）。
     * 分开标定，避免把背包列表 / 队伍格子的下半屏点击误当成取消：
     * - 背包底部条（「合上背包」/道具说明）：真机实测 y≥114；窗口 win1=(5,14) 25×6 → y=112..160；
     * - 队伍底部条（「取消」按钮 + 消息条）：取消按钮 win7=(24,17) 6×2 → x=192..240、y=136..152；
     *   第 5 行格子到 y=127 为止，所以取消区从 136 起、不抢格子点击。
     */
    val BAG_CANCEL_ZONE = Zone(0, 114, GAME_W, GAME_H)
    val PARTY_CANCEL_ZONE = Zone(0, 136, GAME_W, GAME_H)

    // ---------- 战斗背包（2026-11-15 真机标定） ----------

    /** 背包翻页箭头 ◀/▶：真机截图量得中心 (8,72) / (72,72)，箭头 16×16。 */
    val BAG_LEFT_ARROW_ZONE = Zone(0, 60, 22, 84)
    val BAG_RIGHT_ARROW_ZONE = Zone(58, 60, 86, 84)

    /**
     * 道具列表窗口 win0=(11,1) 18×12：内区 x=88..232、y=8..104。
     * 行高 = 字体最大高度 14 + itemVerticalPadding 2 = 16（list_menu.c）；一屏最多 6 行。
     */
    const val BAG_LIST_LEFT = 88
    const val BAG_LIST_RIGHT = 232
    const val BAG_ROW_TOP = 8
    const val BAG_ROW_H = 16
    const val BAG_MAX_ROWS = 6

    /**
     * 背包列表右侧滚动指示箭头（item_menu.c `CreatePocketScrollArrowPair`：中心 (160,8)/(160,104)、16×16）。
     * 口袋超过 6 种道具时出现；游戏里只是指示器不是按钮，横屏里点它=把光标挪一格更直观。
     */
    val BAG_SCROLL_UP_ZONE = Zone(152, 0, 168, 16)
    val BAG_SCROLL_DOWN_ZONE = Zone(152, 96, 168, 112)

    /** 点击点 → 道具列表行号 0..5；不在列表窗口内 / 落在滚动箭头上返回 null（不选行、不按 A）。 */
    fun bagRowAt(x: Int, y: Int): Int? {
        if (x !in BAG_LIST_LEFT until BAG_LIST_RIGHT) return null
        if (y !in BAG_ROW_TOP until BAG_ROW_TOP + BAG_ROW_H * BAG_MAX_ROWS) return null
        if (BAG_SCROLL_UP_ZONE.hit(x, y) || BAG_SCROLL_DOWN_ZONE.hit(x, y)) return null
        return (y - BAG_ROW_TOP) / BAG_ROW_H
    }

    // ---------- 战斗队伍（PARTY_LAYOUT_SINGLE，2026-11-15 真机标定） ----------

    /**
     * 队伍菜单：第 1 只独占左侧大框 win0=(1,3) 10×7 → x=8..88、y=24..80；
     * 第 2..6 只各占右侧一行 win1..5=(12,1/4/7/10/13) 18×3 → x=96..240，行高 24。
     */
    val PARTY_SLOT0_ZONE = Zone(8, 24, 88, 80)
    private val PARTY_ROW_ZONES = List(5) { i -> Zone(96, 8 + 24 * i, GAME_W, 8 + 24 * (i + 1)) }

    /** 点击点 → 队伍槽位 0..5；不在任何格子内返回 null。 */
    fun partySlotAt(x: Int, y: Int): Int? {
        if (PARTY_SLOT0_ZONE.hit(x, y)) return 0
        val row = PARTY_ROW_ZONES.indexOfFirst { it.hit(x, y) }
        return if (row >= 0) row + 1 else null
    }

    /**
     * 是否点在战斗子菜单底部取消条上。[menuMain] 是 MAIN_CURSOR（1=背包 2=队伍）；
     * 其它值一律不算，避免把招式菜单/其它菜单的点击当取消。
     */
    fun isSubmenuCancelTap(menuMain: Int, x: Int, y: Int): Boolean = when (menuMain) {
        1 -> BAG_CANCEL_ZONE.hit(x, y)
        2 -> PARTY_CANCEL_ZONE.hit(x, y)
        else -> false
    }

    /** 视图像素 → 游戏像素；落在游戏画面外（黑边）返回 null。 */
    fun viewToGame(
        viewW: Int, viewH: Int, x: Float, y: Float,
        gw: Int = GAME_W, gh: Int = GAME_H,
    ): Point? {
        if (viewW <= 0 || viewH <= 0 || gw <= 0 || gh <= 0) return null
        val scale = minOf(viewW.toFloat() / gw, viewH.toFloat() / gh)
        if (scale <= 0f) return null
        val dw = gw * scale
        val dh = gh * scale
        val ox = (viewW - dw) / 2f
        val oy = (viewH - dh) / 2f
        val gx = (x - ox) / scale
        val gy = (y - oy) / scale
        if (gx < 0f || gy < 0f || gx >= gw || gy >= gh) return null
        return Point(gx, gy)
    }

    /** 招式格编号 0..3；不在四格内返回 null（不猜）。 */
    fun moveIndexAt(x: Int, y: Int): Int? =
        MOVE_ZONES.indexOfFirst { it.hit(x, y) }.takeIf { it >= 0 }

    /** 战斗主菜单项编号 0..3；不在选项窗口内返回 null。 */
    fun mainMenuIndexAt(x: Int, y: Int): Int? =
        MAIN_ZONES.indexOfFirst { it.hit(x, y) }.takeIf { it >= 0 }

    /** 是否点在对话框上（推进对话）。 */
    fun isDialogTap(x: Int, y: Int): Boolean = DIALOG_ZONE.hit(x, y)

    /**
     * 点击地图位置 → 目标 tile（同图内）。
     * 玩家脚下 tile 中心在屏幕锚点 (ANCHOR_X, ANCHOR_Y)，故：
     *   目标 = 玩家 + round((点击像素 - 锚点) / 16)
     * 目标越出地图范围返回 null —— 不夹到边界、也不盲走。
     */
    fun mapTarget(fromX: Int, fromY: Int, gx: Int, gy: Int, w: Int, h: Int): Pair<Int, Int>? {
        if (w <= 0 || h <= 0) return null
        val tx = fromX + Math.round((gx - ANCHOR_X) / TILE_PX.toFloat())
        val ty = fromY + Math.round((gy - ANCHOR_Y) / TILE_PX.toFloat())
        if (tx !in 0 until w || ty !in 0 until h) return null
        return tx to ty
    }
}
