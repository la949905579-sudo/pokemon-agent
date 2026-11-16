package com.dsh.emu.game

import org.json.JSONObject
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** 遭遇表摘要离线单测：纯函数 + 测试注入，不读 APK 资产。 */
class EncountersTest {

    @After
    fun tearDown() {
        Encounters.resetForTest()
    }

    @Test
    fun summaryGroupsSpeciesAndLevels() {
        val entry = JSONObject(
            """
            {"land":{"slots":[
              {"species":16,"min":2,"max":5,"chance":20},
              {"species":16,"min":3,"max":4,"chance":20},
              {"species":19,"min":2,"max":2,"chance":30}]},
             "water":{"slots":[{"species":129,"min":5,"max":10,"chance":60}]},
             "rock_smash":{"slots":[{"species":74,"min":30,"max":40,"chance":60}]},
             "fishing":{"rods":{
               "old_rod":[{"species":129,"min":5,"max":5,"chance":70}],
               "super_rod":[{"species":130,"min":20,"max":30,"chance":60}]}}}
            """
        )
        // 同种按等级区间合并；分类顺序 陆/水/碎岩/钓
        assertEquals(
            "陆 波波2-5/小拉达2；水 鲤鱼王5-10；碎岩 小拳石30-40；钓 鲤鱼王5/暴鲤龙20-30",
            Encounters.summaryOf(entry),
        )
    }

    @Test
    fun unknownSpeciesUsesIdFallback() {
        val entry = JSONObject("""{"land":{"slots":[{"species":999,"min":5,"max":5}]}}""")
        assertEquals("陆 #9995", Encounters.summaryOf(entry))
    }

    @Test
    fun summaryPicksFirstMapWithEncounters() {
        Encounters.putJsonForTest(
            """{"maps":{
                 "MAP_X":{"land":{"slots":[{"species":16,"min":2,"max":3}]}},
                 "MAP_Y":{"water":{"slots":[{"species":129,"min":5,"max":5}]}}}}"""
        )
        assertEquals("陆 波波2-3", Encounters.summary(listOf("MAP_MISSING", "MAP_X")))
        // 缓存命中后再查同一张图仍一致
        assertEquals("陆 波波2-3", Encounters.summary(listOf("MAP_X")))
    }

    @Test
    fun summaryEmptyWhenNoData() {
        Encounters.putJsonForTest("""{"maps":{}}""")
        assertEquals("", Encounters.summary(emptyList()))
        assertEquals("", Encounters.summary(listOf("MAP_NONE")))
        assertTrue(Encounters.summaryOf(null).isEmpty())
    }
}
