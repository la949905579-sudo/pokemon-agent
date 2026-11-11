package com.dsh.emu.game

/**
 * 战斗出招决策（阶段 2 的简化版）：威力 × 属性克制，选最高分。
 * 与 Python 版 decision_battle.choose_move 的基础策略一致（不含 intent/压血等高级约束）。
 */
object BattleDecider {

    data class Choice(val index: Int, val moveId: Int, val name: String, val score: Double)

    /** 单招对指定敌方属性的倍率（无数据返回 1.0）。 */
    fun effect(moveId: Int, enemyTypes: List<String>): Double {
        val info = GameData.moves[moveId] ?: return 1.0
        val typ = info.second
        if (enemyTypes.isEmpty()) return 1.0
        var eff = 1.0
        for (et in enemyTypes) {
            eff *= GameData.typeChart[typ to et] ?: 1.0
        }
        return eff
    }

    /** 招式评分：威力 × 克制（变化招威力 0 → 低分保底）。 */
    fun score(moveId: Int, enemyTypes: List<String>): Double {
        val info = GameData.moves[moveId] ?: return -1.0
        val power = info.third
        return (power.coerceAtLeast(1) * effect(moveId, enemyTypes))
    }

    /**
     * 选招：返回最优的候选（含序号）。
     * pp 里 <=0 的招跳过；全都不行返回 null。
     */
    fun chooseMove(moves: List<Int>, pp: List<Int>, enemyTypes: List<String>): Choice? {
        var best: Choice? = null
        for (i in moves.indices) {
            val mid = moves[i]
            if (mid == 0) continue
            val p = pp.getOrNull(i) ?: 0
            if (p <= 0) continue
            val info = GameData.moves[mid] ?: continue
            val s = score(mid, enemyTypes)
            if (best == null || s > best.score) {
                best = Choice(i, mid, info.first, s)
            }
        }
        return best
    }
}
