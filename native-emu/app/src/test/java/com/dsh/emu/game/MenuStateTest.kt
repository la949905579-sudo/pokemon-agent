package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * [MenuState] 纯逻辑单测：sMenu/gWindows 字节解析、标准是/否框识别、选项行命中。
 * 字节样本 = 2026-11-14 真机存档「是/否」框实测值（sMenu @0x0203ADE4、gWindows[2]）。
 */
class MenuStateTest {

    /** sMenu：left=0 top=2 cursorPos=0 min=0 max=1 windowId=2 font=2 optW=0 optH=14 cols=0 rows=0 muted=0 */
    private val menuYes = byteArrayOf(0, 2, 0, 0, 1, 2, 2, 0, 14, 0, 0, 0)

    /** gWindows[2]：bg=0 tilemapLeft=21 tilemapTop=9 w=6 h=4 pal=15 baseBlock=0x0125 tileData=ptr */
    private val winYes = byteArrayOf(0, 21, 9, 6, 4, 15, 0x25, 0x01, 0x30, 0x3d, 0x00, 0x02)

    private fun profile() = MenuState.fromBytes(menuYes, winYes)!!

    private fun menuWith(cursor: Int = 0, max: Int = 1, winId: Int = 2, optH: Int = 14, left: Int = 0, top: Int = 2) =
        byteArrayOf(left.toByte(), top.toByte(), cursor.toByte(), 0, max.toByte(), winId.toByte(), 2, 0, optH.toByte(), 0, 0, 0)

    private fun winWith(bg: Int = 0, l: Int = 21, t: Int = 9, w: Int = 6, h: Int = 4) =
        byteArrayOf(bg.toByte(), l.toByte(), t.toByte(), w.toByte(), h.toByte(), 15, 0x25, 0x01, 0x30, 0x3d, 0, 2)

    @Test
    fun parsesObservedYesNoMenu() {
        val p = profile()
        assertEquals(0, p.cursorPos)
        assertEquals(2, p.count)
        assertEquals(2, p.windowId)
        assertEquals(0, p.left)
        assertEquals(2, p.top)
        assertEquals(14, p.optionHeight)
        assertEquals(21, p.winLeft)
        assertEquals(9, p.winTop)
        assertEquals(6, p.winWidth)
        assertEquals(4, p.winHeight)
    }

    @Test
    fun rejectsInvalidWindowId() {
        assertNull(MenuState.fromBytes(menuWith(winId = MenuState.WINDOW_MAX), winYes))
        assertNull(MenuState.fromBytes(menuWith(winId = 0xFF), winYes))
    }

    @Test
    fun rejectsDestroyedWindowOrBadFields() {
        assertNull(MenuState.fromBytes(menuYes, winWith(bg = 0xFF)))   // 窗口已销毁（dummy）
        assertNull(MenuState.fromBytes(menuYes, winWith(w = 0)))      // 宽 0
        assertNull(MenuState.fromBytes(menuYes, winWith(h = 0)))
        assertNull(MenuState.fromBytes(menuWith(optH = 0), winYes))   // 行高非法
        assertNull(MenuState.fromBytes(menuWith(optH = 40), winYes))
        assertNull(MenuState.fromBytes(menuWith(max = 8), winYes))    // 选项数 > 8
        assertNull(MenuState.fromBytes(ByteArray(4), winYes))         // 短数据
    }

    @Test
    fun isStandardYesNoMatchesObserved() {
        assertTrue(MenuState.isStandardYesNo(profile()))
    }

    @Test
    fun isStandardYesNoRejectsOtherMenus() {
        // 窗口挪了位置 / 选项数不是 2 / 行高不同 → 不当是/否处理
        assertFalse(MenuState.isStandardYesNo(profile().copy(winLeft = 20)))
        assertFalse(MenuState.isStandardYesNo(profile().copy(winTop = 8)))
        assertFalse(MenuState.isStandardYesNo(profile().copy(count = 3)))
        assertFalse(MenuState.isStandardYesNo(profile().copy(optionHeight = 16)))
        assertFalse(MenuState.isStandardYesNo(profile().copy(winWidth = 5)))
    }

    @Test
    fun optionRowsFollowWindowAndLineHeight() {
        val p = profile()
        assertEquals(9 * 8 + 2, MenuState.optionRowTop(p, 0))   // 74
        assertEquals(9 * 8 + 2 + 14, MenuState.optionRowTop(p, 1)) // 88
    }

    @Test
    fun optionIndexAt_hitsRowsAndRejectsOutside() {
        val p = profile()
        assertEquals(0, MenuState.optionIndexAt(p, 200, 74))
        assertEquals(0, MenuState.optionIndexAt(p, 200, 87))
        assertEquals(1, MenuState.optionIndexAt(p, 200, 88))
        assertEquals(1, MenuState.optionIndexAt(p, 200, 101))
        assertNull(MenuState.optionIndexAt(p, 200, 73))    // 行上方
        assertNull(MenuState.optionIndexAt(p, 200, 102))   // 行下方
        assertNull(MenuState.optionIndexAt(p, 159, 80))    // 窗框左外
        assertNull(MenuState.optionIndexAt(p, 224, 80))    // 窗框右外
        assertEquals(0, MenuState.optionIndexAt(p, 160, 80)) // 窗框内左沿
        assertEquals(0, MenuState.optionIndexAt(p, 223, 80)) // 窗框内右沿（y=80 属于行 0）
        assertEquals(1, MenuState.optionIndexAt(p, 223, 95)) // 右沿 + 行 1
    }

    @Test
    fun genericThreeOptionRows() {
        val p = MenuState.fromBytes(menuWith(max = 2, winId = 3, optH = 14, top = 2), winWith(w = 8, h = 5))!!
        // 这里只验证行换算（窗口位置同实测的 21,9）
        assertEquals(listOf(74, 88, 102), (0..2).map { MenuState.optionRowTop(p, it) })
        assertEquals(2, MenuState.optionIndexAt(p, 200, 110))
    }

    @Test
    fun stepDirection() {
        assertEquals(1, MenuState.step(0, 1))
        assertEquals(-1, MenuState.step(1, 0))
        assertEquals(0, MenuState.step(1, 1))
        assertEquals(1, MenuState.step(1, 3))
        assertEquals(-1, MenuState.step(3, 1))
    }
}
