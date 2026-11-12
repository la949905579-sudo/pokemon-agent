package com.dsh.emu.ui

import com.dsh.emu.game.MoveCaster
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * 施放线程机械逻辑的离线单测：假 setKeys / sleep，不加载 native 库、不碰 Android。
 *
 * 覆盖：方向 → 按键掩码；取消（closeKeys 代际路径）后不按键 / 提前松键；
 * 正常按住结束必清键；InterruptedException 也必须清键。
 */
class MoveCastThreadTest {

    /** 假按键/睡眠：记录调用序列，不碰 JNI。 */
    private class FakeJni {
        val masks = mutableListOf<Int>()
        val sleeps = mutableListOf<Long>()

        fun setKeys(mask: Int) {
            masks.add(mask)
        }

        fun sleep(ms: Long) {
            sleeps.add(ms)
        }
    }

    @Test
    fun maskOfMapsGridDirectionsToGbaMasks() {
        // GBA 掩码：RIGHT=16 LEFT=32 UP=64 DOWN=128（与 EmuCore.KEY_* 一致）
        assertEquals(64, MoveCastThread.maskOf(MoveCaster.Dir.UP))
        assertEquals(128, MoveCastThread.maskOf(MoveCaster.Dir.DOWN))
        assertEquals(32, MoveCastThread.maskOf(MoveCaster.Dir.LEFT))
        assertEquals(16, MoveCastThread.maskOf(MoveCaster.Dir.RIGHT))
    }

    @Test
    fun cancelledBeforePressPressesNothing() {
        val jni = FakeJni()
        MoveCastThread.press(64, 300, { true }, jni::setKeys, jni::sleep)
        assertTrue("取消后不应按键：${jni.masks}", jni.masks.isEmpty())
        assertTrue("取消后不应等待：${jni.sleeps}", jni.sleeps.isEmpty())
    }

    @Test
    fun closeKeysGenerationCancelReleasesAfterFirstSlice() {
        // 模拟 closeKeys()：press 进行中 BattleMoveAction.cancel() 把代际 +1。
        val jni = FakeJni()
        val myGen = 1
        var generation = myGen
        val sleep: (Long) -> Unit = { ms ->
            jni.sleep(ms)
            generation++   // closeKeys 发生在这一个 20ms 切片之后
        }
        MoveCastThread.press(64, 300, { myGen != generation }, jni::setKeys, sleep)

        assertEquals("按下后必须松开", listOf(64, 0), jni.masks)
        assertEquals("取消后只再等 1 个切片", 1, jni.sleeps.size)
        assertEquals(MoveCastThread.SLICE_MS, jni.sleeps[0])
    }

    @Test
    fun normalPressHoldsThenReleases() {
        val jni = FakeJni()
        MoveCastThread.press(1, 60, { false }, jni::setKeys, jni::sleep)
        assertEquals(listOf(1, 0), jni.masks)
        assertEquals("等待总时长不变", 60L, jni.sleeps.sum())
    }

    @Test
    fun interruptedSleepReturnsFalseAndStillClearsKeys() {
        val jni = FakeJni()
        MoveCastThread.press(128, 300, { false }, jni::setKeys) {
            throw InterruptedException("test")
        }
        assertEquals("异常也必须清键", listOf(128, 0), jni.masks)
    }

    @Test
    fun sleepInterruptiblyStopsAtCancellation() {
        var cancelled = false
        val slept = mutableListOf<Long>()
        val done = MoveCastThread.sleepInterruptibly(100, { cancelled }) { ms ->
            slept.add(ms)
            cancelled = true
        }
        assertFalse(done)
        assertEquals(1, slept.size)
        assertEquals(MoveCastThread.SLICE_MS, slept[0])
    }

    @Test
    fun sleepInterruptiblyCompletesWithoutCancellation() {
        val slept = mutableListOf<Long>()
        val done = MoveCastThread.sleepInterruptibly(50, { false }) { ms -> slept.add(ms) }
        assertTrue(done)
        assertEquals(50L, slept.sum())
    }
}
