package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** 离线单测：用内存镜像替换 JNI 读取。 */
class GameStateTest {

    private val memory = HashMap<Int, Byte>()

    private fun put(addr: Int, vararg bytes: Int) {
        bytes.forEachIndexed { i, b -> memory[addr + i] = b.toByte() }
    }

    private fun putU16(addr: Int, v: Int) {
        put(addr, v and 0xFF, (v shr 8) and 0xFF)
    }

    @Before
    fun setUp() {
        memory.clear()
        Memo.reader = { addr, n ->
            ByteArray(n) { i -> memory[addr + i] ?: 0 }
        }
    }

    @Test
    fun coordsSubTractTileOffset() {
        putU16(Addresses.X_ADDR, 20)
        putU16(Addresses.Y_ADDR, 15)
        val c = GameState.coords()!!
        assertEquals(13, c.x)   // 20 - 7
        assertEquals(8, c.y)    // 15 - 7
    }

    @Test
    fun battleFlagAndTurn() {
        put(Addresses.BATTLE_FLAG, 1)
        put(Addresses.TURN_FLAG, 1)
        assertTrue(GameState.inBattle())
        assertEquals("battle_main", GameState.scene())
        assertEquals(1, GameState.turnFlag())
    }

    @Test
    fun mapSceneWhenNotInBattle() {
        put(Addresses.BATTLE_FLAG, 0)
        assertEquals("map", GameState.scene())
        assertFalse(GameState.inBattle())
    }

    @Test
    fun moveScene() {
        put(Addresses.BATTLE_FLAG, 1)
        put(Addresses.TURN_FLAG, 2)
        assertEquals("battle_moves", GameState.scene())
    }

    @Test
    fun partySkipsEmptySlots() {
        val base = Addresses.PARTY_ADDR
        // 第 0 只：Lv10 HP 29/29
        memory[base + Addresses.PARTY_LV] = 10.toByte()
        putU16(base + Addresses.PARTY_HP, 29)
        putU16(base + Addresses.PARTY_HP + 2, 29)
        memory[base + Addresses.PARTY_PID] = 1
        // 第 1 只：空（等级 0）
        val mon = GameState.party()
        assertEquals(1, mon.size)
        assertEquals(10, mon[0].lv)
        assertEquals(29, mon[0].hp)
        assertEquals(29, mon[0].maxHp)
        assertEquals(0, mon[0].slot)
    }

    @Test
    fun partyReadsTwoMon() {
        val base = Addresses.PARTY_ADDR
        for (i in 0..1) {
            val o = base + i * Addresses.PARTY_STRIDE
            memory[o + Addresses.PARTY_LV] = (10 + i).toByte()
            putU16(o + Addresses.PARTY_HP, 20 + i)
            putU16(o + Addresses.PARTY_HP + 2, 30)
        }
        val mon = GameState.party()
        assertEquals(2, mon.size)
        assertEquals(10, mon[0].lv)
        assertEquals(11, mon[1].lv)
        assertEquals(1, mon[1].slot)
    }

    @Test
    fun myMovesReadsFourU16() {
        val base = Addresses.MY_BATTLE + 0x0C
        putU16(base, 10)
        putU16(base + 2, 45)
        putU16(base + 4, 52)
        putU16(base + 6, 0)
        assertEquals(listOf(10, 45, 52, 0), GameState.myMoves())
    }

    @Test
    fun species() {
        putU16(Addresses.MY_BATTLE, 4)
        putU16(Addresses.EN_BATTLE, 16)
        assertEquals(4, GameState.mySpecies())
        assertEquals(16, GameState.enemySpecies())
    }

    @Test
    fun facingValidRange() {
        memory[Addresses.FACING_ADDR] = 2.toByte()
        assertEquals(2, GameState.facing())
        memory[Addresses.FACING_ADDR] = 9.toByte()
        assertEquals(-1, GameState.facing())
    }

    @Test
    fun coordsNullWhenShortRead() {
        Memo.reader = { _, n -> null }
        assertNull(GameState.coords())
    }
}
