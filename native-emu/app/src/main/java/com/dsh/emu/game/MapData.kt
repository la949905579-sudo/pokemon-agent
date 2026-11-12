package com.dsh.emu.game

import android.content.Context
import com.dsh.emu.Nlog
import org.json.JSONObject

/**
 * 当前地图数据（tile 级），给下屏「当前地图页 / 大地图」用。
 *
 * 数据源优先级（运行时不再依赖 /sdcard 和 Python 推送）：
 *   1. APK 内 `assets/maps/map_<地图数组地址>.json`（仓库根 `maps/` 打包，13 张）；
 *   2. assets 没覆盖这张图 → 直接读模拟器内存 tiles，并写一条 WARN `map.fallback source=memory`；
 *   3. 都失败 → null（UI 显示 --，不崩）。
 *
 * assets 里的 tiles 存的是碰撞位（0=可走、非 0=挡，见 `legacy/mapcap2.py`），
 * 这里统一归一化成 1=可走，与 `MapWalker` 和渲染约定一致。
 */
object MapData {
    /** 一张地图的 tile 数据；tiles[y][x]，1=可走。 */
    data class Layer(
        val addr: Int,
        val w: Int,
        val h: Int,
        val tiles: List<List<Int>>,
        /** true=来自 assets，false=回退读了模拟器内存。 */
        val fromAssets: Boolean,
    )

    /** gMapHeader 指针（Python `terrain.py` 实测：换图后值立刻变）。 */
    const val MAP_HDR_PTR = 0x02036DFC

    /** 地图数组地址 -> 归一化 tiles（assets 打包的）。 */
    private val assetTiles = HashMap<Int, List<List<Int>>>()
    @Volatile private var assetsLoaded = false
    @Volatile private var cached: Layer? = null

    // ---------- 初始化 / 测试 ----------

    /** 启动时把 assets 里 maps 目录下的 json 读进内存（13 个文件共 ~70KB，主线程加载也够快）。 */
    @Synchronized
    fun loadAssets(context: Context) {
        if (assetsLoaded) return
        assetsLoaded = true
        try {
            val names = context.assets.list("maps") ?: return
            for (name in names) {
                if (!name.startsWith("map_") || !name.endsWith(".json")) continue
                val text = context.assets.open("maps/$name").bufferedReader().use { it.readText() }
                val layer = parseJson(text) ?: continue
                assetTiles[layer.addr] = layer.tiles
            }
            Nlog.info("map.assets", "ok" to true, "loaded" to assetTiles.size)
        } catch (e: Throwable) {
            Nlog.warn("map.assets", "ok" to false, "code" to e.javaClass.simpleName)
        }
    }

    @Synchronized
    fun resetForTest() {
        assetTiles.clear()
        assetsLoaded = false
        cached = null
    }

    /** 单测注入 assets 数据，省得依赖 Android Context。 */
    @Synchronized
    fun putAssetTilesForTest(addr: Int, tiles: List<List<Int>>) {
        assetTiles[addr] = tiles
        assetsLoaded = true
        cached = null
    }

    // ---------- 解析 ----------

    /** 解析一份地图 json（addr / w / h / tiles），失败返回 null。 */
    private fun parseJson(text: String): Layer? {
        return try {
            val o = JSONObject(text)
            val addr = o.optString("addr", "").removePrefix("0x").removePrefix("0X")
                .toIntOrNull(16) ?: return null
            val w = o.optInt("w")
            val h = o.optInt("h")
            val arr = o.optJSONArray("tiles") ?: return null
            if (w <= 0 || h <= 0 || arr.length() < h) return null
            val raw = ArrayList<List<Int>>(h)
            for (y in 0 until h) {
                val row = arr.optJSONArray(y) ?: return null
                val cells = ArrayList<Int>(row.length())
                for (x in 0 until row.length()) cells.add(row.optInt(x))
                raw.add(cells)
            }
            Layer(addr, w, h, normalize(raw), true)
        } catch (e: Throwable) {
            Nlog.warn("map.parse", "ok" to false, "code" to e.javaClass.simpleName)
            null
        }
    }

    /** 碰撞位 -> 1=可走（0 可走、非 0 挡）。 */
    fun normalize(raw: List<List<Int>>): List<List<Int>> =
        raw.map { row -> row.map { v -> if (v == 0) 1 else 0 } }

    // ---------- 读当前地图 ----------

    private fun validPtr(v: Int): Boolean =
        v in 0x08000000..0x09FFFFFF || v in 0x02000000..0x0203FFFF

    /** 当前地图数组地址：`0x02036DFC`(gMapHeader) -> `+0x0C`。读不到返回 0。 */
    fun currentMapAddr(): Int {
        val hdr = Memo.u32(MAP_HDR_PTR)
        if (hdr <= 0 || hdr > Int.MAX_VALUE) return 0
        val h = hdr.toInt()
        if (!validPtr(h)) return 0
        val map = Memo.u32(h + 0x0C)
        if (map <= 0 || map > Int.MAX_VALUE) return 0
        val m = map.toInt()
        return if (validPtr(m)) m else 0
    }

    /** 地图尺寸（从地图 header 读 w/h）；失败返回 null。 */
    fun mapSize(): Pair<Int, Int>? {
        val hdr = Memo.u32(MAP_HDR_PTR)
        if (hdr <= 0 || hdr > Int.MAX_VALUE) return null
        val h = hdr.toInt()
        if (!validPtr(h)) return null
        val w = Memo.u32(h).toInt()
        val hh = Memo.u32(h + 4).toInt()
        if (w !in 5..120 || hh !in 5..120) return null
        return w to hh
    }

    /** 直接读模拟器内存里的 tiles（碰撞位归一化）；失败返回 null。 */
    fun fromMemory(addr: Int, w: Int, h: Int): List<List<Int>>? {
        if (w <= 0 || h <= 0) return null
        val buf = Memo.bytes(addr, w * h * 2) ?: return null
        val raw = ArrayList<List<Int>>(h)
        for (y in 0 until h) {
            val row = ArrayList<Int>(w)
            for (x in 0 until w) {
                val i = (y * w + x) * 2
                val v = (buf[i].toInt() and 0xFF) or ((buf[i + 1].toInt() and 0xFF) shl 8)
                row.add((v shr 10) and 3)
            }
            raw.add(row)
        }
        return normalize(raw)
    }

    /** 当前地图；同一张图复用缓存，换图才重取。读不到返回 null。 */
    @Synchronized
    fun current(): Layer? {
        val addr = currentMapAddr()
        if (addr == 0) return null
        cached?.let { if (it.addr == addr) return it }
        val size = mapSize() ?: return null
        val w = size.first
        val h = size.second
        val fromAssets = assetTiles[addr]
        val tiles = fromAssets ?: fromMemory(addr, w, h)?.also {
            // assets 没这张图才走内存：留痕，方便以后排查「这张图为什么没有」
            Nlog.info("map.fallback", "source" to "memory", "addr" to "0x%x".format(addr), "ok" to true)
        } ?: run {
            Nlog.warn("map.fallback", "source" to "memory", "addr" to "0x%x".format(addr), "ok" to false)
            null
        }
        val layer = tiles?.let { Layer(addr, w, h, it, fromAssets != null) }
        cached = layer
        return layer
    }

}
