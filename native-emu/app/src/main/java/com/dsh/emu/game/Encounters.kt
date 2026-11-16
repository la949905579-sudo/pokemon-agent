package com.dsh.emu.game

import android.content.Context
import com.dsh.emu.Nlog
import org.json.JSONObject

/**
 * 地图遭遇表（叶绿版）：APK 内 `assets/maps/encounters_leafgreen.json`
 * （由 `tools/gen_map_assets.py` 从解包 `wild_encounters.json` 的 `_LeafGreen` 分支拷入）。
 *
 * 懒加载：第一次用到才解析整表（208KB），按地图 id 缓存一行摘要给地图页显示；
 * 数据缺失/解析失败时返回空串，UI 不显示，不崩。
 */
object Encounters {
    private const val ASSET = "maps/encounters_leafgreen.json"

    private var appContext: Context? = null
    @Volatile private var loaded = false
    @Volatile private var mapsObj: JSONObject? = null
    /** 资产缺失/解析失败：负缓存，避免常驻刷新反复重开 208KB + 刷日志。 */
    @Volatile private var loadFailed = false
    /** 地图 id -> 摘要（空串=该图没有遭遇表），避免每次刷新重复拼）。 */
    private val cache = HashMap<String, String>()

    @Synchronized
    fun loadAssets(context: Context) {
        if (loaded) return
        loaded = true
        appContext = context.applicationContext
    }

    @Synchronized
    fun resetForTest() {
        appContext = null
        loaded = false
        mapsObj = null
        loadFailed = false
        cache.clear()
    }

    /** 单测注入遭遇表 JSON（{"maps":{...}} 或直接 maps 对象）。 */
    @Synchronized
    fun putJsonForTest(json: String) {
        mapsObj = try {
            val o = JSONObject(json)
            o.optJSONObject("maps") ?: o
        } catch (_: Throwable) {
            null
        }
        loaded = true
        cache.clear()
    }

    private fun ensureMaps(): JSONObject? {
        if (loadFailed) return null
        mapsObj?.let { return it }
        val ctx = appContext ?: return null
        return try {
            val text = ctx.assets.open(ASSET).bufferedReader().use { it.readText() }
            JSONObject(text).optJSONObject("maps")?.also { mapsObj = it } ?: run {
                loadFailed = true
                Nlog.warnThrottled("map.encounters", "map.encounters",
                    "ok" to false, "code" to "no-maps")
                null
            }
        } catch (e: Throwable) {
            loadFailed = true
            Nlog.warnThrottled("map.encounters", "map.encounters",
                "ok" to false, "code" to e.javaClass.simpleName)
            null
        }
    }

    /**
     * 地图 id 列表 → 一行摘要（如 "陆 波波2-5/小拉达3-4；水 鲤鱼王5-10"）；都没遭遇返回 ""。
     * 同一布局可能对应多张图（资产按 blockdata 共址），取第一个有遭遇表的 id。
     */
    fun summary(mapIds: List<String>): String {
        if (mapIds.isEmpty()) return ""
        val maps = ensureMaps() ?: return ""
        for (id in mapIds) {
            val hit = cache[id] ?: summaryOf(maps.optJSONObject(id)).also { cache[id] = it }
            if (hit.isNotEmpty()) return hit
        }
        return ""
    }

    /** 纯函数：单张地图的遭遇 JSON → 摘要行。分类顺序：陆/水/碎岩/钓。 */
    internal fun summaryOf(entry: JSONObject?): String {
        if (entry == null) return ""
        val parts = ArrayList<String>(4)
        for ((key, label) in CATEGORIES) {
            val o = entry.optJSONObject(key) ?: continue
            val slots = ArrayList<JSONObject>()
            if (key == "fishing") {
                // 钓鱼分 old/good/super_rod 三组，摘要里合并
                val rods = o.optJSONObject("rods")
                if (rods != null) {
                    for (r in RODS) {
                        val arr = rods.optJSONArray(r) ?: continue
                        for (i in 0 until arr.length()) arr.optJSONObject(i)?.let { slots.add(it) }
                    }
                }
            } else {
                addSlots(o, slots)
            }
            val text = slotsText(slots)
            if (text.isNotEmpty()) parts.add("$label $text")
        }
        return parts.joinToString("；")
    }

    private val CATEGORIES = listOf(
        "land" to "陆", "water" to "水", "rock_smash" to "碎岩", "fishing" to "钓",
    )
    private val RODS = listOf("old_rod", "good_rod", "super_rod")

    private fun addSlots(o: JSONObject, out: MutableList<JSONObject>) {
        val arr = o.optJSONArray("slots") ?: return
        for (i in 0 until arr.length()) arr.optJSONObject(i)?.let { out.add(it) }
    }

    /** slots → "波波2-5/小拉达3-4"：同种合并等级区间；名表没有的种显示 #id。 */
    internal fun slotsText(slots: List<JSONObject>): String {
        val order = ArrayList<Int>()
        val mins = HashMap<Int, Int>()
        val maxs = HashMap<Int, Int>()
        for (s in slots) {
            val sp = s.optInt("species", 0)
            if (sp <= 0) continue
            val lo = s.optInt("min", 0)
            val hi = s.optInt("max", lo)
            if (sp !in mins) order.add(sp)
            mins[sp] = minOf(mins.getOrDefault(sp, lo), lo)
            maxs[sp] = maxOf(maxs.getOrDefault(sp, hi), hi)
        }
        return order.joinToString("/") { sp ->
            val name = Species.names.getOrNull(sp - 1) ?: "#$sp"
            val lo = mins[sp] ?: 0
            val hi = maxs[sp] ?: lo
            if (lo == hi) "$name$lo" else "$name$lo-$hi"
        }
    }
}
