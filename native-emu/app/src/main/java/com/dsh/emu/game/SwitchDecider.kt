package com.dsh.emu.game

/**
 * 换人决策（对应 Python 的 decision_battle.choose_switch 基础策略）：
 * 优先克制敌方、等级不低、少挨打、血多。
 */
object SwitchDecider {

    data class Mon(
        val slot: Int,
        val lv: Int,
        val hp: Int,
        val maxHp: Int,
        val types: List<String>,
        val moves: List<Int> = emptyList(),
    )

    /** 敌方属性打我方属性的倍率（>1 表示被克制）。 */
    fun takesDamage(monTypes: List<String>, enemyTypes: List<String>): Double {
        if (monTypes.isEmpty() || enemyTypes.isEmpty()) return 1.0
        var dmg = 1.0
        for (et in enemyTypes) for (mt in monTypes) {
            dmg *= GameData.typeChart[et to mt] ?: 1.0
        }
        return dmg
    }

    /** 我方最强招对敌方的倍率（无招返回 1.0）。 */
    fun bestEffect(moves: List<Int>, enemyTypes: List<String>): Double {
        var best = 1.0
        for (mid in moves) {
            if (mid == 0) continue
            val eff = BattleDecider.effect(mid, enemyTypes)
            if (eff > best) best = eff
        }
        return best
    }

    /** 单只评分：克制敌方 + 少挨打 + 等级差 + 血量。 */
    fun score(mon: Mon, enemyTypes: List<String>, enemyLv: Int): Double {
        val eff = bestEffect(mon.moves, enemyTypes)
        val takes = takesDamage(mon.types, enemyTypes)
        val hpRatio = if (mon.maxHp > 0) mon.hp.toDouble() / mon.maxHp else 0.0
        return eff * 10 - takes * 8 + (mon.lv - enemyLv) * 0.5 + hpRatio * 5
    }

    /** 选换人槽位：总分最高的可用成员（可排除当前场上的槽）。返回 slot 或 null。 */
    fun choose(team: List<Mon>, enemyTypes: List<String>, enemyLv: Int, excludeSlot: Int = -1): Int? {
        var bestSlot: Int? = null
        var bestScore = Double.NEGATIVE_INFINITY
        for (mon in team) {
            if (mon.slot == excludeSlot) continue
            if (mon.hp <= 0) continue
            val s = score(mon, enemyTypes, enemyLv)
            if (s > bestScore) {
                bestScore = s
                bestSlot = mon.slot
            }
        }
        return bestSlot
    }
}
