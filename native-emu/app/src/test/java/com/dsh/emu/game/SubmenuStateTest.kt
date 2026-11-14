package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * [SubmenuState] 纯逻辑单测：背包/队伍窗口识别、口袋与光标地址映射。
 * 字节样本 = 2026-11-15 真机实测窗口（背包 win0=(11,1)18×12、队伍 win0=(1,3)10×7）。
 * 只替换 [Memo.reader] 的假实现，不加载 native 库。
 */
class SubmenuStateTest {

    /** 背包列表 win0：bg=0 (11,1) 18×12（gWindows 实测值）。 */
    private val winBag = byteArrayOf(0, 11, 1, 18, 12, 15, 0x8a.toByte(), 0, 0x78, 0xf7.toByte(), 0, 2)

    /** 队伍大框 win0：bg=0 (1,3) 10×7（gWindows 实测值）。 */
    private val winParty = byteArrayOf(0, 1, 3, 10, 7, 3, 0x63, 0, 0x6c, 1, 1, 2)

    /** 战斗招式菜单的窗口（不是子菜单）。 */
    private val winOther = byteArrayOf(0, 15, 28, 4, 0, 0x90.toByte(), 0, 0, 0x44, 0xf7.toByte(), 0, 2)

    /** 假内存：只命中给定的 (地址, 字节数组) 区段，其它读不到。 */
    private fun memReader(vararg segs: Pair<Int, ByteArray>): (Int, Int) -> ByteArray? = { addr, n ->
        segs.firstOrNull { addr >= it.first && addr + n <= it.first + it.second.size }
            ?.let { it.second.copyOfRange(addr - it.first, addr - it.first + n) }
    }

    @Test
    fun kindFromWindow_recognizesBagAndParty() {
        assertEquals(SubmenuState.Kind.BAG, SubmenuState.kindFromWindow(winBag))
        assertEquals(SubmenuState.Kind.PARTY, SubmenuState.kindFromWindow(winParty))
        assertNull(SubmenuState.kindFromWindow(winOther))
    }

    @Test
    fun kindFromWindow_rejectsBadInput() {
        assertNull(SubmenuState.kindFromWindow(null))
        assertNull(SubmenuState.kindFromWindow(ByteArray(3)))          // 不够长
        // bg 不是 0（窗口已释放/异常）：即使几何像背包也不认
        assertNull(SubmenuState.kindFromWindow(winBag.copyOf().also { it[0] = 0xFF.toByte() }))
        // 几何差 1 tile 也不认（不猜）
        assertNull(SubmenuState.kindFromWindow(winBag.copyOf().also { it[3] = 17.toByte() }))
    }

    @Test
    fun kindFromWindow_doubleAndMultiLayoutsNotSingle() {
        // 双打/多人布局 win0=(1,1)10×7（sDoublePartyMenuWindowTemplate / sMultiPartyMenuWindowTemplate）：
        // 本版只标定了 SINGLE，识别不了就返回 null，横屏只能点底部取消（不会错按）
        assertNull(SubmenuState.kindFromWindow(byteArrayOf(0, 1, 1, 10, 7, 3, 0x63, 0, 0x6c, 1, 1, 2)))
    }

    @Test
    fun partyCursor_slotConfirmIsNotSelectable() {
        val original = Memo.reader
        Memo.reader = memReader(Addresses.PARTY_CURSOR to byteArrayOf(6))   // SLOT_CONFIRM(6)
        try {
            assertEquals(-1, SubmenuState.partyCursor())
        } finally {
            Memo.reader = original
        }
    }

    @Test
    fun readKind_readsFirstWindowOnly() {
        val original = Memo.reader
        Memo.reader = memReader(Addresses.WINDOWS to winBag)
        try {
            assertEquals(SubmenuState.Kind.BAG, SubmenuState.readKind())
        } finally {
            Memo.reader = original
        }
    }

    @Test
    fun readKind_battleMoveMenuIsNotSubmenu() {
        val original = Memo.reader
        Memo.reader = memReader(Addresses.WINDOWS to winOther)
        try {
            assertNull(SubmenuState.readKind())
        } finally {
            Memo.reader = original
        }
    }

    /**
     * 背包状态：location=5(battle)、bagOpen=1、pocket=1；
     * 可视行 3/1/0（+8..），滚动偏移 2/0/1（+14..）。
     * 布局与真机标定一致：+8/+10/+12 行、+14/+16/+18 滚动偏移。
     */
    private val bagState = byteArrayOf(
        0, 0, 0, 0,          // +0 bagCallback
        5, 1,                // +4 location / +5 bagOpen
        1, 0,                // +6 pocket = 1
        3, 0,                // +8  口袋 0 可视行 = 3
        1, 0,                // +10 口袋 1 可视行 = 1
        0, 0,                // +12 口袋 2 可视行 = 0
        2, 0,                // +14 口袋 0 滚动偏移 = 2
        0, 0,                // +16 口袋 1 滚动偏移 = 0
        1, 0,                // +18 口袋 2 滚动偏移 = 1
    )

    @Test
    fun pocketRowAndScroll_perPocketSlots() {
        val original = Memo.reader
        Memo.reader = memReader(Addresses.BAG_MENU_STATE to bagState)
        try {
            assertEquals(1, SubmenuState.pocket())
            assertEquals(3, SubmenuState.bagRow(0))
            assertEquals(1, SubmenuState.bagRow(1))
            assertEquals(0, SubmenuState.bagRow(2))
            assertEquals(2, SubmenuState.bagScroll(0))
            assertEquals(0, SubmenuState.bagScroll(1))
            assertEquals(1, SubmenuState.bagScroll(2))
            // 绝对行 = 滚动偏移 + 可视行（真机：>6 件道具时 DOWN 会滚窗口，abs 才单调 +1）
            assertEquals(5, SubmenuState.bagAbs(0))
            assertEquals(1, SubmenuState.bagAbs(1))
            assertEquals(1, SubmenuState.bagAbs(2))
        } finally {
            Memo.reader = original
        }
    }

    @Test
    fun pocket_badValueReturnsMinusOne() {
        val original = Memo.reader
        Memo.reader = memReader(Addresses.BAG_POCKET to byteArrayOf(7))
        try {
            assertEquals(-1, SubmenuState.pocket())
            assertEquals(-1, SubmenuState.bagRow(7))      // 口袋越界不读地址
            assertEquals(-1, SubmenuState.bagScroll(7))
        } finally {
            Memo.reader = original
        }
    }

    @Test
    fun bagRow_badValueReturnsMinusOne() {
        val original = Memo.reader
        Memo.reader = memReader(Addresses.BAG_ROW_BASE to byteArrayOf(9))
        try {
            assertEquals(-1, SubmenuState.bagRow(0))      // > 5 行，不猜
            assertEquals(-1, SubmenuState.bagAbs(0))      // row 读不到 → abs 也 fail-closed
        } finally {
            Memo.reader = original
        }
    }

    @Test
    fun bagAbs_unreadableScrollReturnsMinusOne() {
        val original = Memo.reader
        // 只给 row、不给 scroll 区 → abs 必须失败（否则会拿错行按 A）
        Memo.reader = memReader(Addresses.BAG_ROW_BASE to byteArrayOf(2))
        try {
            assertEquals(2, SubmenuState.bagRow(0))
            assertEquals(-1, SubmenuState.bagScroll(0))
            assertEquals(-1, SubmenuState.bagAbs(0))
        } finally {
            Memo.reader = original
        }
    }

    @Test
    fun partyCursor_acceptsSlotsAndCancel() {
        val original = Memo.reader
        try {
            Memo.reader = memReader(Addresses.PARTY_CURSOR to byteArrayOf(0))
            assertEquals(0, SubmenuState.partyCursor())
            Memo.reader = memReader(Addresses.PARTY_CURSOR to byteArrayOf(5))
            assertEquals(5, SubmenuState.partyCursor())
            Memo.reader = memReader(Addresses.PARTY_CURSOR to byteArrayOf(SubmenuState.PARTY_CANCEL.toByte()))
            assertEquals(SubmenuState.PARTY_CANCEL, SubmenuState.partyCursor())
            Memo.reader = memReader(Addresses.PARTY_CURSOR to byteArrayOf(9))
            assertEquals(-1, SubmenuState.partyCursor())
        } finally {
            Memo.reader = original
        }
    }

    @Test
    fun allUnreadableReturnsMinusOne() {
        val original = Memo.reader
        Memo.reader = { _, _ -> null }
        try {
            assertNull(SubmenuState.readKind())
            assertEquals(-1, SubmenuState.pocket())
            assertEquals(-1, SubmenuState.bagRow(0))
            assertEquals(-1, SubmenuState.bagScroll(0))
            assertEquals(-1, SubmenuState.bagAbs(0))
            assertEquals(-1, SubmenuState.partyCursor())
        } finally {
            Memo.reader = original
        }
    }
}
