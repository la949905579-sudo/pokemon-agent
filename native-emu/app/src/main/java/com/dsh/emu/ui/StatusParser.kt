package com.dsh.emu.ui

import org.json.JSONObject

/** 队伍里的一只；读不到的字段留空/负数，UI 显示 --（见 TeamPage 详情）。 */
data class TeamMove(val name: String, val pp: Int, val maxPp: Int?)
data class TeamMon(
    val name: String, val lv: Int, val hp: Int, val max: Int,
    val types: List<String> = emptyList(),
    val moves: List<TeamMove> = emptyList(),
    val exp: Long = -1L,
    /** 当前等级的经验下限 / 下一级阈值；-1 = 数据不够（UI 显示 --） */
    val expCur: Long = -1L,
    val expNext: Long = -1L,
    /** 已满级（100 级没有下一级阈值，UI 显示「已满级」而不是 --） */
    val expMax: Boolean = false,
)
/**
 * 「地图」Tab 的行走预览：起点/终点/tile 方向序列，加上预览时的地图身份
 * （地图数组地址；用于「开始走」前判断是不是已经换图了）。
 */
data class WalkPlan(
    val fromX: Int, val fromY: Int,
    val toX: Int, val toY: Int,
    val steps: List<String>,
    val mapName: String,
)

data class EmuStatus(
    val map: String = "", val x: Int = 0, val y: Int = 0,
    val team: List<TeamMon> = emptyList(),
    val battle: String = "",
    val foeLv: Int = 0, val foeHp: Int = 0, val foeMax: Int = 0,
    val meLv: Int = 0, val meHp: Int = 0, val meMax: Int = 0,
    val moves: List<String> = emptyList(),
    val mmW: Int = 0, val mmH: Int = 0, val mmPx: Int = 0, val mmPy: Int = 0,
    val mmTiles: List<List<Int>>? = null,
)

/**
 * 解析下屏状态 JSON（TCP 推送格式）→ [EmuStatus]。
 *
 * 纯函数：空串 / 解析异常 / 缺字段一律回退默认值，不抛异常（掉线时 UI 仍可渲染）。
 * 从 MainActivity.kt 原样迁出（行为等价）。
 */
internal fun parseStatus(json: String): EmuStatus {
    if (json.isBlank()) return EmuStatus()
    return try {
        val o = JSONObject(json)
        val team = mutableListOf<TeamMon>()
        o.optJSONArray("team")?.let { arr ->
            for (i in 0 until arr.length()) {
                val t = arr.getJSONObject(i)
                val types = mutableListOf<String>()
                t.optJSONArray("types")?.let { a ->
                    for (k in 0 until a.length()) a.optString(k, "").takeIf { it.isNotEmpty() }?.let { types.add(it) }
                }
                val moves = mutableListOf<TeamMove>()
                t.optJSONArray("moves")?.let { a ->
                    for (k in 0 until a.length()) {
                        val mo = a.optJSONObject(k) ?: continue
                        moves.add(TeamMove(
                            mo.optString("name", ""),
                            if (mo.has("pp")) mo.optInt("pp") else -1,
                            if (mo.has("max")) mo.optInt("max") else null,
                        ))
                    }
                }
                team.add(TeamMon(t.optString("name", "?"), t.optInt("lv"), t.optInt("hp"), t.optInt("max"),
                    types, moves, if (t.has("exp")) t.optLong("exp") else -1L,
                    if (t.has("expCur")) t.optLong("expCur") else -1L,
                    if (t.has("expNext")) t.optLong("expNext") else -1L,
                    t.optBoolean("expMax", false)))
            }
        }
        val mm = o.optJSONObject("minimap")
        var mmTiles: List<List<Int>>? = null
        mm?.optJSONArray("tiles")?.let { arr ->
            val rows = mutableListOf<List<Int>>()
            for (y in 0 until arr.length()) {
                val row = arr.optJSONArray(y) ?: continue
                val cells = mutableListOf<Int>()
                for (x in 0 until row.length()) cells.add(row.optInt(x))
                rows.add(cells)
            }
            if (rows.isNotEmpty()) mmTiles = rows
        }
        val d = o.optJSONObject("battle_detail")
        val foe = d?.optJSONObject("foe")
        val me = d?.optJSONObject("me")
        val moves = mutableListOf<String>()
        me?.optJSONArray("moves")?.let { arr ->
            for (i in 0 until arr.length()) moves.add(arr.optString(i, ""))
        }
        EmuStatus(
            o.optString("map", ""), o.optInt("x"), o.optInt("y"), team, o.optString("battle", ""),
            foe?.optInt("lv") ?: 0, foe?.optInt("hp") ?: 0, foe?.optInt("mhp") ?: 0,
            me?.optInt("lv") ?: 0, me?.optInt("hp") ?: 0, me?.optInt("mhp") ?: 0,
            moves,
            mm?.optInt("w") ?: 0, mm?.optInt("h") ?: 0, mm?.optInt("px") ?: 0, mm?.optInt("py") ?: 0,
            mmTiles,
        )
    } catch (e: Exception) { EmuStatus() }
}
