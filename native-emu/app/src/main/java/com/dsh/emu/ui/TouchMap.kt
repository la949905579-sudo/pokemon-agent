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

    /** 玩家脚下 tile 中心在屏幕上的位置（LeafGreen 镜头锚点；实测标定值）。 */
    const val ANCHOR_X = 120
    const val ANCHOR_Y = 88

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
     * 战斗主菜单「战斗」热区。v1 只支持点「战斗」开招式菜单（点其它项回读不了成功，
     * 按 fail-closed 不盲按 A）；热区取底部左侧的宽区，保证命中真实「战斗」按钮。
     */
    val FIGHT_ZONE = Zone(0, 104, 120, 160)

    /** 对话/文本框区域：屏幕下半部（点=推进一句）。 */
    val DIALOG_ZONE = Zone(0, 104, GAME_W, GAME_H)

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

    /** 是否点在战斗主菜单「战斗」上。 */
    fun isFightTap(x: Int, y: Int): Boolean = FIGHT_ZONE.hit(x, y)

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
