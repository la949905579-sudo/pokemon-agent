package com.dsh.emu.game

/** 游戏状态解码（对应 Python 的 state.py / info.py 的只读部分）。 */
object GameState {

    data class Coords(val x: Int, val y: Int)

    data class PartyMon(
        val slot: Int, val lv: Int, val hp: Int, val maxHp: Int, val pid: Long,
        val species: Int = 0,
    ) {
        val name: String get() = Species.nameOf(species)
    }

    /** 坐标（地块坐标，原始值 - 7）。读不到返回 null。 */
    fun coords(): Coords? {
        val x = Memo.s16(Addresses.X_ADDR)
        val y = Memo.s16(Addresses.Y_ADDR)
        if (x == -1) return null
        return Coords(x - Addresses.TILE_OFF, y - Addresses.TILE_OFF)
    }

    /** 是否在战斗中（0 = 地图）。 */
    fun inBattle(): Boolean = Memo.u8(Addresses.BATTLE_FLAG) != 0

    /** 回合阶段（1=主菜单 2=招式 4=动画 0=开场）。 */
    fun turnFlag(): Int = Memo.u8(Addresses.TURN_FLAG)

    /** 对话框是否打开。 */
    fun inDialog(): Boolean = Memo.u8(Addresses.DIALOG_FLAG) != 0

    /** 最近一次确认在战斗里的时间（毫秒），用于战斗结束的滞回。 */
    @Volatile
    private var lastBattleAt = 0L

    /** 滞回时长：战斗标记消失后，这段时间内仍视为战斗（等对话框/动画走完）。 */
    private const val BATTLE_HOLD_MS = 4000L

    /**
     * 场景名。
     * 战斗中按回合标志细分；战斗标记消失但还在对话（击败提示等）且最近战斗过，
     * 返回 "battle_end"，避免下屏立刻跳回地图。
     */
    fun scene(): String {
        val now = System.currentTimeMillis()
        if (inBattle()) {
            lastBattleAt = now
            return when (turnFlag()) {
                0 -> "battle_intro"
                1 -> "battle_main"
                2 -> "battle_moves"
                4 -> "anim"
                else -> "battle"
            }
        }
        // 刚结束战斗、还在对话里（按确定关对话框）→ 保持战斗页
        if (inDialog() && now - lastBattleAt < BATTLE_HOLD_MS) {
            return "battle_end"
        }
        return "map"
    }

    /** 队伍（跳过空槽，等级 0 视为无效）。 */
    fun party(): List<PartyMon> {
        val buf = Memo.bytes(Addresses.PARTY_ADDR, Addresses.PARTY_STRIDE * 6) ?: return emptyList()
        val out = mutableListOf<PartyMon>()
        for (i in 0 until 6) {
            val base = i * Addresses.PARTY_STRIDE
            val lv = buf[base + Addresses.PARTY_LV].toInt() and 0xFF
            if (lv <= 0 || lv > 100) continue
            val hp = (buf[base + Addresses.PARTY_HP].toInt() and 0xFF) or
                ((buf[base + Addresses.PARTY_HP + 1].toInt() and 0xFF) shl 8)
            val mhp = (buf[base + Addresses.PARTY_HP + 2].toInt() and 0xFF) or
                ((buf[base + Addresses.PARTY_HP + 3].toInt() and 0xFF) shl 8)
            val pid = (0 until 4).fold(0L) { acc, k ->
                acc or ((buf[base + Addresses.PARTY_PID + k].toLong() and 0xFF) shl (8 * k))
            }
            val dec = PartyCrypto.decrypt(buf, base)
            out.add(PartyMon(i, lv, hp, mhp, pid, dec?.species ?: 0))
        }
        return out
    }

    /** 玩家朝向（0=下 1=上 2=左 3=右，低字节）。读不到返回 -1。 */
    fun facing(): Int {
        val v = Memo.u8(Addresses.FACING_ADDR)
        return if (v < 0 || v > 3) -1 else v
    }

    /** 我方场上 species（战斗结构 +0）。 */
    fun mySpecies(): Int = Memo.u16(Addresses.MY_BATTLE)

    /** 敌方 species。 */
    fun enemySpecies(): Int = Memo.u16(Addresses.EN_BATTLE)

    data class EnemyInfo(val lv: Int, val hp: Int, val maxHp: Int, val species: Int)

    /** 敌方战斗摘要（等级/HP/最大 HP/species）。读不到返回 null。 */
    fun enemyInfo(): EnemyInfo? {
        val d = Memo.bytes(Addresses.ENEMY_BASE, 8) ?: return null
        val lv = d[0].toInt() and 0xFF
        val hp = (d[2].toInt() and 0xFF) or ((d[3].toInt() and 0xFF) shl 8)
        val mhp = (d[4].toInt() and 0xFF) or ((d[5].toInt() and 0xFF) shl 8)
        val sp = Memo.u16(Addresses.EN_BATTLE)
        if (lv == 0 && hp == 0 && mhp == 0) return null
        return EnemyInfo(lv, hp, mhp, sp)
    }

    /** 我方 4 个招式 id（+0x0C 起，4 × u16）。 */
    fun myMoves(): List<Int> {
        val base = Addresses.MY_BATTLE + 0x0C
        return (0 until 4).map { i -> Memo.u16(base + i * 2) }
    }
}
