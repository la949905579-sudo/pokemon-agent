package com.dsh.emu.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * 状态 JSON 解析器离线单测：纯函数，不读实机、不写文件。
 *
 * 覆盖：空串/非法 JSON 回退默认；基本字段；队伍详情（缺字段回退）；小地图 tiles（含损坏行）；
 * 战斗详情（foe/me/招式列表）；`{}` 缺字段默认值。
 */
class StatusParserTest {

    @Test
    fun blankAndInvalidJsonFallBackToDefaults() {
        assertEquals(EmuStatus(), parseStatus(""))
        assertEquals(EmuStatus(), parseStatus("   "))
        assertEquals(EmuStatus(), parseStatus("not-json"))
        assertEquals(EmuStatus(), parseStatus("{"))
    }

    @Test
    fun parsesMapAndBasicFields() {
        val s = parseStatus("""{"map":"map_pallet","x":5,"y":7,"battle":"battle_moves"}""")
        assertEquals("map_pallet", s.map)
        assertEquals(5, s.x)
        assertEquals(7, s.y)
        assertEquals("battle_moves", s.battle)
        assertTrue("无队伍数据", s.team.isEmpty())
        assertNull("无小地图", s.mmTiles)
    }

    @Test
    fun parsesTeamWithMovesAndMissingOptionalFields() {
        val s = parseStatus(
            """
            {"team":[
              {"name":"皮卡丘","lv":12,"hp":35,"max":40,"types":["电"],
               "moves":[{"name":"电击","pp":30,"max":35},{"name":"电磁波"}],
               "exp":1234,"expCur":1000,"expNext":1500},
              {"lv":5,"hp":10,"max":12}
            ]}
            """.trimIndent()
        )
        assertEquals(2, s.team.size)

        val pika = s.team[0]
        assertEquals("皮卡丘", pika.name)
        assertEquals(12, pika.lv)
        assertEquals(35, pika.hp)
        assertEquals(40, pika.max)
        assertEquals(listOf("电"), pika.types)
        assertEquals(2, pika.moves.size)
        assertEquals("电击", pika.moves[0].name)
        assertEquals(30, pika.moves[0].pp)
        assertEquals(35, pika.moves[0].maxPp)
        assertEquals("电磁波", pika.moves[1].name)
        assertEquals("缺 pp 回退 -1", -1, pika.moves[1].pp)
        assertNull("缺 max 回退 null", pika.moves[1].maxPp)
        assertEquals(1234L, pika.exp)
        assertEquals(1000L, pika.expCur)
        assertEquals(1500L, pika.expNext)

        val bare = s.team[1]
        assertEquals("缺 name 回退 ?", "?", bare.name)
        assertEquals(5, bare.lv)
        assertEquals(10, bare.hp)
        assertEquals(12, bare.max)
        assertTrue(bare.types.isEmpty())
        assertTrue(bare.moves.isEmpty())
        assertEquals("缺 exp 回退 -1", -1L, bare.exp)
        assertEquals(-1L, bare.expCur)
        assertEquals(-1L, bare.expNext)
    }

    @Test
    fun parsesMinimapTilesAndSkipsBrokenRows() {
        val s = parseStatus(
            """{"minimap":{"w":3,"h":2,"px":1,"py":2,"tiles":[[1,0,1],null,[2,2,2]]}}"""
        )
        assertEquals(3, s.mmW)
        assertEquals(2, s.mmH)
        assertEquals(1, s.mmPx)
        assertEquals(2, s.mmPy)
        assertEquals(listOf(listOf(1, 0, 1), listOf(2, 2, 2)), s.mmTiles)
    }

    @Test
    fun parsesBattleDetail() {
        val s = parseStatus(
            """
            {"battle":"battle_anim",
             "battle_detail":{
               "foe":{"lv":9,"hp":20,"mhp":24},
               "me":{"lv":12,"hp":35,"mhp":40,"moves":["电击","电磁波"]}
             }}
            """.trimIndent()
        )
        assertEquals("battle_anim", s.battle)
        assertEquals(9, s.foeLv)
        assertEquals(20, s.foeHp)
        assertEquals(24, s.foeMax)
        assertEquals(12, s.meLv)
        assertEquals(35, s.meHp)
        assertEquals(40, s.meMax)
        assertEquals(listOf("电击", "电磁波"), s.moves)
    }

    @Test
    fun emptyObjectUsesAllDefaults() {
        val s = parseStatus("{}")
        assertEquals(EmuStatus(), s)
    }
}
