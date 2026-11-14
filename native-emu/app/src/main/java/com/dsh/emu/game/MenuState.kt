package com.dsh.emu.game

/**
 * 对话/菜单「选项光标」的只读适配层（2026-11-14 真机实测标定）。
 *
 * 叶绿/火红的通用菜单状态在 `sMenu`（menu.c 的 `static struct Menu`）里：
 * `cursorPos`（当前光标）、`maxCursorPos+1`（选项数）、`windowId`、行高与文字偏移；
 * `gWindows[windowId]`（window.c）给出窗口在屏幕上的 tile 位置和宽高（1 tile = 8px）。
 * 两者都是固定 EWRAM 地址（见 [Addresses.MENU_STATE] / [Addresses.WINDOWS]）。
 *
 * 只读：不做按键、不做重试；场景判断与操纵在 `ui/Wysiwyg`（fail-closed）。
 * 单测用 [fromBytes] 注入原始字节，不碰 native 库。
 */
object MenuState {

    const val WINDOW_MAX = 32
    const val TILE_PX = 8

    /** 当前菜单快照（字段顺序同 sMenu/Window）。 */
    data class Profile(
        val cursorPos: Int,
        val count: Int,
        val windowId: Int,
        val left: Int,
        val top: Int,
        val optionHeight: Int,
        val winLeft: Int,
        val winTop: Int,
        val winWidth: Int,
        val winHeight: Int,
    )

    /**
     * 解析 sMenu(12B) + 对应 Window(12B)。字段不合法返回 null（读一半/菜单已销毁时不硬猜）。
     */
    fun fromBytes(menu: ByteArray, window: ByteArray): Profile? {
        if (menu.size < 12 || window.size < 12) return null
        fun u(b: ByteArray, i: Int): Int = b[i].toInt() and 0xFF
        val windowId = u(menu, 5)
        if (windowId >= WINDOW_MAX) return null
        val bg = u(window, 0)
        if (bg > 3) return null                       // 对话框/菜单都在 BG0..BG3
        val winW = u(window, 3)
        val winH = u(window, 4)
        if (winW == 0 || winH == 0) return null
        val count = u(menu, 4) + 1                    // maxCursorPos + 1
        if (count !in 1..8) return null
        val optH = u(menu, 8)
        if (optH !in 8..32) return null
        return Profile(
            cursorPos = u(menu, 2),
            count = count,
            windowId = windowId,
            left = u(menu, 0),
            top = u(menu, 1),
            optionHeight = optH,
            winLeft = u(window, 1),
            winTop = u(window, 2),
            winWidth = winW,
            winHeight = winH,
        )
    }

    /** 线上读取：sMenu → gWindows[windowId]；读不到返回 null。 */
    fun read(): Profile? {
        val menu = Memo.bytes(Addresses.MENU_STATE, 12) ?: return null
        val windowId = menu[5].toInt() and 0xFF
        if (windowId >= WINDOW_MAX) return null
        val window = Memo.bytes(Addresses.WINDOWS + windowId * 12, 12) ?: return null
        return fromBytes(menu, window)
    }

    /**
     * 标准「是/否」菜单（`DisplayYesNoMenuDefaultYes`）：窗口 BG0 (21,9) 6×4 格、
     * 2 个选项、光标行高 14、文字偏移 (0,2)。真机截图标定；不满足就不当是/否处理。
     */
    fun isStandardYesNo(p: Profile): Boolean =
        p.count == 2 && p.optionHeight == 14 && p.left == 0 && p.top == 2 &&
            p.winLeft == 21 && p.winTop == 9 && p.winWidth == 6 && p.winHeight == 4

    /** 第 [index] 个选项的文字行在屏幕上的 y 范围（tile 坐标换算成像素，右/下开区间）。 */
    fun optionRowTop(p: Profile, index: Int): Int =
        p.winTop * TILE_PX + p.top + p.optionHeight * index

    /** 选项文字行的 x 范围：整格窗口宽度（含 1 格窗框，点框内都算这一行）。 */
    fun optionXRange(p: Profile): IntRange =
        (p.winLeft - 1) * TILE_PX until (p.winLeft + p.winWidth + 1) * TILE_PX

    /** 点击游戏像素 → 选项编号；不在任何选项行/窗口范围内返回 null（不猜）。 */
    fun optionIndexAt(p: Profile, x: Int, y: Int): Int? {
        if (x !in optionXRange(p)) return null
        for (i in 0 until p.count) {
            val top = optionRowTop(p, i)
            if (y >= top && y < top + p.optionHeight) return i
        }
        return null
    }

    /** 从 [from] 到 [to] 的竖向一步（-1=UP / +1=DOWN）；无需移动返回 0。 */
    fun step(from: Int, to: Int): Int = when {
        to > from -> 1
        to < from -> -1
        else -> 0
    }
}
