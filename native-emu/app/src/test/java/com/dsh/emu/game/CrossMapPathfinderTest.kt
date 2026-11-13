package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * 跨图 A* 离线单测：假地图图 + 假连接表，不读实机/assets。
 *
 * 覆盖：同图降级 MapWalker、直连两图、多跳三图、无路（缺图/断连）、
 * 复用房间多目标选择、多出口时选更短路线。
 */
class CrossMapPathfinderTest {

    private val a = 0x100
    private val b = 0x200
    private val c = 0x300

    private fun open(w: Int = 5, h: Int = 5): List<List<Int>> = List(h) { List(w) { 1 } }

    private fun link(
        map: Int,
        exit: Pair<Int, Int>,
        side: String?,
        toMap: Int,
        to: Pair<Int, Int>,
        targets: List<MapLinkTarget> = emptyList(),
    ) = MapLink(map, exit.first, exit.second, side, toMap, to.first, to.second, targets, targets.isNotEmpty())

    private fun plan(
        start: CrossMapPathfinder.Pos,
        goal: CrossMapPathfinder.Pos,
        tiles: Map<Int, List<List<Int>>>,
        links: List<MapLink>,
    ) = CrossMapPathfinder.plan(
        start, goal,
        tilesOf = { tiles[it] },
        linksFrom = { m -> links.filter { it.map == m } },
    )

    // 1) 同图：降级成现有 MapWalker，行为不变
    @Test
    fun sameMapDegradesToMapWalker() {
        val tiles = open()
        val result = plan(
            CrossMapPathfinder.Pos(a, 1, 1),
            CrossMapPathfinder.Pos(a, 3, 3),
            mapOf(a to tiles), emptyList(),
        )
        assertNotNull(result)
        result!!
        assertEquals(1, result.legs.size)
        assertNull("同图段不应有换图动作", result.legs[0].warp)
        assertEquals(
            MapWalker.path(tiles, MapWalker.Point(1, 1), MapWalker.Point(3, 3)),
            result.legs[0].dirs,
        )
        assertEquals(4, result.totalSteps)
    }

    // 2) 直连两图：边界出口 side=east，走 3 步到出口再往右一步换图
    @Test
    fun directLinkAcrossTwoMaps() {
        val result = plan(
            CrossMapPathfinder.Pos(a, 1, 2),
            CrossMapPathfinder.Pos(b, 3, 2),
            mapOf(a to open(), b to open()),
            listOf(link(a, 4 to 2, "east", b, 0 to 2)),
        )
        assertNotNull(result)
        result!!
        assertEquals(2, result.legs.size)
        assertEquals(a, result.legs[0].map)
        assertEquals(listOf("RIGHT", "RIGHT", "RIGHT"), result.legs[0].dirs)
        assertEquals(CrossMapPathfinder.Warp(4, 2, "RIGHT", b, 0, 2), result.legs[0].warp)
        assertEquals(b, result.legs[1].map)
        assertEquals(CrossMapPathfinder.Pos(b, 3, 2), result.goal)
        assertEquals(6, result.totalSteps)
    }

    // 3) 多跳三图：A→B→C 两段换图
    @Test
    fun multiHopAcrossThreeMaps() {
        val result = plan(
            CrossMapPathfinder.Pos(a, 1, 2),
            CrossMapPathfinder.Pos(c, 3, 2),
            mapOf(a to open(), b to open(), c to open()),
            listOf(
                link(a, 4 to 2, "east", b, 0 to 2),
                link(b, 4 to 2, "east", c, 0 to 2),
            ),
        )
        assertNotNull(result)
        result!!
        assertEquals(3, result.legs.size)
        assertEquals(listOf(a, b, c), result.legs.map { it.map })
        assertEquals(2, result.legs.count { it.warp != null })
        assertEquals(c, result.legs[1].warp!!.toMap)
        assertEquals(10, result.totalSteps)
    }

    // 4) 无路：目标图缺 tiles / 目标图无连接 → null
    @Test
    fun noRouteWhenTilesMissingOrDisconnected() {
        val missingTiles = plan(
            CrossMapPathfinder.Pos(a, 0, 0),
            CrossMapPathfinder.Pos(b, 2, 2),   // 目标在 B 内部，必须走 B 的 tiles
            mapOf(a to open()),   // 没有 B 的图数据
            listOf(link(a, 4 to 0, "east", b, 0 to 0)),
        )
        assertNull("缺目标图 tiles 应无路", missingTiles)

        val disconnected = plan(
            CrossMapPathfinder.Pos(a, 0, 0),
            CrossMapPathfinder.Pos(c, 0, 0),
            mapOf(a to open(), c to open()),
            listOf(link(a, 4 to 0, "east", b, 0 to 0)),   // A 只连 B，且无 B 数据
        )
        assertNull("断连应无路", disconnected)
    }

    // 5) 复用房间：同一出口两个 targets，要选能到目标的那个
    @Test
    fun reusedRoomPicksReachableTarget() {
        val links = listOf(
            link(a, 2 to 2, null, b, 0 to 0, targets = listOf(
                MapLinkTarget(b, 0, 0),
                MapLinkTarget(c, 0, 0),
            )),
        )
        val toC = plan(
            CrossMapPathfinder.Pos(a, 2, 1),
            CrossMapPathfinder.Pos(c, 2, 2),
            mapOf(a to open(), b to open(), c to open()),
            links,
        )
        assertNotNull(toC)
        toC!!
        assertEquals("应选通向 C 的目标", c, toC.legs[0].warp!!.toMap)
        assertNull("复用房间出口 side 为空 = 踩格触发", toC.legs[0].warp!!.sideDir)
        assertEquals(CrossMapPathfinder.Warp(2, 2, null, c, 0, 0), toC.legs[0].warp)

        val toB = plan(
            CrossMapPathfinder.Pos(a, 2, 1),
            CrossMapPathfinder.Pos(b, 2, 2),
            mapOf(a to open(), b to open(), c to open()),
            links,
        )
        assertNotNull(toB)
        assertEquals(b, toB!!.legs[0].warp!!.toMap)
    }

    // 6) 多出口：选总步数更短的路线（A* 最优性）
    @Test
    fun picksShorterRouteAmongTwoExits() {
        val result = plan(
            CrossMapPathfinder.Pos(a, 0, 0),
            CrossMapPathfinder.Pos(b, 3, 2),
            mapOf(a to open(), b to open()),
            listOf(
                link(a, 4 to 2, "east", b, 0 to 2),   // A 侧 6 步 + B 侧 3 步
                link(a, 0 to 4, "south", b, 2 to 0),  // A 侧 4 步 + B 侧 3 步（更短）
            ),
        )
        assertNotNull(result)
        result!!
        assertEquals("应走更短的南出口", 0, result.legs[0].warp!!.exitX)
        assertEquals(4, result.legs[0].warp!!.exitY)
        assertEquals(7, result.totalSteps)
    }
}
