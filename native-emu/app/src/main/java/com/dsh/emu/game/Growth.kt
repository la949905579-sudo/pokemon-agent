package com.dsh.emu.game

import android.util.Log
import java.io.File
import java.time.Instant
import java.time.temporal.ChronoUnit

/**
 * 升级经验阈值（Gen III）。
 *
 * 优先级：
 *  1. 从 ROM 的 BaseStats 表读「成长类型」：每个种族固定 28 字节，成长类型在结构 +0x13。
 *     表位置因 ROM 而异，所以不硬编码地址：用「妙蛙种子特征串」扫描定位，
 *     再用小火龙（第 4 条记录，+3*28）二次校验。本机火红/叶绿实测命中文件偏移 0x25477C，
 *     成长类型核对过：妙蛙种子=中慢(3)、皮卡丘=中快(0)、鲤鱼王/超梦=慢(5)。
 *  2. ROM 读不到/校验失败 → 回退下面的标准表（Kanto 151 的成长类型，见 FALLBACK_RATES 注释）。
 *  3. 都失败 → 返回 null，UI 显示 --，不崩。
 */
object Growth {
    const val STRIDE = 28
    const val GROWTH_OFFSET = 0x13

    /** 妙蛙种子 BaseStats 前 10 字节（HP/攻/防/速/特攻/特防/属性1/属性2/捕获率/基础经验）。 */
    private val BULBASAUR_SIG = byteArrayOf(45, 49, 49, 45, 65, 65, 12, 3, 45, 64)

    /** 小火龙（第 4 条记录）前 8 字节，用来确认表起点没错位。 */
    private val CHARMANDER_SIG = byteArrayOf(39, 52, 43, 65, 60, 50, 10, 10)

    /**
     * Kanto 151 成长类型回退表：0=中快 1=无规律 2=波动 3=中慢 4=快 5=慢。
     * 来源：本地火红/叶绿 ROM 的 BaseStats 表提取（抽样核对见类注释）。
     * 它不是通用真源：换 ROM 时优先走第 1 条从 ROM 读，这张表只在 ROM 扫描失败时兜底。
     */
    private const val FALLBACK_RATES =
        "3333333330000003330000000000333333440044003330000000000005533333333333355333000000000000055333000000055000000055400000055000005555500000000005555555553"

    private const val TAG = "native-emu"
    private const val LOG_PATH = "/sdcard/Download/emu_native.log"

    /** 从 ROM 读到的 151 条成长类型；null=没读到，走回退表。 */
    @Volatile
    private var romRates: ByteArray? = null

    /** 升级进度：当前经验 / 当前等级下限 / 下一级阈值。 */
    data class Progress(val exp: Long, val cur: Long, val next: Long) {
        /** 0..1；数据异常返回 0。 */
        val ratio: Float
            get() {
                val span = next - cur
                if (span <= 0) return 0f
                val got = (exp - cur).coerceIn(0, span)
                return got.toFloat() / span
            }
    }

    @Synchronized
    fun resetForTest() {
        romRates = null
    }

    /** 读 ROM、定位 BaseStats、缓存 151 条成长类型。放后台线程调用（要扫 16MB）。 */
    fun prepare(rom: File) {
        try {
            val bytes = rom.readBytes()
            val base = locateBaseStats(bytes)
            if (base < 0) {
                romRates = null
                warn("growth.rom stage=locate ok=false code=not_found")
                return
            }
            val rates = ByteArray(151)
            for (i in 0 until 151) {
                val off = base + i * STRIDE + GROWTH_OFFSET
                rates[i] = if (off < bytes.size) bytes[off] else 0
            }
            romRates = rates
            warn("growth.rom stage=locate ok=true base=0x%x bulbasaur=%d pikachu=%d"
                .format(base, rates[0].toInt(), rates[24].toInt()))
        } catch (e: Throwable) {
            romRates = null
            warn("growth.rom stage=read ok=false code=${e.javaClass.simpleName}")
        }
    }

    /** 在 ROM 字节里定位 BaseStats 表；返回第 1 条记录的偏移，找不到返回 -1。纯函数。 */
    fun locateBaseStats(rom: ByteArray): Int {
        var i = 0
        val max = rom.size - BULBASAUR_SIG.size
        while (i <= max) {
            if (rom[i] == BULBASAUR_SIG[0] && matches(rom, i, BULBASAUR_SIG)) {
                val charmander = i + 3 * STRIDE
                if (matches(rom, charmander, CHARMANDER_SIG)) return i
            }
            i++
        }
        return -1
    }

    private fun matches(rom: ByteArray, at: Int, sig: ByteArray): Boolean {
        if (at < 0 || at + sig.size > rom.size) return false
        for (k in sig.indices) if (rom[at + k] != sig[k]) return false
        return true
    }

    /** 该物种的成长类型（0..5）；拿不到返回 null。 */
    fun growthRateOf(species: Int): Int? {
        if (species !in 1..151) return null
        romRates?.let { return it[species - 1].toInt().takeIf { r -> r in 0..5 } }
        val ch = FALLBACK_RATES.getOrNull(species - 1) ?: return null
        return (ch - '0').takeIf { it in 0..5 }
    }

    /** 升到 level 所需总经验（Gen III 官方公式；0/1 级按官方表里的 0/1 处理）。 */
    fun expForLevel(rate: Int, level: Int): Long {
        val n = level.coerceIn(0, 100)
        if (n <= 1) return n.toLong()
        val cube = n.toLong() * n * n
        return when (rate) {
            0 -> cube                                              // 中快
            1 -> when {                                            // 无规律
                n <= 50 -> (100 - n) * cube / 50
                n <= 68 -> (150 - n) * cube / 100
                n <= 98 -> ((1911 - 10 * n) / 3) * cube / 500
                else -> (160 - n) * cube / 100
            }
            2 -> when {                                            // 波动
                n <= 15 -> (((n + 1) / 3) + 24) * cube / 50
                n <= 36 -> (n + 14) * cube / 50
                else -> ((n / 2) + 32) * cube / 50
            }
            3 -> 6 * cube / 5 - 15L * n * n + 100L * n - 140       // 中慢
            4 -> 4 * cube / 5                                      // 快
            5 -> 5 * cube / 4                                      // 慢
            else -> 0
        }
    }

    /** 升级进度；数据不够（未知物种 / 满级 / 读不到经验）返回 null。 */
    fun progress(species: Int, level: Int, exp: Long): Progress? {
        val rate = growthRateOf(species) ?: return null
        if (level <= 0 || level >= 100) return null
        if (exp < 0) return null
        val cur = expForLevel(rate, level)
        val next = expForLevel(rate, level + 1)
        if (next <= cur) return null
        return Progress(exp, cur, next)
    }

    // ---------- 日志（格式同 docs/OBSERVABILITY.md） ----------

    private fun warn(msg: String) {
        val line = "${isoNow()} WARN  $msg"
        try { Log.w(TAG, line) } catch (_: Throwable) {}
        try {
            Thread {
                try {
                    File(LOG_PATH).appendText(line + "\n")
                } catch (_: Throwable) {
                }
            }.start()
        } catch (_: Throwable) {
        }
    }

    private fun isoNow(): String =
        try {
            Instant.now().truncatedTo(ChronoUnit.SECONDS).toString()
        } catch (_: Throwable) {
            "1970-01-01T00:00:00Z"
        }
}
