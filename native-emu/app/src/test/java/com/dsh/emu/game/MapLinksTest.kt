package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** 地图连接表离线单测：解析（side/targets/reused/坏条目跳过）与 side 方向映射。 */
class MapLinksTest {

    @Test
    fun parseKeepsSideTargetsAndSkipsBadEntries() {
        val json = """
            [
             {"map": 256, "exit": [4, 2], "side": "east", "to_map": 512, "to_pos": [0, 2]},
             {"map": 256, "exit": [2, 2], "side": null, "to_map": 512, "to_pos": [0, 0],
              "reused": true,
              "targets": [{"to_map": 768, "to_pos": [1, 1]}, {"to_map": 512, "to_pos": [0, 0]}]},
             {"map": 0, "exit": [1, 1], "to_map": 512, "to_pos": [0, 0]},
             {"map": 256, "exit": [1, 1], "to_map": 0, "to_pos": [0, 0]}
            ]
        """.trimIndent()
        val links = MapLinks.parse(json)
        assertEquals("坏条目应跳过", 2, links.size)

        val l0 = links[0]
        assertEquals(256, l0.map)
        assertEquals(4, l0.exitX)
        assertEquals(2, l0.exitY)
        assertEquals("east", l0.side)
        assertEquals(listOf(MapLinkTarget(512, 0, 2)), l0.destinations())

        val l1 = links[1]
        assertNull("显式 null side 读成 null", l1.side)
        assertTrue(l1.reused)
        assertEquals(
            listOf(MapLinkTarget(768, 1, 1), MapLinkTarget(512, 0, 0)),
            l1.destinations(),
        )
    }

    @Test
    fun sideDirMapsKnownSides() {
        assertEquals("UP", MapLinks.sideDir("north"))
        assertEquals("UP", MapLinks.sideDir("top"))
        assertEquals("UP", MapLinks.sideDir("up"))
        assertEquals("DOWN", MapLinks.sideDir("south"))
        assertEquals("DOWN", MapLinks.sideDir("bottom"))
        assertEquals("RIGHT", MapLinks.sideDir("east"))
        assertEquals("LEFT", MapLinks.sideDir("west"))
        assertNull(MapLinks.sideDir(null))
        assertNull(MapLinks.sideDir(""))
        assertNull(MapLinks.sideDir("diagonal"))
    }
}
