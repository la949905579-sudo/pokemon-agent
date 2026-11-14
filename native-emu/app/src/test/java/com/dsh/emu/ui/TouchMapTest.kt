package com.dsh.emu.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * [TouchMap] 纯逻辑单测：视口逆变换、招式/战斗/对话热区、地图目标格换算。
 * 不加载 native 库、不碰实机。
 */
class TouchMapTest {

    // ---------- 视图像素 → 游戏像素 ----------

    @Test
    fun viewToGame_landscapeFullscreen_centerIsGameCenter() {
        // 1920×1080，240×160 等比：scale=6.75，左右各留 150 黑边
        val p = TouchMap.viewToGame(1920, 1080, 960f, 540f)!!
        assertEquals(120f, p.x, 0.01f)
        assertEquals(80f, p.y, 0.01f)
    }

    @Test
    fun viewToGame_outsideLetterbox_returnsNull() {
        assertNull(TouchMap.viewToGame(1920, 1080, 100f, 540f))   // 左侧黑边
        assertNull(TouchMap.viewToGame(1920, 1080, 1850f, 540f))  // 右侧黑边
    }

    @Test
    fun viewToGame_portraitish_letterboxTopBottom() {
        // 1000×1000：scale=1000/240≈4.167，上下留边 → 顶部点在画面外
        assertNull(TouchMap.viewToGame(1000, 1000, 500f, 100f))
        val p = TouchMap.viewToGame(1000, 1000, 500f, 500f)!!
        assertEquals(120f, p.x, 0.01f)
        assertEquals(80f, p.y, 0.01f)
    }

    @Test
    fun viewToGame_zeroSize_returnsNull() {
        assertNull(TouchMap.viewToGame(0, 0, 0f, 0f))
    }

    // ---------- 招式 2×2 热区 ----------

    @Test
    fun moveZones_fourQuads() {
        assertEquals(0, TouchMap.moveIndexAt(40, 125))   // 左上
        assertEquals(1, TouchMap.moveIndexAt(110, 125))  // 右上
        assertEquals(2, TouchMap.moveIndexAt(40, 146))   // 左下
        assertEquals(3, TouchMap.moveIndexAt(110, 146))  // 右下
    }

    @Test
    fun moveZones_outsideOrOnInfoPane_returnsNull() {
        assertNull(TouchMap.moveIndexAt(160, 125))  // 右侧 PP/属性窗
        assertNull(TouchMap.moveIndexAt(40, 113))   // 顶边框
        assertNull(TouchMap.moveIndexAt(40, 158))   // 底边框
        assertNull(TouchMap.moveIndexAt(79, 125))   // 两列之间的缝
    }

    @Test
    fun moveZones_disjointAndInsideScreen() {
        for (i in TouchMap.MOVE_ZONES.indices) {
            val a = TouchMap.MOVE_ZONES[i]
            assertTrue(a.l < a.r && a.t < a.b)
            assertTrue(a.r <= TouchMap.GAME_W && a.b <= TouchMap.GAME_H)
            for (j in i + 1 until TouchMap.MOVE_ZONES.size) {
                val b = TouchMap.MOVE_ZONES[j]
                val overlap = a.l < b.r && b.l < a.r && a.t < b.b && b.t < a.b
                assertFalse("zone $i 与 $j 重叠", overlap)
            }
        }
    }

    // ---------- 战斗主菜单 / 对话 ----------

    @Test
    fun mainMenuZones_fourOptions() {
        assertEquals(0, TouchMap.mainMenuIndexAt(140, 125))  // 战斗（左上）
        assertEquals(1, TouchMap.mainMenuIndexAt(200, 125))  // 背包（右上）
        assertEquals(2, TouchMap.mainMenuIndexAt(140, 145))  // 宝可梦（左下）
        assertEquals(3, TouchMap.mainMenuIndexAt(200, 145))  // 逃跑（右下）
    }

    @Test
    fun mainMenuZones_outsideOptionBox_returnsNull() {
        assertNull(TouchMap.mainMenuIndexAt(60, 130))    // 左边对话框
        assertNull(TouchMap.mainMenuIndexAt(120, 130))   // 选项窗左边框
        assertNull(TouchMap.mainMenuIndexAt(140, 50))    // 画面上半
    }

    @Test
    fun mainMenuZones_disjointAndInsideScreen() {
        for (i in TouchMap.MAIN_ZONES.indices) {
            val a = TouchMap.MAIN_ZONES[i]
            assertTrue(a.l < a.r && a.t < a.b)
            assertTrue(a.r <= TouchMap.GAME_W && a.b <= TouchMap.GAME_H)
            for (j in i + 1 until TouchMap.MAIN_ZONES.size) {
                val b = TouchMap.MAIN_ZONES[j]
                val overlap = a.l < b.r && b.l < a.r && a.t < b.b && b.t < a.b
                assertFalse("main zone $i 与 $j 重叠", overlap)
            }
        }
    }

    @Test
    fun dialogTap_bottomArea() {
        assertTrue(TouchMap.isDialogTap(120, 130))
        assertFalse(TouchMap.isDialogTap(120, 60))
    }

    @Test
    fun submenuCancelTap_bagAndPartySeparately() {
        // 背包底部条 y≥114；队伍取消条从 y≥136 起（第 5 行格子到 127 为止，不能被抢走）
        assertTrue(TouchMap.isSubmenuCancelTap(1, 120, 130))
        assertTrue(TouchMap.isSubmenuCancelTap(1, 30, 114))
        assertFalse(TouchMap.isSubmenuCancelTap(1, 30, 113))
        assertTrue(TouchMap.isSubmenuCancelTap(2, 200, 140))
        assertTrue(TouchMap.isSubmenuCancelTap(2, 30, 136))
        assertFalse(TouchMap.isSubmenuCancelTap(2, 120, 130))   // 第 5 行格子区
        assertFalse(TouchMap.isSubmenuCancelTap(2, 30, 135))
        // 非子菜单（0=招式菜单 / 3=逃跑 / 其他）不算取消
        assertFalse(TouchMap.isSubmenuCancelTap(0, 120, 130))
        assertFalse(TouchMap.isSubmenuCancelTap(3, 120, 130))
    }

    // ---------- 战斗背包热区（2026-11-15 真机标定） ----------

    @Test
    fun bagArrows_doNotOverlapListOrCancel() {
        // ◀ 中心 (8,72)、▶ 中心 (72,72)，都在列表窗口 x≥88 之外、底部条 y≥114 之上
        assertTrue(TouchMap.BAG_LEFT_ARROW_ZONE.hit(8, 72))
        assertTrue(TouchMap.BAG_RIGHT_ARROW_ZONE.hit(72, 72))
        assertNull(TouchMap.bagRowAt(8, 72))
        assertNull(TouchMap.bagRowAt(72, 72))
        assertFalse(TouchMap.BAG_LEFT_ARROW_ZONE.hit(120, 130))
        assertFalse(TouchMap.BAG_RIGHT_ARROW_ZONE.hit(120, 130))
    }

    @Test
    fun bagRowAt_sixRowsInListWindow() {
        // win0 内区 x=88..232、y=8..104，行高 16
        assertEquals(0, TouchMap.bagRowAt(120, 8))
        assertEquals(0, TouchMap.bagRowAt(120, 23))
        assertEquals(1, TouchMap.bagRowAt(120, 24))
        assertEquals(2, TouchMap.bagRowAt(120, 40))
        assertEquals(5, TouchMap.bagRowAt(120, 103))
        assertNull(TouchMap.bagRowAt(120, 104))   // 窗口下沿
        assertNull(TouchMap.bagRowAt(87, 20))     // 窗口左外侧（背包图案）
        assertNull(TouchMap.bagRowAt(232, 20))    // 窗口右外侧
        assertNull(TouchMap.bagRowAt(120, 105))   // 列表下沿与底部条(y>=114)之间
        assertNull(TouchMap.bagRowAt(120, 113))
    }

    @Test
    fun bagScrollArrows_excludedFromRows() {
        // 滚动箭头中心 (160,8)/(160,104)，16×16：点它不选行（改由 scrollBag 挪一格），不能按 A
        assertNull(TouchMap.bagRowAt(160, 12))
        assertNull(TouchMap.bagRowAt(160, 100))
        assertTrue(TouchMap.BAG_SCROLL_UP_ZONE.hit(160, 8))
        assertTrue(TouchMap.BAG_SCROLL_DOWN_ZONE.hit(160, 104))
        // 箭头左右两侧仍是正常行
        assertEquals(0, TouchMap.bagRowAt(140, 12))
        assertEquals(5, TouchMap.bagRowAt(140, 100))
        assertFalse(TouchMap.BAG_SCROLL_UP_ZONE.hit(140, 12))
    }

    // ---------- 战斗队伍热区（PARTY_LAYOUT_SINGLE，2026-11-15 真机标定） ----------

    @Test
    fun partySlotAt_bigBoxAndFiveRows() {
        // 第 1 只：左侧大框 x=8..88、y=24..80
        assertEquals(0, TouchMap.partySlotAt(40, 50))
        assertEquals(0, TouchMap.partySlotAt(8, 24))
        assertNull(TouchMap.partySlotAt(40, 23))
        // 第 2..6 只：右侧 5 行，x=96..240，行高 24
        assertEquals(1, TouchMap.partySlotAt(150, 8))
        assertEquals(1, TouchMap.partySlotAt(150, 31))
        assertEquals(2, TouchMap.partySlotAt(150, 32))
        assertEquals(5, TouchMap.partySlotAt(150, 120))
        assertNull(TouchMap.partySlotAt(150, 128))   // 第 5 行下沿
        assertNull(TouchMap.partySlotAt(95, 20))     // 两列之间的缝
    }

    @Test
    fun partyCancelZone_doesNotStealLastRow() {
        // 取消按钮 win7=(24,17) 6×2 → x=192..240、y=136..152；第 5 行格子到 127
        assertTrue(TouchMap.PARTY_CANCEL_ZONE.hit(200, 140))
        assertFalse(TouchMap.PARTY_CANCEL_ZONE.hit(200, 127))
        assertEquals(5, TouchMap.partySlotAt(200, 127))
        assertNull(TouchMap.partySlotAt(200, 136))
    }

    // ---------- 地图目标格 ----------

    @Test
    fun mapTarget_tapOnAnchorIsSameTile() {
        assertEquals(10 to 10, TouchMap.mapTarget(10, 10, TouchMap.ANCHOR_X, TouchMap.ANCHOR_Y, 30, 30))
    }

    @Test
    fun mapTarget_tileOffsets() {
        // 锚点右侧 2 格 / 下方 1 格
        assertEquals(12 to 11, TouchMap.mapTarget(10, 10, TouchMap.ANCHOR_X + 32, TouchMap.ANCHOR_Y + 16, 40, 40))
        // 锚点左侧 2 格 / 上方 2 格
        assertEquals(8 to 8, TouchMap.mapTarget(10, 10, TouchMap.ANCHOR_X - 32, TouchMap.ANCHOR_Y - 32, 40, 40))
    }

    @Test
    fun mapTarget_outOfMap_returnsNull() {
        // 站在地图左上角，点左侧/上方 → 目标越界，不夹取
        assertNull(TouchMap.mapTarget(0, 0, TouchMap.ANCHOR_X - 32, TouchMap.ANCHOR_Y, 20, 20))
        assertNull(TouchMap.mapTarget(0, 0, TouchMap.ANCHOR_X, TouchMap.ANCHOR_Y - 32, 20, 20))
        // 右下角同理
        assertNull(TouchMap.mapTarget(19, 19, TouchMap.ANCHOR_X + 32, TouchMap.ANCHOR_Y, 20, 20))
    }

    @Test
    fun mapTarget_emptyMap_returnsNull() {
        assertNull(TouchMap.mapTarget(0, 0, 120, 88, 0, 0))
    }
}
