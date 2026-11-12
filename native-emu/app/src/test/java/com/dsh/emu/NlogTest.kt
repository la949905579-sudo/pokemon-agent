package com.dsh.emu

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.CyclicBarrier

/** 离线单测：Nlog 的行格式 / 值清洗 / 滚动与限流判定。 */
class NlogTest {

    @Test
    fun buildLineMatchesObservabilityFormat() {
        val line = Nlog.buildLine(
            Nlog.Level.INFO, "bridge.conn",
            listOf("ok" to true, "port" to 55401),
            "2026-11-12T05:30:12Z",
        )
        // 级别补齐 5 宽 + 一个空格 → INFO 后两个空格
        assertEquals("2026-11-12T05:30:12Z INFO  bridge.conn ok=true port=55401", line)
    }

    @Test
    fun buildLineWarnAndNoFields() {
        assertEquals("2026-11-12T05:30:12Z WARN  emu.frame.stall",
            Nlog.buildLine(Nlog.Level.WARN, "emu.frame.stall", emptyList(), "2026-11-12T05:30:12Z"))
    }

    @Test
    fun cleanFlattensWhitespace() {
        assertEquals("a b c d", Nlog.clean("a\nb\r\nc\td"))
        assertEquals("前后空格压平", Nlog.clean(" 前后空格压平 "))
    }

    @Test
    fun cleanEmptyBecomesDash() {
        assertEquals("-", Nlog.clean(null))
        assertEquals("-", Nlog.clean(""))
        assertEquals("-", Nlog.clean("   "))
    }

    @Test
    fun cleanTruncatesLongValue() {
        val raw = "x".repeat(500)
        val out = Nlog.clean(raw)
        assertEquals(Nlog.MAX_VALUE_CHARS, out.length)
        assertTrue(out.all { it == 'x' })
    }

    @Test
    fun shouldRotateOnlyAboveLimit() {
        assertFalse(Nlog.shouldRotate(Nlog.MAX_BYTES))
        assertTrue(Nlog.shouldRotate(Nlog.MAX_BYTES + 1))
        assertFalse(Nlog.shouldRotate(0))
    }

    @Test
    fun throttleWindow() {
        // 没记录过 → 放行
        assertTrue(Nlog.shouldLogThrottled(null, 1_000))
        // 窗口内 → 拒绝
        assertFalse(Nlog.shouldLogThrottled(1_000, 1_000))
        assertFalse(Nlog.shouldLogThrottled(1_000, 10_999))
        // 到点 / 超时 → 放行
        assertTrue(Nlog.shouldLogThrottled(1_000, 11_000))
        assertTrue(Nlog.shouldLogThrottled(1_000, 11_001))
    }

    @Test
    fun levelFilterDefaultsToInfo() {
        assertTrue(Nlog.shouldEmit(Nlog.Level.INFO, Nlog.Level.INFO))
        assertTrue(Nlog.shouldEmit(Nlog.Level.ERROR, Nlog.Level.INFO))
        assertFalse(Nlog.shouldEmit(Nlog.Level.DEBUG, Nlog.Level.INFO))
    }

    @Test
    fun throttlePassSequentialWindow() {
        val key = "seq-" + System.nanoTime()
        assertTrue(Nlog.throttlePass(key, 1_000))
        assertFalse(Nlog.throttlePass(key, 5_000))
        assertTrue(Nlog.throttlePass(key, 11_000))
        assertFalse(Nlog.throttlePass(key, 12_000))
    }

    @Test
    fun throttlePassIsAtomicUnderConcurrency() {
        // 16 个线程同时抢同一个 key：同一个窗口内只能有一个 true（旧 get→put 实现可能多个）
        val key = "atomic-" + System.nanoTime()
        val n = 16
        val barrier = CyclicBarrier(n)
        val results = BooleanArray(n)
        val threads = (0 until n).map { i ->
            Thread {
                try { barrier.await() } catch (_: Throwable) {}
                results[i] = Nlog.throttlePass(key, 5_000)
            }
        }
        threads.forEach { it.start() }
        threads.forEach { it.join(5_000) }
        assertEquals(1, results.count { it })
    }
}
