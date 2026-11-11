package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class BattleDeciderTest {

    @Test
    fun fireBeatsGrass() {
        // 火花(52) 对 草 应 2 倍
        val eff = BattleDecider.effect(52, listOf("草"))
        assertEquals(2.0, eff, 0.001)
    }

    @Test
    fun waterResistsFire() {
        // 水枪(55) 对 火 是 2 倍
        assertEquals(2.0, BattleDecider.effect(55, listOf("火")), 0.001)
        // 火花打水是 0.5
        assertEquals(0.5, BattleDecider.effect(52, listOf("水")), 0.001)
    }

    @Test
    fun unknownMoveIsNeutral() {
        assertEquals(1.0, BattleDecider.effect(99999, listOf("草")), 0.001)
    }

    @Test
    fun choosesSuperEffectiveMove() {
        // 招式 10(抓/一般/40) vs 52(火花/火/40) 打草 → 火花 2 倍胜出
        val c = BattleDecider.chooseMove(listOf(10, 52, 0, 0), listOf(10, 10, 0, 0), listOf("草"))!!
        assertEquals(1, c.index)
        assertEquals(52, c.moveId)
        assertEquals("火花", c.name)
    }

    @Test
    fun skipsZeroPpAndEmptySlots() {
        // 火花 pp=0 应跳过，选抓
        val c = BattleDecider.chooseMove(listOf(10, 52, 0, 0), listOf(10, 0, 0, 0), listOf("草"))!!
        assertEquals(10, c.moveId)
    }

    @Test
    fun returnsNullWhenNoUsableMove() {
        assertNull(BattleDecider.chooseMove(listOf(0, 0, 0, 0), listOf(0, 0, 0, 0), listOf("草")))
        assertNull(BattleDecider.chooseMove(listOf(10), listOf(0), listOf("草")))
    }

    @Test
    fun higherPowerWinsOnNeutral() {
        // 抓(40) vs 撞击(33)：同一倍率下抓分高
        val c = BattleDecider.chooseMove(listOf(33, 10, 0, 0), listOf(10, 10, 0, 0), emptyList())!!
        assertEquals(10, c.moveId)
    }
}
