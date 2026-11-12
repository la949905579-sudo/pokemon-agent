package com.dsh.emu.ui

import org.junit.Assert.assertEquals
import org.junit.Test

/** 离线单测：设置页重置操作的提示文案。 */
class ActionHintsTest {

    @Test
    fun noRomAsksToLoadFirst() {
        assertEquals("先载入 ROM", ActionHints.reset(romReady = false, ok = false))
    }

    @Test
    fun successSaysReset() {
        assertEquals("已重置", ActionHints.reset(romReady = true, ok = true))
    }

    @Test
    fun failureSaysResetFailed() {
        assertEquals("重置失败", ActionHints.reset(romReady = true, ok = false))
    }
}
