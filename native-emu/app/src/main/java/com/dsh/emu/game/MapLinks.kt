package com.dsh.emu.game

import android.content.Context
import com.dsh.emu.Nlog
import org.json.JSONArray

/** 一条「换图出口」的目标。复用房间的同一出口可能有多个去向（`targets`）。 */
data class MapLinkTarget(val toMap: Int, val toX: Int, val toY: Int)

/**
 * 一条地图连接（实测走位记录，与 Python `map_links.py` 同源）：在 [map] 的 ([exitX],[exitY]) 格换到 [toMap] 的 ([toX],[toY])。
 *
 * - [side] 非空：站上出口格后再朝该方向多走一步触发换图（north/south/east/west/top/bottom/up/down）；
 * - [side] 为空：踩上出口格即换图（实机门格语义待真机确认）；
 * - [targets] 非空：复用房间多目标，实际去向由游戏状态决定，规划时逐个当边处理。
 */
data class MapLink(
    val map: Int,
    val exitX: Int,
    val exitY: Int,
    val side: String?,
    val toMap: Int,
    val toX: Int,
    val toY: Int,
    val targets: List<MapLinkTarget> = emptyList(),
    val reused: Boolean = false,
) {
    /** 该出口的全部可能去向（有 targets 用 targets，兼容只有 to_map 的老记录）。 */
    fun destinations(): List<MapLinkTarget> =
        if (targets.isNotEmpty()) targets else listOf(MapLinkTarget(toMap, toX, toY))
}

/**
 * 地图连接表：打包在 `assets/maps/map_links.json`（由根 `map_links.json` 复制，13 条实测记录）。
 *
 * 数据缺失/解析失败 = 空表：跨图规划返回 null，同图行走不受影响。
 * 单测用 [putForTest] 注入假表，不读 assets、不读实机。
 */
object MapLinks {
    @Volatile private var links: List<MapLink> = emptyList()
    @Volatile private var loaded = false

    /** 启动时读 `assets/maps/map_links.json`；重复调用只加载一次。 */
    @Synchronized
    fun loadAssets(context: Context) {
        if (loaded) return
        loaded = true
        try {
            val text = context.assets.open("maps/map_links.json").bufferedReader().use { it.readText() }
            links = parse(text)
            Nlog.info("map.links", "ok" to true, "count" to links.size)
        } catch (e: Throwable) {
            Nlog.warn("map.links", "ok" to false, "code" to e.javaClass.simpleName)
        }
    }

    @Synchronized
    fun resetForTest() {
        links = emptyList()
        loaded = false
    }

    @Synchronized
    fun putForTest(list: List<MapLink>) {
        links = list
        loaded = true
    }

    /** 全部连接（规划器按图过滤用）。 */
    fun all(): List<MapLink> = links

    /** 该地图的所有出口。 */
    fun linksFrom(mapAddr: Int): List<MapLink> = links.filter { it.map == mapAddr }

    /** 指定出口格的连接（执行器落地校验用）。 */
    fun linkAt(mapAddr: Int, x: Int, y: Int): MapLink? =
        links.firstOrNull { it.map == mapAddr && it.exitX == x && it.exitY == y }

    /** side → 方向（执行器多按一步用）；不可识别/为空返回 null。 */
    fun sideDir(side: String?): String? = when (side?.lowercase()) {
        "north", "up", "top" -> "UP"
        "south", "down", "bottom" -> "DOWN"
        "east", "right" -> "RIGHT"
        "west", "left" -> "LEFT"
        else -> null
    }

    /** 解析 json 数组；坏条目跳过，整体异常返回空表。 */
    internal fun parse(text: String): List<MapLink> = try {
        val arr = JSONArray(text)
        val out = ArrayList<MapLink>(arr.length())
        for (i in 0 until arr.length()) {
            val o = arr.optJSONObject(i) ?: continue
            val map = o.optInt("map", 0)
            val exit = o.optJSONArray("exit") ?: continue
            val toMap = o.optInt("to_map", 0)
            val toPos = o.optJSONArray("to_pos")
            if (map == 0 || exit.length() < 2 || toMap == 0 || toPos == null || toPos.length() < 2) continue
            val targets = ArrayList<MapLinkTarget>()
            o.optJSONArray("targets")?.let { ts ->
                for (k in 0 until ts.length()) {
                    val t = ts.optJSONObject(k) ?: continue
                    val tm = t.optInt("to_map", 0)
                    val tp = t.optJSONArray("to_pos") ?: continue
                    if (tm == 0 || tp.length() < 2) continue
                    targets.add(MapLinkTarget(tm, tp.optInt(0), tp.optInt(1)))
                }
            }
            out.add(
                MapLink(
                    map = map,
                    exitX = exit.optInt(0),
                    exitY = exit.optInt(1),
                    side = if (o.isNull("side")) null else o.optString("side", "").ifBlank { null },
                    toMap = toMap,
                    toX = toPos.optInt(0),
                    toY = toPos.optInt(1),
                    targets = targets,
                    reused = o.optBoolean("reused", false),
                )
            )
        }
        out
    } catch (e: Throwable) {
        emptyList()
    }
}
