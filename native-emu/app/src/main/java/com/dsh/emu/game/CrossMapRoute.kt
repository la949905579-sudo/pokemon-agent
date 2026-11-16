package com.dsh.emu.game

/**
 * 跨图 UI 的小工具：当前地图能直接去哪些相邻地图、地图 id 怎么显示成友好名。
 * 纯函数（links / mapIds 由调用方注入），单测直接覆盖；不读内存/assets。
 */
object CrossMapRoute {
    /** 一个相邻目的地：目标地图地址 + 展示名。 */
    data class Destination(val mapAddr: Int, val label: String)

    /**
     * 当前地图的相邻目的地：按目标图去重（同一张图多个出口只留一个）、去掉自己/坏地址，
     * 按展示名排序。links 来自 [MapLinks.all]。
     */
    fun destinations(
        cur: Int,
        links: List<MapLink>,
        mapIds: (Int) -> List<String>,
    ): List<Destination> {
        // 连接记录里的解包地图 id 最准（同布局多张图共用资产，比如 17 个宝可梦中心）；
        // 没有时退回资产 maps 首项，再退回 0x 地址。
        val nameByAddr = HashMap<Int, String>()
        for (l in links) {
            if (l.map != cur) continue
            for (d in l.destinations()) {
                if (!d.name.isNullOrBlank()) nameByAddr.putIfAbsent(d.toMap, d.name)
            }
        }
        return links.asSequence()
            .filter { it.map == cur }
            .flatMap { it.destinations().asSequence() }
            .map { it.toMap }
            .distinct()
            .filter { it != cur && it != 0 }
            .map { Destination(it, label(it, nameByAddr[it], mapIds(it))) }
            .sortedBy { it.label }
            .toList()
    }

    /** 地图地址 → 展示名：连接记录的解包 id > 资产里的地图 id > 0x 地址。 */
    fun label(addr: Int, ids: List<String>): String = label(addr, null, ids)

    fun label(addr: Int, name: String?, ids: List<String>): String =
        (name ?: ids.firstOrNull())?.let { prettyMapId(it) } ?: "0x%x".format(addr)

    /** MAP_PALLET_TOWN → PalletTown；MAP_ROUTE22 → Route22；…_1F → 1F（楼层大写）。 */
    fun prettyMapId(id: String): String {
        val name = id.removePrefix("MAP_").trim()
        if (name.isEmpty()) return id
        return name.split('_').joinToString("") { token ->
            when {
                token.isEmpty() -> ""
                token.first().isDigit() -> token.uppercase()      // 1F / 2F / B1F
                else -> token.lowercase().replaceFirstChar { it.uppercase() }
            }
        }.ifEmpty { id }
    }
}
