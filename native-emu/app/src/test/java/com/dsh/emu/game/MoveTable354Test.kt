package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** 354 招式名表完整性（Gen3 火红/叶绿；数据源 tools/gen_moves_data.py）。 */
class MoveTable354Test {

    @Test
    fun hasAllGen3Moves() {
        assertEquals("招式表应为 354 条", 354, GameData.moves.size)
    }

    @Test
    fun everyIdPresent() {
        for (id in 1..354) {
            assertNotNull("缺招式 $id", GameData.moves[id])
        }
    }

    @Test
    fun spotChecks() {
        // 数据源：PokeAPI zh-Hans（官方译名，与 ROM「官译修正」一致）
        assertEquals(Triple("拍击", "一般", 40), GameData.moves[1])
        assertEquals(Triple("金属爪", "钢", 50), GameData.moves[232])
        assertEquals(Triple("破坏光线", "一般", 150), GameData.moves[63])
    }

    @Test
    fun namesAreChineseNotPlaceholders() {
        GameData.moves.forEach { (id, info) ->
            assertTrue("招式 $id 名字为空", info.first.isNotBlank())
            assertTrue("招式 $id 仍是占位名", !info.first.startsWith("#"))
        }
    }
}
