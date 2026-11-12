package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * 招式菜单适配层离线单测：只替换 [Memo.reader] 的假实现，不加载 native 库、不碰实机。
 *
 * 覆盖：三个地址的读取映射；读不到统一 -1（fail-closed 交给 [MoveCaster]）。
 */
class BattleMoveMenuTest {

    /** 假内存：地址 → 首字节值；未收录的地址读不到（null）。 */
    private fun readerOf(values: Map<Int, Int>): (Int, Int) -> ByteArray? = { addr, n ->
        val v = values[addr]
        if (v == null) null else ByteArray(n) { i -> if (i == 0) v.toByte() else 0.toByte() }
    }

    @Test
    fun readsMenuStateFromAddresses() {
        val original = Memo.reader
        Memo.reader = readerOf(
            mapOf(
                Addresses.TURN_FLAG to 2,
                Addresses.MAIN_CURSOR to 0,
                Addresses.MOVE_CURSOR to 3,
            )
        )
        try {
            assertEquals(2, BattleMoveMenu.readTurn())
            assertEquals(0, BattleMoveMenu.readMainCursor())
            assertEquals(3, BattleMoveMenu.readMoveCursor())
        } finally {
            Memo.reader = original
        }
    }

    @Test
    fun unreadableReturnsMinusOne() {
        val original = Memo.reader
        Memo.reader = readerOf(emptyMap())
        try {
            assertEquals(-1, BattleMoveMenu.readTurn())
            assertEquals(-1, BattleMoveMenu.readMainCursor())
            assertEquals(-1, BattleMoveMenu.readMoveCursor())
        } finally {
            Memo.reader = original
        }
    }
}
