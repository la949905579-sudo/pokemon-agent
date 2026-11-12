package com.dsh.emu.ui

import org.junit.Assert.assertEquals
import org.junit.Test

/** 离线单测：行走预览折线点。 */
class WalkPreviewTest {

    @Test
    fun emptyStepsYieldsOnlyStart() {
        assertEquals(listOf(3 to 4), previewPoints(3, 4, emptyList()))
    }

    @Test
    fun stepsAdvanceByDirection() {
        // UP/RIGHT/DOWN/LEFT 各一步应回到起点
        val pts = previewPoints(10, 10, listOf("UP", "RIGHT", "DOWN", "LEFT"))
        assertEquals(
            listOf(10 to 10, 10 to 9, 11 to 9, 11 to 10, 10 to 10),
            pts,
        )
    }

    @Test
    fun pathEndsAtExpectedTile() {
        val pts = previewPoints(5, 5, listOf("DOWN", "DOWN", "RIGHT"))
        assertEquals(5 to 5, pts.first())
        assertEquals(6 to 7, pts.last())
        assertEquals(4, pts.size)
    }
}
