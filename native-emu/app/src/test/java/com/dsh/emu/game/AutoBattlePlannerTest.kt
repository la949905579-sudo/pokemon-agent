package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/** 自动战斗选招规划（纯逻辑）。 */
class AutoBattlePlannerTest {

    @Test
    fun picksSuperEffectiveMove() {
        // 33 撞击（一般 35） / 85 十万伏特（电 90）；敌方水 → 电 2 倍
        val plan = AutoBattlePlanner.plan(listOf(33, 85, 0, 0), listOf(10, 10, 0, 0), listOf("水"))
        assertEquals(1, plan!!.slotIndex)
        assertEquals(85, plan.moveId)
    }

    @Test
    fun skipsMoveWithoutPp() {
        // 十万伏特 PP 用光 → 退而用撞击
        val plan = AutoBattlePlanner.plan(listOf(33, 85, 0, 0), listOf(10, 0, 0, 0), listOf("水"))
        assertEquals(0, plan!!.slotIndex)
        assertEquals(33, plan.moveId)
    }

    @Test
    fun noMovesReturnsNull() {
        assertNull(AutoBattlePlanner.plan(emptyList(), emptyList(), listOf("水")))
    }

    @Test
    fun allPpZeroReturnsNull() {
        assertNull(AutoBattlePlanner.plan(listOf(33, 85, 0, 0), listOf(0, 0, 0, 0), listOf("水")))
    }

    @Test
    fun missingPpAssumesFull() {
        // PP 缺失（读不到）时按满 PP 处理，仍能选出最优招
        val plan = AutoBattlePlanner.plan(listOf(33, 85, 0, 0), emptyList(), listOf("水"))
        assertEquals(1, plan!!.slotIndex)
    }
}
