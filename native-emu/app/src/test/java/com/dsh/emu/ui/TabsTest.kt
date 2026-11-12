package com.dsh.emu.ui

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** 离线单测：右侧 Tab 是否可点（「地图」Tab 暂置灰）。 */
class TabsTest {

    @Test
    fun mapTabIsDisabledOthersEnabled() {
        assertFalse(isPageTabEnabled(Page.MAP))
        assertTrue(isPageTabEnabled(Page.TEAM))
        assertTrue(isPageTabEnabled(Page.BAG))
        assertTrue(isPageTabEnabled(Page.NICK))
        assertTrue(isPageTabEnabled(Page.DEX))
        assertTrue(isPageTabEnabled(Page.SAVE))
        assertTrue(isPageTabEnabled(Page.OPTION))
    }
}
