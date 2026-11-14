package com.dsh.emu.game

/**
 * 自动战斗的选招规划（纯逻辑，可离线单测）。
 *
 * 输入：我方 4 招 id（战斗结构）/ 队伍 PP（可能为空）/ 敌方属性；
 * 输出：要施放的招式格（0..3）与分数，交给 `ui/BattleMoveAction.cast` 执行。
 * PP 缺失时按满 PP 处理（只有演示/兜底场景会缺）。
 */
object AutoBattlePlanner {

    data class Plan(val slotIndex: Int, val moveId: Int, val name: String, val score: Double)

    /** 4 招 + 4 PP + 敌方属性 → 最优招式；全部不可用返回 null。 */
    fun plan(moves: List<Int>, pp: List<Int>, enemyTypes: List<String>): Plan? {
        if (moves.isEmpty()) return null
        val effPp = if (pp.size >= moves.size) pp else List(moves.size) { 99 }
        val c = BattleDecider.chooseMove(moves, effPp, enemyTypes) ?: return null
        return Plan(c.index, c.moveId, c.name, c.score)
    }
}
