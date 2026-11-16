package com.dsh.emu.game

import android.content.Context
import com.dsh.emu.Nlog
import org.json.JSONObject

/**
 * 当前地图数据（tile 级），给下屏「当前地图页 / 大地图」用。
 *
 * 数据源优先级（运行时不再依赖 /sdcard 和 Python 推送）：
 *   1. APK 内 `assets/maps/map_<地图数组地址>.json`（由 `tools/gen_map_assets.py` 从解包数据生成，
 *      全量 345 个 ROM 地址；**懒加载**：先只列文件名，用到哪张才解析哪个文件）；
 *   2. assets 没覆盖这张图 → 直接读模拟器内存 tiles，并写一条 WARN `map.fallback source=memory`；
 *   3. 都失败 → null（UI 显示 --，不崩）。
 *
 * assets 里的 tiles 存的是碰撞位（0=可走、非 0=挡，见 `legacy/mapcap2.py`），
 * 这里统一归一化成 1=可走，与 `MapWalker` 和渲染约定一致。
 *
 * M2-A 起 assets 还带 `behaviors`（每格 2 位十六进制行为 id，来自布局 tileset 的 metatile
 * 属性表）与 `maps`（该布局对应的地图 id）。tiles 会被行为表修正成「步行可走」：
 * `MB_*_WATER` / `MB_WATERFALL` 等水面即使碰撞位可走也当挡（除非以后做冲浪）；
 * 行为容器另存成 [Layer.terrain] 供地图页按 水/草/台阶 着色。
 */
object MapData {
    /** 一张地图的 tile 数据；[tiles][y][x]，1=可走（已扣掉水面等步行不可走行为）。 */
    data class Layer(
        val addr: Int,
        val w: Int,
        val h: Int,
        val tiles: List<List<Int>>,
        /** true=来自 assets，false=回退读了模拟器内存。 */
        val fromAssets: Boolean,
        /** 地形分类（[Terrain] 常量）；null=没有行为数据（内存回退/旧资产），UI 只按 tiles 画。 */
        val terrain: List<List<Int>>? = null,
        /** 该布局对应的地图 id（如 MAP_ROUTE1，查询遭遇表用）；空=list 未知。 */
        val maps: List<String> = emptyList(),
    )

    /** gMapHeader 指针（Python `terrain.py` 实测：换图后值立刻变）。 */
    const val MAP_HDR_PTR = 0x02036DFC

    /** 地图数组地址 -> 归一化 tiles（已解析/测试注入的）。 */
    private val assetTiles = HashMap<Int, List<List<Int>>>()
    /** 地图数组地址 -> (w, h)（assets json 里的尺寸；跨图寻路按任意地图取图用）。 */
    private val assetSizes = HashMap<Int, Pair<Int, Int>>()
    /** 地图数组地址 -> 地形分类网格（从 behaviors 解析；没有 behaviors 的图不存）。 */
    private val assetTerrain = HashMap<Int, List<List<Int>>>()
    /** 地图数组地址 -> 该布局对应的地图 id 列表。 */
    private val assetMaps = HashMap<Int, List<String>>()
    /** assets/maps 里的文件名（只列目录，不解析内容——345 个文件懒加载）。 */
    private val assetNames = HashSet<String>()
    /** 解析资产用的 Context（loadAssets 里存 applicationContext）。 */
    private var appContext: Context? = null
    @Volatile private var assetsLoaded = false
    @Volatile private var cached: Layer? = null

    // ---------- 初始化 / 测试 ----------

    /**
     * 启动时只列 assets/maps 目录（不解析内容）：全量 345 张图 ~2.7MB，主线程逐个解析会卡。
     * 用到哪张图由 [assetLayer] / [current] 懒解析并缓存。
     */
    @Synchronized
    fun loadAssets(context: Context) {
        if (assetsLoaded) return
        assetsLoaded = true
        appContext = context.applicationContext
        try {
            val names = context.assets.list("maps") ?: return
            for (name in names) {
                if (!name.startsWith("map_") || !name.endsWith(".json")) continue
                // map_links.json 是跨图连接表，由 MapLinks 单独加载，这里跳过
                if (name == "map_links.json") continue
                assetNames.add(name)
            }
            Nlog.info("map.assets", "ok" to true, "indexed" to assetNames.size)
        } catch (e: Throwable) {
            Nlog.warn("map.assets", "ok" to false, "code" to e.javaClass.simpleName)
        }
    }

    /** 按地址懒解析 assets（命中缓存直接返回）；没有该资产/解析失败返回 null。 */
    @Synchronized
    private fun parseAsset(addr: Int): Layer? {
        assetTiles[addr]?.let { tiles ->
            val size = assetSizes[addr] ?: ((tiles.firstOrNull()?.size ?: 0) to tiles.size)
            if (size.first > 0 && size.second > 0) {
                return Layer(addr, size.first, size.second, tiles, true,
                    assetTerrain[addr], assetMaps[addr] ?: emptyList())
            }
        }
        val ctx = appContext ?: return null
        val name = "map_%x.json".format(addr)
        if (name !in assetNames) return null
        return try {
            val text = ctx.assets.open("maps/$name").bufferedReader().use { it.readText() }
            parseJson(text)?.also { layer ->
                assetTiles[layer.addr] = layer.tiles
                assetSizes[layer.addr] = layer.w to layer.h
                layer.terrain?.let { assetTerrain[layer.addr] = it }
                assetMaps[layer.addr] = layer.maps
            }
        } catch (e: Throwable) {
            Nlog.warn("map.parse", "ok" to false, "code" to e.javaClass.simpleName)
            null
        }
    }

    @Synchronized
    fun resetForTest() {
        assetTiles.clear()
        assetSizes.clear()
        assetTerrain.clear()
        assetMaps.clear()
        assetNames.clear()
        appContext = null
        assetsLoaded = false
        cached = null
    }

    /** 单测注入 assets 数据，省得依赖 Android Context（无 behaviors → 只按碰撞位）。 */
    @Synchronized
    fun putAssetTilesForTest(addr: Int, tiles: List<List<Int>>) {
        assetTerrain.remove(addr)
        assetMaps.remove(addr)
        assetTiles[addr] = tiles
        val w = tiles.firstOrNull()?.size ?: 0
        if (w > 0) assetSizes[addr] = w to tiles.size
        assetsLoaded = true
        cached = null
    }

    /**
     * 单测注入带行为数据的 assets：behaviorIds[y][x] 是 metatile 行为 id（同 assets `behaviors`），
     * tiles 是碰撞位归一化（1=可走）。内部按与线上相同的规则算地形与「步行可走」。
     */
    @Synchronized
    fun putAssetForTest(addr: Int, tiles: List<List<Int>>, behaviorIds: List<List<Int>>,
                        maps: List<String> = emptyList()) {
        val w = tiles.firstOrNull()?.size ?: 0
        if (w <= 0 || tiles.size != behaviorIds.size) return
        val layer = buildLayer(addr, w, tiles.size, tiles, behaviorIds, maps)
        assetTiles[addr] = layer.tiles
        assetSizes[addr] = w to tiles.size
        layer.terrain?.let { assetTerrain[addr] = it }
        assetMaps[addr] = maps
        assetsLoaded = true
        cached = null
    }

    /**
     * 按地图地址取 assets（或测试注入）里的整张图；没有该图返回 null。
     * 跨图寻路用：规划时不能只看当前地图。
     */
    @Synchronized
    fun assetLayer(addr: Int): Layer? = parseAsset(addr)

    // ---------- 解析 ----------

    /**
     * 解析行为网格行（每格 2 位十六进制，如 "0010"）→ Int 网格；行数/列数不够返回 null。
     * 与 assets `behaviors` 同格式；0x00=MB_NORMAL、0xFF=未知（按普通格处理）。
     */
    internal fun parseBehaviors(rows: List<String>, w: Int, h: Int): List<List<Int>>? {
        if (rows.size < h) return null
        val out = ArrayList<List<Int>>(h)
        for (y in 0 until h) {
            val row = rows[y]
            if (row.length < w * 2) return null
            val cells = ArrayList<Int>(w)
            for (x in 0 until w) {
                val v = row.substring(x * 2, x * 2 + 2).toIntOrNull(16) ?: return null
                cells.add(v)
            }
            out.add(cells)
        }
        return out
    }

    /** 碰撞位归一化 + 行为网格 → 地形分类 / 有效可走 tiles（纯函数，单测直接覆盖）。 */
    internal fun buildLayer(
        addr: Int, w: Int, h: Int,
        pass: List<List<Int>>, behaviorIds: List<List<Int>>?, maps: List<String>,
    ): Layer {
        if (behaviorIds == null) return Layer(addr, w, h, pass, true, null, maps)
        val terrain = ArrayList<List<Int>>(h)
        val tiles = ArrayList<List<Int>>(h)
        for (y in 0 until h) {
            val tRow = ArrayList<Int>(w)
            val eRow = ArrayList<Int>(w)
            for (x in 0 until w) {
                val p = pass.getOrNull(y)?.getOrNull(x) ?: 0
                if (p != 1) {
                    tRow.add(Terrain.BLOCKED)
                    eRow.add(0)
                    continue
                }
                val cat = Terrain.fromBehavior(behaviorIds.getOrNull(y)?.getOrNull(x) ?: 0)
                tRow.add(cat ?: Terrain.WALK)
                eRow.add(if (cat == Terrain.WATER) 0 else 1)
            }
            terrain.add(tRow)
            tiles.add(eRow)
        }
        return Layer(addr, w, h, tiles, true, terrain, maps)
    }

    /** 解析一份地图 json（addr / w / h / tiles / behaviors / maps），失败返回 null。
     *  internal 给单测直接喂 JSON（不用 Android Context）。 */
    internal fun parseJson(text: String): Layer? {
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
            // 行为网格（可选）：缺 behaviors 的旧图照旧只按碰撞位；
            // 有 behaviors 但解析失败时留一条 WARN（地图页会失去地形着色、水格不挡）
            val behaviorRows = o.optJSONArray("behaviors")?.let { a ->
                val rows = ArrayList<String>(a.length())
                for (y in 0 until a.length()) rows.add(a.optString(y, ""))
                parseBehaviors(rows, w, h) ?: run {
                    Nlog.warnThrottled("map.behaviors", "map.behaviors",
                        "addr" to "0x%x".format(addr), "ok" to false, "rows" to a.length())
                    null
                }
            }
            // 地图 id 列表（查询遭遇表用）
            val maps = o.optJSONArray("maps")?.let { a ->
                val out = ArrayList<String>(a.length())
                for (i in 0 until a.length()) a.optString(i, "").takeIf { it.isNotEmpty() }?.let { out.add(it) }
                out
            } ?: emptyList()
            buildLayer(addr, w, h, normalize(raw), behaviorRows, maps)
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
        val asset = parseAsset(addr)
        val layer = if (asset != null) {
            // assets 命中：tiles 已按 behaviors 修正（水不可走），地形/地图 id 一并带给 UI
            Layer(addr, w, h, asset.tiles, true, asset.terrain, asset.maps)
        } else {
            // assets 没这张图才走内存：留痕，方便以后排查「这张图为什么没有」
            fromMemory(addr, w, h)?.also {
                Nlog.warnThrottled(
                    "map.fallback:ok", "map.fallback",
                    "source" to "memory", "addr" to "0x%x".format(addr), "ok" to true,
                )
            }?.let { Layer(addr, w, h, it, false) } ?: run {
                Nlog.warnThrottled(
                    "map.fallback:fail", "map.fallback",
                    "source" to "memory", "addr" to "0x%x".format(addr), "ok" to false,
                )
                null
            }
        }
        cached = layer
        return layer
    }

}

/**
 * 地形分类：[MapData.buildLayer] 从 metatile 行为 id 归一化出的格子类别，给地图页着色与步行判定用。
 * 行为 id → 名字见 `games/pokemon_firered/data/metatile_behaviors.json`。
 */
object Terrain {
    const val BLOCKED = 0
    const val WALK = 1
    const val WATER = 2
    const val GRASS = 3
    const val STAIRS = 4

    /** 步行不可走的水面 = 引擎 `sBehaviorSurfable` 表（实测 2026-11-16 对照 pokefirered
     *  `src/metatile_behavior.c`）：MB_POND_WATER(16)/FAST(17)/DEEP(18)/WATERFALL(19)/
     *  OCEAN(21)/UNUSED(26)/CYCLING_ROAD_WATER(27) + 水流 80–83。
     *  注意 MB_SHALLOW_WATER(23) 是「浅水流/沙」可步行（`IsSandOrShallowFlowingWater`），不能挡。
     *  冲浪以后再做。 */
    private val WATER_IDS = setOf(16, 17, 18, 19, 21, 26, 27, 80, 81, 82, 83)
    /** MB_TALL_GRASS=2：可走，地图页标绿。 */
    private const val BEHAVIOR_TALL_GRASS = 2

    /** MB_ROCK_STAIRS(42) 与 MB_CAVE_DOOR(96)…MB_UNION_ROOM_WARP(113)：楼梯/门/传送。 */
    private fun isStairs(id: Int): Boolean = id == 42 || id in 96..113

    /** 行为 id → 地形分类；null=普通格（可走/挡由碰撞位决定）。 */
    fun fromBehavior(behavior: Int): Int? = when {
        behavior in WATER_IDS -> WATER
        behavior == BEHAVIOR_TALL_GRASS -> GRASS
        isStairs(behavior) -> STAIRS
        else -> null
    }
}
