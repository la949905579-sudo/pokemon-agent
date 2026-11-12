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

    private fun putU32(addr: Int, v: Long) {
        put(addr, (v and 0xFF).toInt(), ((v shr 8) and 0xFF).toInt(),
            ((v shr 16) and 0xFF).toInt(), ((v shr 24) and 0xFF).toInt())
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
    fun enemyInfoReadsHp() {
        val base = Addresses.ENEMY_BASE
        memory[base] = 5.toByte()          // lv 5
        putU16(base + 2, 20)               // hp 20
        putU16(base + 4, 22)               // max 22
        putU16(Addresses.EN_BATTLE, 16)    // species 16
        val e = GameState.enemyInfo()!!
        assertEquals(5, e.lv)
        assertEquals(20, e.hp)
        assertEquals(22, e.maxHp)
        assertEquals(16, e.species)
    }

    @Test
    fun enemyInfoNullWhenEmpty() {
        Memo.reader = { _, n -> ByteArray(n) }
        assertNull(GameState.enemyInfo())
    }

    @Test
    fun speciesNames() {
        assertEquals("妙蛙种子", com.dsh.emu.game.Species.nameOf(1))
        assertEquals("小火龙", com.dsh.emu.game.Species.nameOf(4))
        assertEquals("梦幻", com.dsh.emu.game.Species.nameOf(151))
        assertEquals("#999", com.dsh.emu.game.Species.nameOf(999))
    }

    @Test
    fun mapWalkerFindsPath() {
        // 3x3 全通行，从 (0,0) 到 (2,2) 应 4 步
        val tiles = List(3) { List(3) { 1 } }
        val p = com.dsh.emu.game.MapWalker.path(tiles, com.dsh.emu.game.MapWalker.Point(0, 0),
            com.dsh.emu.game.MapWalker.Point(2, 2))
        assertEquals(4, p!!.size)
    }

    @Test
    fun mapWalkerBlocked() {
        // 中间一堵墙
        val tiles = listOf(
            listOf(1, 0, 1),
            listOf(1, 0, 1),
            listOf(1, 0, 1),
        )
        assertNull(com.dsh.emu.game.MapWalker.path(tiles,
            com.dsh.emu.game.MapWalker.Point(0, 0), com.dsh.emu.game.MapWalker.Point(2, 0)))
    }

    @Test
    fun mapWalkerSamePoint() {
        val tiles = List(3) { List(3) { 1 } }
        val p = com.dsh.emu.game.MapWalker.path(tiles,
            com.dsh.emu.game.MapWalker.Point(1, 1), com.dsh.emu.game.MapWalker.Point(1, 1))
        assertEquals(0, p!!.size)
    }

    @Test
    fun partyDetailReadsTypesMovesPpExp() {
        val base = Addresses.PARTY_ADDR
        memory[base + Addresses.PARTY_LV] = 12.toByte()
        putU16(base + Addresses.PARTY_HP, 35)
        putU16(base + Addresses.PARTY_HP + 2, 35)
        // PID/OTID 都是 0 → 异或 key = 0；顺序表第 0 项 "GAEM"：G 在 0，A 在 12
        putU16(base + 0x20, 25)        // species 皮卡丘
        putU32(base + 0x20 + 4, 1234)  // 经验
        putU16(base + 0x20 + 12, 84)   // 电击
        putU16(base + 0x20 + 14, 86)   // 电磁波
        memory[base + 0x20 + 20] = 30  // 电击 PP
        memory[base + 0x20 + 21] = 20  // 电磁波 PP
        val m = GameState.party().single()
        assertEquals(25, m.species)
        assertEquals("皮卡丘", m.name)
        assertEquals(listOf("电"), m.types)
        assertEquals(listOf(84, 86, 0, 0), m.moves)
        assertEquals(listOf(30, 20, 0, 0), m.pp)
        assertEquals(1234L, m.exp)
    }

    @Test
    fun speciesTypesKnownAndMissing() {
        assertEquals(listOf("草", "毒"), Species.typesOf(1))
        assertEquals(listOf("一般", "飞行"), Species.typesOf(16))
        assertEquals(listOf("超能力"), Species.typesOf(151))
        assertTrue(Species.typesOf(0).isEmpty())
        assertTrue(Species.typesOf(152).isEmpty())
    }

    @Test
    fun coordsNullWhenShortRead() {
        Memo.reader = { _, n -> null }
        assertNull(GameState.coords())
    }
}
