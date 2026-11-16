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

/**
 * 跨图寻路预览：[plan] 由 [com.dsh.emu.game.CrossMapPathfinder.planToMap] 算出，
 * [mapName] 是规划时的当前地图身份（开始走前比对，换图后不误执行）。
 */
data class CrossPlan(
    val plan: com.dsh.emu.game.CrossMapPathfinder.Plan,
    val targetLabel: String,
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
    /** 地形分类网格（[com.dsh.emu.game.Terrain] 常量；null=没有行为数据）。 */
    val mmTerrain: List<List<Int>>? = null,
    /** 当前地图遭遇摘要（一行；空=没有数据）。 */
    val encounters: String = "",
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
        // 地形分类：每行一个字符串，字符=分类（0 挡/1 可走/2 水/3 草/4 台阶）。
        // 严格校验：出现非法字符就整张地形作废（fail-closed，UI 退回只按 tiles 画）。
        var mmTerrain: List<List<Int>>? = null
        mm?.optJSONArray("terrain")?.let { arr ->
            val rows = mutableListOf<List<Int>>()
            var ok = true
            for (y in 0 until arr.length()) {
                val s2 = arr.optString(y, "")
                if (s2.isEmpty()) { ok = false; break }
                val cells = ArrayList<Int>(s2.length)
                for (ch in s2) {
                    val v = ch - '0'
                    if (v !in 0..4) { ok = false; break }
                    cells.add(v)
                }
                if (!ok) break
                rows.add(cells)
            }
            if (ok && rows.isNotEmpty()) mmTerrain = rows
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
            mmTiles, mmTerrain, o.optString("encounters", ""),
        )
    } catch (e: Exception) { EmuStatus() }
}
