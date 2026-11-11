package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SwitchDeciderTest {

    private fun mon(slot: Int, lv: Int, hp: Int, max: Int, types: List<String>, moves: List<Int> = emptyList()) =
        SwitchDecider.Mon(slot, lv, hp, max, types, moves)

    @Test
    fun takesDamageSuperEffective() {
        // 火 打 草 = 2.0
        assertEquals(2.0, SwitchDecider.takesDamage(listOf("草"), listOf("火")), 0.001)
        // 水打草 = 2.0... 实际表里 水→草 是 0.5（草抗水）；草→水 是 2.0
        assertEquals(2.0, SwitchDecider.takesDamage(listOf("水"), listOf("草")), 0.001)
    }

    @Test
    fun takesDamageNeutralWithoutTypes() {
        assertEquals(1.0, SwitchDecider.takesDamage(emptyList(), listOf("火")), 0.001)
    }

    @Test
    fun bestEffectPicksBestMove() {
        // 抓(40/一般) vs 火花(52/火) 打草 → 2.0
        assertEquals(2.0, SwitchDecider.bestEffect(listOf(10, 52), listOf("草")), 0.001)
    }

    @Test
    fun choosesCounterAndHealthy() {
        val team = listOf(
            mon(0, 10, 20, 29, listOf("火"), listOf(52)),   // 打草强，但被克
            mon(1, 10, 29, 29, listOf("水"), listOf(55)),   // 水打草 0.5，但抗火
        )
        val slot = SwitchDecider.choose(team, listOf("草"), 10)
        // 火焰宠克制草（eff 2.0）应该胜出
        assertEquals(0, slot)
    }

    @Test
    fun excludeCurrentSlot() {
        val team = listOf(
            mon(0, 10, 20, 29, listOf("火"), listOf(52)),
            mon(1, 10, 29, 29, listOf("水"), listOf(55)),
        )
        val slot = SwitchDecider.choose(team, listOf("草"), 10, excludeSlot = 0)
        assertEquals(1, slot)
    }

    @Test
    fun skipsFainted() {
        val team = listOf(
            mon(0, 10, 0, 29, listOf("火"), listOf(52)),
            mon(1, 10, 29, 29, listOf("水"), listOf(55)),
        )
        assertEquals(1, SwitchDecider.choose(team, listOf("草"), 10))
    }

    @Test
    fun noUsableReturnsNull() {
        assertNull(SwitchDecider.choose(emptyList(), listOf("草"), 10))
        assertNull(SwitchDecider.choose(listOf(mon(0, 10, 0, 29, listOf("火"))), listOf("草"), 10))
    }
}
