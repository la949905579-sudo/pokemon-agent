package com.dsh.emu.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.time.ZoneId

/** 离线单测：存档卡槽的文件名 / 空槽文案 / 时间格式。 */
class SaveSlotsTest {

    @get:Rule
    val tmp = TemporaryFolder()

    @Test
    fun fileNameIsStateNSav() {
        assertEquals("state1.sav", SaveSlots.file(tmp.root, 1).name)
        assertEquals("state3.sav", SaveSlots.file(tmp.root, 3).name)
    }

    @Test
    fun emptySlotLabel() {
        assertEquals("槽 2 · 空", SaveSlots.label(tmp.root, 2))
    }

    @Test
    fun existingSlotLabelUsesFileTime() {
        val f = SaveSlots.file(tmp.root, 1)
        f.writeText("fake state")
        val zone = ZoneId.of("UTC")
        assertEquals("槽 1 · " + SaveSlots.formatTime(f.lastModified(), zone),
            SaveSlots.label(tmp.root, 1, zone))
    }

    @Test
    fun formatTimeFixedInstant() {
        // 2026-11-12T17:05:00Z
        assertEquals("2026-11-12 17:05", SaveSlots.formatTime(1_794_503_100_000L, ZoneId.of("UTC")))
    }

    @Test
    fun slotRangeIsOneToThree() {
        assertFalse(SaveSlots.exists(tmp.root, 0))
        assertFalse(SaveSlots.exists(tmp.root, 4))
        SaveSlots.file(tmp.root, 2).writeText("x")
        assertTrue(SaveSlots.exists(tmp.root, 2))
    }

    @Test
    fun emptySlotActionsRunWithoutConfirm() {
        // 空槽：三个操作都直接执行（各自负责给「空槽」提示），不用二次确认
        for (a in listOf(SlotAction.SAVE, SlotAction.LOAD, SlotAction.DELETE)) {
            assertTrue(SlotConfirm.shouldRunNow(a, 1, null, hasSave = false))
        }
    }

    @Test
    fun destructiveActionsNeedSecondClickOnSameSlot() {
        // 有档：覆盖存档 / 读取 / 删除第一次都只进确认态
        for (a in listOf(SlotAction.SAVE, SlotAction.LOAD, SlotAction.DELETE)) {
            assertFalse(SlotConfirm.shouldRunNow(a, 2, null, hasSave = true))
        }
        // 第二次点同一操作同一槽 → 执行
        for (a in listOf(SlotAction.SAVE, SlotAction.LOAD, SlotAction.DELETE)) {
            assertTrue(SlotConfirm.shouldRunNow(a, 2, a to 2, hasSave = true))
        }
        // 换了槽或换了操作都不算确认
        assertFalse(SlotConfirm.shouldRunNow(SlotAction.LOAD, 3, SlotAction.LOAD to 2, hasSave = true))
        assertFalse(SlotConfirm.shouldRunNow(SlotAction.DELETE, 2, SlotAction.LOAD to 2, hasSave = true))
        assertFalse(SlotConfirm.shouldRunNow(SlotAction.SAVE, 2, SlotAction.DELETE to 2, hasSave = true))
    }
}
