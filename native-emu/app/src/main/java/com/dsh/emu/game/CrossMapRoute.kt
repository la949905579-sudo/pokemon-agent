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
    ): List<Destination> = links.asSequence()
        .filter { it.map == cur }
        .flatMap { it.destinations().asSequence() }
        .map { it.toMap }
        .distinct()
        .filter { it != cur && it != 0 }
        .map { Destination(it, label(it, mapIds(it))) }
        .sortedBy { it.label }
        .toList()

    /** 地图地址 → 展示名：优先资产里的地图 id（MAP_ROUTE1 → Route1），没有就 0x 地址。 */
    fun label(addr: Int, ids: List<String>): String =
        ids.firstOrNull()?.let { prettyMapId(it) } ?: "0x%x".format(addr)

    /** MAP_PALLET_TOWN → PalletTown；MAP_ROUTE22 → Route22；无前缀原样返回。 */
    fun prettyMapId(id: String): String {
        val name = id.removePrefix("MAP_").trim()
        if (name.isEmpty()) return id
        return name.split('_').joinToString("") { token ->
            if (token.isEmpty()) "" else token.lowercase().replaceFirstChar { it.uppercase() }
        }.ifEmpty { id }
    }
}
