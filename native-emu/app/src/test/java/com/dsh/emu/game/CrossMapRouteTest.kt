package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** 跨图 UI 的纯函数：相邻目的地去重/排序、地图 id 友好名。 */
class CrossMapRouteTest {

    private fun link(map: Int, toMap: Int, to: Pair<Int, Int> = 0 to 0) =
        MapLink(map, 4, 2, "east", toMap, to.first, to.second)

    @Test
    fun destinationsDedupesAndSortsByLabel() {
        val ids = mapOf(
            0x200 to listOf("MAP_ROUTE2"),
            0x300 to listOf("MAP_PALLET_TOWN"),
            0x400 to listOf("MAP_VIRIDIAN_CITY"),
        )
        val links = listOf(
            link(0x100, 0x300), link(0x100, 0x300, 1 to 2), link(0x100, 0x300, 2 to 2),
            link(0x100, 0x200), link(0x100, 0x100),      // 自己
            link(0x200, 0x100),                          // 别的图的出口不算
        )
        val got = CrossMapRoute.destinations(0x100, links) { ids[it] ?: emptyList() }
        assertEquals(listOf("PalletTown", "Route2"), got.map { it.label })
        assertEquals(listOf(0x300, 0x200), got.map { it.mapAddr })
    }

    @Test
    fun destinationsEmptyWithoutLinks() {
        assertTrue(CrossMapRoute.destinations(0x100, emptyList()) { emptyList() }.isEmpty())
    }

    @Test
    fun labelFallsBackToAddressWithoutAsset() {
        assertEquals("0x2a0", CrossMapRoute.label(0x2a0, emptyList()))
        assertEquals("Route1", CrossMapRoute.label(0x82e4e2c, listOf("MAP_ROUTE1")))
    }

    @Test
    fun prettyMapIdFormatsIds() {
        assertEquals("PalletTown", CrossMapRoute.prettyMapId("MAP_PALLET_TOWN"))
        assertEquals("Route22", CrossMapRoute.prettyMapId("MAP_ROUTE22"))
        assertEquals("ViridianCityGym", CrossMapRoute.prettyMapId("MAP_VIRIDIAN_CITY_GYM"))
        assertEquals("Untitled", CrossMapRoute.prettyMapId("UNTITLED"))
        assertEquals("", CrossMapRoute.prettyMapId(""))
    }

    @Test
    fun destinationsPreferLinkMapNameOverSharedAsset() {
        // 17 个宝可梦中心共用同一布局资产；链接里的 to_name 才能给出正确城市名
        val ids = mapOf(0x500 to listOf("MAP_CELADON_CITY_POKEMON_CENTER_1F"))
        val links = listOf(
            MapLink(0x100, 4, 2, null, 0x500, 7, 8, emptyList(), false,
                "MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F")
        )
        val got = CrossMapRoute.destinations(0x100, links) { ids[it] ?: emptyList() }
        assertEquals("ViridianCityPokemonCenter1F", got[0].label)
        // 没有 to_name 时退回资产 maps 首项
        val plain = listOf(MapLink(0x100, 4, 2, null, 0x500, 7, 8))
        assertEquals("CeladonCityPokemonCenter1F",
            CrossMapRoute.destinations(0x100, plain) { ids[it] ?: emptyList() }[0].label)
    }
}
