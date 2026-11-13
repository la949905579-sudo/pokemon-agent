package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * 跨图执行器离线单测：假世界（内存地图 + 记录按键），不读实机、不写文件。
 *
 * 覆盖：直连换图完成（含出口多按一步）、取消即停并且清键、换图后坐标异常失败。
 */
class CrossMapWalkerTest {

    private val a = 0x100
    private val b = 0x200

    private fun open(w: Int = 5, h: Int = 5): List<List<Int>> = List(h) { List(w) { 1 } }

    private fun link(map: Int, exit: Pair<Int, Int>, side: String?, toMap: Int, to: Pair<Int, Int>) =
        MapLink(map, exit.first, exit.second, side, toMap, to.first, to.second)

    private fun plan(tiles: Map<Int, List<List<Int>>>, links: List<MapLink>): CrossMapPathfinder.Plan {
        val p = CrossMapPathfinder.plan(
            CrossMapPathfinder.Pos(a, 1, 2),
            CrossMapPathfinder.Pos(b, 3, 2),
            tilesOf = { tiles[it] },
            linksFrom = { m -> links.filter { it.map == m } },
        )
        requireNotNull(p)
        return p
    }

    /**
     * 假世界：A → B 直连（side=east）。
     * 按方向键移动；站上出口格后朝 side 方向一步 / 踩上 side=null 的出口格 → 换图。
     */
    private class FakeWorld(
        private val tiles: Map<Int, List<List<Int>>>,
        private val links: List<MapLink>,
        var map: Int,
        var pos: Pair<Int, Int>,
    ) : CrossMapWalker.Io {
        var presses = 0
        var clearCount = 0
        var cancelledNow = false

        /** >0：第 N 次按键后进入取消状态（模拟施放/行走中被 closeKeys 打断）。 */
        var cancelAfterPresses = -1
        /** 非空：换图落点被改成这个值，模拟换图后坐标异常。 */
        var warpTargetOverride: MapLinkTarget? = null

        override fun readMapAddr(): Int = map
        override fun readPos(): Pair<Int, Int>? = pos

        override fun press(dir: String): Boolean {
            if (cancelledNow) return false
            presses++
            val d = when (dir) {
                "UP" -> 0 to -1
                "DOWN" -> 0 to 1
                "LEFT" -> -1 to 0
                else -> 1 to 0
            }
            val np = (pos.first + d.first) to (pos.second + d.second)
            // 踩格触发：目标格是 side=null 的出口
            val warpTile = links.firstOrNull {
                it.map == map && it.exitX == np.first && it.exitY == np.second &&
                    MapLinks.sideDir(it.side) == null
            }
            if (warpTile != null) {
                applyWarp(warpTile)
            } else {
                // 站上出口格后朝 side 方向一步触发
                val boundary = links.firstOrNull {
                    it.map == map && it.exitX == pos.first && it.exitY == pos.second &&
                        MapLinks.sideDir(it.side) == dir
                }
                if (boundary != null) applyWarp(boundary)
                else if (walkable(np)) pos = np
            }
            if (cancelAfterPresses > 0 && presses >= cancelAfterPresses) cancelledNow = true
            return !cancelledNow
        }

        private fun walkable(p: Pair<Int, Int>): Boolean =
            tiles[map]?.getOrNull(p.second)?.getOrNull(p.first) == 1

        private fun applyWarp(link: MapLink) {
            val target = warpTargetOverride ?: link.destinations().first()
            map = target.toMap
            pos = target.toX to target.toY
        }

        override fun sleep(ms: Long) = Unit
        override fun clearKeys() { clearCount++ }
        override fun cancelled(): Boolean = cancelledNow
    }

    private fun world(): FakeWorld = FakeWorld(
        tiles = mapOf(a to open(), b to open()),
        links = listOf(link(a, 4 to 2, "east", b, 0 to 2)),
        map = a,
        pos = 1 to 2,
    )

    // 1) 直连换图：走 3 步到出口 + 出口多按 1 步，落点 B(0,2)，再走 3 步到终点
    @Test
    fun directLinkWalkCompletes() {
        val w = world()
        val p = plan(mapOf(a to open(), b to open()), listOf(link(a, 4 to 2, "east", b, 0 to 2)))
        val r = CrossMapWalker.walk(p, w)
        assertTrue("应成功：$r", r is CrossMapWalker.Result.Ok)
        assertEquals(p.totalSteps + 1, (r as CrossMapWalker.Result.Ok).steps)   // +1 = 出口多按一步
        assertEquals(b, w.map)
        assertEquals(3 to 2, w.pos)
        assertTrue("结束时必须清键", w.clearCount >= 1)
    }

    // 2) 取消：走到一半被 closeKeys 打断 → Cancelled，立即停并清键
    @Test
    fun cancelMidRouteStopsAndClearsKeys() {
        val w = world()
        w.cancelAfterPresses = 2
        val p = plan(mapOf(a to open(), b to open()), listOf(link(a, 4 to 2, "east", b, 0 to 2)))
        val r = CrossMapWalker.walk(p, w)
        assertTrue("应取消：$r", r is CrossMapWalker.Result.Cancelled)
        assertTrue("取消后不应走完（按键 ${w.presses}）", w.presses < p.totalSteps + 1)
        assertTrue("取消必须清键", w.clearCount >= 1)
        assertEquals(a, w.map)   // 还没换图
    }

    // 3) 换图后坐标异常（落点被顶到别处）→ Failed(WARP_MISMATCH)
    @Test
    fun warpLandingMismatchFails() {
        val w = world()
        w.warpTargetOverride = MapLinkTarget(b, 4, 4)   // 与链接记录的落点 (0,2) 不符
        val p = plan(mapOf(a to open(), b to open()), listOf(link(a, 4 to 2, "east", b, 0 to 2)))
        val r = CrossMapWalker.walk(p, w)
        assertTrue("应失败：$r", r is CrossMapWalker.Result.Failed)
        assertEquals(CrossMapWalker.Reason.WARP_MISMATCH, (r as CrossMapWalker.Result.Failed).reason)
        assertEquals("pos", r.detail)
        assertTrue("失败也要清键", w.clearCount >= 1)
    }
}
