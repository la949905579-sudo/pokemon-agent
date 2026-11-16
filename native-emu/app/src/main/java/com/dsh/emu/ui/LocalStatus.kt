package com.dsh.emu.ui

import com.dsh.emu.Nlog
import com.dsh.emu.game.MapData
import com.dsh.emu.game.Terrain
import org.json.JSONArray
import org.json.JSONObject

/**
 * 用 Kotlin GameState 直接读内存，组装下屏用的 JSON（与 Python 推送格式一致）。
 * 从 MainActivity.kt 原样迁出（行为等价）；返回空串表示本次读取失败，调用方回退到推送数据。
 */
internal fun buildLocalStatusJson(): String {
    return try {
        val c = com.dsh.emu.game.GameState.coords()
        val party = com.dsh.emu.game.GameState.party()
        val scene = com.dsh.emu.game.GameState.scene()
        val battle = if (scene.startsWith("battle")) scene else ""
        val o = org.json.JSONObject()
        o.put("map", scene)
        o.put("x", c?.x ?: 0)
        o.put("y", c?.y ?: 0)
        o.put("battle", battle)
        // 当前地图 tiles：优先 assets/maps，缺图回退模拟器内存（MapData 里打 WARN）
        val mapLayer = com.dsh.emu.game.MapData.current()
        if (mapLayer != null) {
            val mm = org.json.JSONObject()
            mm.put("w", mapLayer.w)
            mm.put("h", mapLayer.h)
            mm.put("px", c?.x ?: 0)
            mm.put("py", c?.y ?: 0)
            val tiles = org.json.JSONArray()
            for (row in mapLayer.tiles) {
                val r = org.json.JSONArray()
                for (v in row) r.put(v)
                tiles.put(r)
            }
            mm.put("tiles", tiles)
            addTerrain(mm, mapLayer)
            o.put("minimap", mm)
            // 遭遇摘要（地图页一行展示）；同一布局多张图时取第一个有遭遇表的
            val enc = com.dsh.emu.game.Encounters.summary(mapLayer.maps)
            if (enc.isNotEmpty()) o.put("encounters", enc)
            logMapFacts(mapLayer, enc)
        }
        val team = org.json.JSONArray()
        for (m in party) {
            val t = org.json.JSONObject()
            t.put("name", m.name)
            t.put("lv", m.lv)
            t.put("hp", m.hp)
            t.put("max", m.maxHp)
            val types = org.json.JSONArray()
            for (ty in m.types) types.put(ty)
            t.put("types", types)
            val moves = org.json.JSONArray()
            for (i in m.moves.indices) {
                val mid = m.moves[i]
                val info = com.dsh.emu.game.GameData.moves[mid]
                val mo = org.json.JSONObject()
                mo.put("name", info?.first ?: "")
                mo.put("pp", m.pp.getOrNull(i) ?: -1)
                // 上限 PP 没有数据源（队伍结构里只有当前 PP），不带 max，UI 显示 --
                moves.put(mo)
            }
            t.put("moves", moves)
            t.put("exp", m.exp)
            // 升级进度：成长类型从 ROM BaseStats 读（读不到回退标准表），拿不到就不带这两个字段。
            // 满级没有「下一级阈值」，单独标出来，UI 显示「已满级」。
            if (m.lv >= 100) {
                t.put("expMax", true)
            } else {
                val prog = com.dsh.emu.game.Growth.progress(m.species, m.lv, m.exp)
                if (prog != null) {
                    t.put("expCur", prog.cur)
                    t.put("expNext", prog.next)
                }
            }
            team.put(t)
        }
        o.put("team", team)
        if (battle.isNotBlank()) {
            val detail = org.json.JSONObject()
            val moves = org.json.JSONArray()
            for (mid in com.dsh.emu.game.GameState.myMoves()) {
                val info = com.dsh.emu.game.GameData.moves[mid]
                // 招式名表未覆盖的招（P3 待补全）显示 #id，保证格子仍可点；
                // 0 = 空槽，显示—并禁用。
                moves.put(if (info != null) info.first else if (mid != 0) "#$mid" else "")
            }
            val me = org.json.JSONObject()
            me.put("lv", party.firstOrNull()?.lv ?: 0)
            me.put("hp", party.firstOrNull()?.hp ?: 0)
            me.put("mhp", party.firstOrNull()?.maxHp ?: 0)
            me.put("moves", moves)
            detail.put("me", me)
            val foe = org.json.JSONObject()
            val ei = com.dsh.emu.game.GameState.enemyInfo()
            foe.put("lv", ei?.lv ?: 0)
            foe.put("hp", ei?.hp ?: 0)
            foe.put("mhp", ei?.maxHp ?: 0)
            foe.put("species", ei?.species ?: 0)
            detail.put("foe", foe)
            o.put("battle_detail", detail)
        }
        o.toString()
    } catch (e: Throwable) {
        ""
    }
}

/** minimap.terrain：每行一个字符串，字符=地形分类（0 挡/1 可走/2 水/3 草/4 台阶）。 */
private fun addTerrain(mm: JSONObject, layer: MapData.Layer) {
    val terrain = layer.terrain ?: return
    val arr = JSONArray()
    for (row in terrain) {
        val sb = StringBuilder(row.size)
        for (v in row) sb.append(v.coerceIn(0, 4))
        arr.put(sb.toString())
    }
    mm.put("terrain", arr)
}

/** 已打过日志的地图地址（常驻刷新每 500ms 一次，不能每帧刷日志）。 */
private val loggedMaps = java.util.Collections.newSetFromMap(
    java.util.concurrent.ConcurrentHashMap<Int, Boolean>()
)

/** 每张图只打一次地形/遭遇摘要（取证用；换图后重新打）。 */
private fun logMapFacts(layer: MapData.Layer, enc: String) {
    if (!loggedMaps.add(layer.addr)) return
    val t = layer.terrain
    if (t != null) {
        var water = 0
        var grass = 0
        var stairs = 0
        for (row in t) for (v in row) when (v) {
            Terrain.WATER -> water++
            Terrain.GRASS -> grass++
            Terrain.STAIRS -> stairs++
        }
        Nlog.info("map.terrain",
            "addr" to "0x%x".format(layer.addr), "w" to layer.w, "h" to layer.h,
            "water" to water, "grass" to grass, "stairs" to stairs, "maps" to layer.maps.size)
    }
    if (enc.isNotEmpty()) {
        Nlog.info("map.encounters", "addr" to "0x%x".format(layer.addr), "text" to enc)
    }
}
