package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** 名表 232（金属爪）收录：战斗页第 4 招不应再显示占位 "#232"。 */
class MoveName232Test {

    @Test
    fun move232HasChineseName() {
        val move = GameData.moves[232]
        assertNotNull("GameData.moves 缺 232", move)
        val (name, type, power) = move!!
        assertTrue("232 名字为空", name.isNotBlank())
        assertFalse("232 仍是占位名", name == "#232")
        assertEquals("金属爪", name)
        assertEquals("钢", type)
        assertEquals(50, power)
    }

    @Test
    fun everyMoveNameIsNonEmpty() {
        GameData.moves.forEach { (id, info) ->
            assertTrue("招式 $id 名字为空", info.first.isNotBlank())
        }
    }
}
