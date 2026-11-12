package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import java.io.File

/** 离线单测：成长公式 / ROM BaseStats 定位 / 回退表 / 升级进度。 */
class GrowthTest {

    @Before
    fun setUp() {
        Growth.resetForTest()
    }

    @Test
    fun expForLevelMatchesGen3MaxValues() {
        // 100 级总经验（Gen III 官方表）：0 中快 / 1 无规律 / 2 波动 / 3 中慢 / 4 快 / 5 慢
        val expected = longArrayOf(1_000_000, 600_000, 1_640_000, 1_059_860, 800_000, 1_250_000)
        for (rate in 0..5) assertEquals("rate=$rate", expected[rate], Growth.expForLevel(rate, 100))
        // 官方表里 0/1 级就是 0/1
        for (rate in 0..5) {
            assertEquals(0L, Growth.expForLevel(rate, 0))
            assertEquals(1L, Growth.expForLevel(rate, 1))
        }
    }

    @Test
    fun expForLevelLevel2() {
        assertEquals(8L, Growth.expForLevel(0, 2))     // 2^3
        assertEquals(15L, Growth.expForLevel(1, 2))    // (100-2)*8/50
        assertEquals(4L, Growth.expForLevel(2, 2))     // ((2+1)/3+24)*8/50
        assertEquals(9L, Growth.expForLevel(3, 2))     // 6*8/5-15*4+200-140
        assertEquals(6L, Growth.expForLevel(4, 2))     // 4*8/5
        assertEquals(10L, Growth.expForLevel(5, 2))    // 5*8/4
    }

    @Test
    fun locateBaseStatsFindsTable() {
        val rom = ByteArray(512)
        val bulbasaur = byteArrayOf(45, 49, 49, 45, 65, 65, 12, 3, 45, 64)
        val charmander = byteArrayOf(39, 52, 43, 65, 60, 50, 10, 10)
        System.arraycopy(bulbasaur, 0, rom, 64, bulbasaur.size)
        System.arraycopy(charmander, 0, rom, 64 + 3 * Growth.STRIDE, charmander.size)
        assertEquals(64, Growth.locateBaseStats(rom))
    }

    @Test
    fun locateBaseStatsRejectsWrongStride() {
        val rom = ByteArray(512)
        val bulbasaur = byteArrayOf(45, 49, 49, 45, 65, 65, 12, 3, 45, 64)
        System.arraycopy(bulbasaur, 0, rom, 64, bulbasaur.size)
        // 少了第 4 条小火龙，不能确认表起点
        assertEquals(-1, Growth.locateBaseStats(rom))
    }

    @Test
    fun fallbackRatesWhenNoRom() {
        assertEquals(3, Growth.growthRateOf(1))     // 妙蛙种子 中慢
        assertEquals(0, Growth.growthRateOf(25))    // 皮卡丘 中快
        assertEquals(5, Growth.growthRateOf(129))   // 鲤鱼王 慢
        assertEquals(5, Growth.growthRateOf(150))   // 超梦 慢
        assertNull(Growth.growthRateOf(0))
        assertNull(Growth.growthRateOf(152))
    }

    @Test
    fun prepareReadsRatesFromSyntheticRom() {
        val speciesCount = 151
        val base = 100
        val rom = ByteArray(base + speciesCount * Growth.STRIDE + Growth.GROWTH_OFFSET + 8)
        val bulbasaur = byteArrayOf(45, 49, 49, 45, 65, 65, 12, 3, 45, 64)
        val charmander = byteArrayOf(39, 52, 43, 65, 60, 50, 10, 10)
        System.arraycopy(bulbasaur, 0, rom, base, bulbasaur.size)
        System.arraycopy(charmander, 0, rom, base + 3 * Growth.STRIDE, charmander.size)
        // 物种 1 = 中慢(3)，物种 25 = 快(4)（故意和回退表不同，验证 ROM 优先）
        rom[base + Growth.GROWTH_OFFSET] = 3
        rom[base + 24 * Growth.STRIDE + Growth.GROWTH_OFFSET] = 4
        val f = File.createTempFile("fake-rom", ".gba")
        try {
            f.writeBytes(rom)
            Growth.prepare(f)
            assertEquals(3, Growth.growthRateOf(1))
            assertEquals(4, Growth.growthRateOf(25))
        } finally {
            f.delete()
        }
    }

    @Test
    fun progressUsesCurrentAndNextLevel() {
        // 回退表：皮卡丘 = 中快(0)
        val p = Growth.progress(25, 10, 1200)!!
        assertEquals(1000L, p.cur)    // 10^3
        assertEquals(1331L, p.next)   // 11^3
        assertEquals(200f / 331f, p.ratio, 0.0001f)
    }

    @Test
    fun progressNullWhenDataMissing() {
        assertNull(Growth.progress(25, 100, 1_000_000))  // 满级
        assertNull(Growth.progress(0, 5, 100))           // 未知物种
        assertNull(Growth.progress(25, 5, -1))           // 读不到经验
    }
}
