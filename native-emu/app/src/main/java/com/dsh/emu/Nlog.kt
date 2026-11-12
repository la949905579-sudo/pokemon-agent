package com.dsh.emu

import android.util.Log
import java.io.File
import java.io.FileOutputStream
import java.time.Instant
import java.time.temporal.ChronoUnit
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors

/**
 * 结构化日志（格式见 docs/OBSERVABILITY.md 第一节）：`ISO8601 LEVEL event k=v`。
 *
 * 只给桥和帧循环用；Updater / Growth / MapData 各自还有自己的日志，别混。
 * 约束：
 * - 落盘 `/sdcard/Download/emu_native.log`；异步单线程按调用顺序写；
 * - 单文件 5MB，超了滚成 `.1`（重名旧 `.1` 先删）；
 * - 写日志绝不外抛（写不了就降级 logcat）；默认 INFO。
 *
 * 行格式 / 值清洗 / 滚动判定 / 限流判定都拆成纯函数，方便单测。
 */
object Nlog {
    const val LOG_PATH = "/sdcard/Download/emu_native.log"
    const val MAX_BYTES = 5L * 1024 * 1024
    const val MAX_VALUE_CHARS = 120
    const val THROTTLE_MS = 10_000L

    private const val TAG = "native-emu"

    /** docs 里的级别固定 5 档；这里只用这四档，每帧的 TRACE 不开放。 */
    enum class Level(val rank: Int, val label: String) {
        DEBUG(0, "DEBUG"),
        INFO(1, "INFO"),
        WARN(2, "WARN"),
        ERROR(3, "ERROR"),
        ;

        /** 第 3 列前补齐 5 宽（`INFO ` + 空格 → 与 bridge.conn 之间两个空格）。 */
        val padded: String get() = label.padEnd(5)
    }

    @Volatile
    var minLevel: Level = Level.INFO

    private val throttleAt = ConcurrentHashMap<String, Long>()

    private val executor = Executors.newSingleThreadExecutor { r ->
        Thread(r, "nlog").apply { isDaemon = true }
    }

    // ---------- 对外 API ----------

    fun debug(event: String, vararg fields: Pair<String, Any?>) = log(Level.DEBUG, event, fields)
    fun info(event: String, vararg fields: Pair<String, Any?>) = log(Level.INFO, event, fields)
    fun warn(event: String, vararg fields: Pair<String, Any?>) = log(Level.WARN, event, fields)
    fun error(event: String, vararg fields: Pair<String, Any?>) = log(Level.ERROR, event, fields)

    /** 限流日志：同一 key 在 THROTTLE_MS 内最多一条（给「同一个错误别刷屏」用）。 */
    fun warnThrottled(key: String, event: String, vararg fields: Pair<String, Any?>) {
        if (throttlePass(key)) warn(event, *fields)
    }

    fun errorThrottled(key: String, event: String, vararg fields: Pair<String, Any?>) {
        if (throttlePass(key)) error(event, *fields)
    }

    fun infoThrottled(key: String, event: String, vararg fields: Pair<String, Any?>) {
        if (throttlePass(key)) info(event, *fields)
    }

    /**
     * 限流放行：key 首次或距上次 ≥ window 时返回 true 并记下时间。
     *
     * 用 ConcurrentHashMap.compute 做 get→put 原子化：并发下同一 key 在一个窗口内
     * 只有一个调用线程能拿到 true（旧实现 get 和 put 分开，两个线程可能同时放行）。
     */
    fun throttlePass(key: String, nowMs: Long = System.currentTimeMillis()): Boolean {
        var allowed = false
        throttleAt.compute(key) { _, last ->
            if (shouldLogThrottled(last, nowMs)) {
                allowed = true
                nowMs
            } else {
                last
            }
        }
        if (allowed && throttleAt.size > 128) {
            // 简单防涨：只保留最近一小时内的
            val cutoff = nowMs - 3_600_000L
            throttleAt.entries.removeIf { it.value < cutoff }
        }
        return allowed
    }

    // ---------- 纯函数（单测覆盖） ----------

    /** 一行日志：`ISO LEVEL event k=v k=v`。 */
    fun buildLine(level: Level, event: String, fields: List<Pair<String, Any?>>, iso: String): String {
        val sb = StringBuilder()
        sb.append(clean(iso)).append(' ').append(level.padded).append(' ').append(clean(event))
        for ((k, v) in fields) sb.append(' ').append(clean(k)).append('=').append(clean(v))
        return sb.toString()
    }

    /** 值清洗：换行/制表压成单空格、trim、空值变 `-`、超长截断。 */
    fun clean(v: Any?): String {
        val raw = v?.toString() ?: return "-"
        val flat = raw.replace(Regex("\\s+"), " ").trim()
        if (flat.isEmpty()) return "-"
        return if (flat.length <= MAX_VALUE_CHARS) flat else flat.substring(0, MAX_VALUE_CHARS)
    }

    /** 文件超上限才滚（等于上限先不滚，避免边界抖动）。 */
    fun shouldRotate(sizeBytes: Long, maxBytes: Long = MAX_BYTES): Boolean = sizeBytes > maxBytes

    /** 限流判定：没记录过，或距上次已超过窗口。 */
    fun shouldLogThrottled(lastAtMs: Long?, nowMs: Long, windowMs: Long = THROTTLE_MS): Boolean =
        lastAtMs == null || nowMs - lastAtMs >= windowMs

    /** 级别过滤（默认 INFO：DEBUG 不落盘）。 */
    fun shouldEmit(level: Level, min: Level = minLevel): Boolean = level.rank >= min.rank

    // ---------- 落盘 ----------

    private fun log(level: Level, event: String, fields: Array<out Pair<String, Any?>>) {
        try {
            if (!shouldEmit(level, minLevel)) return
            val line = buildLine(level, event, fields.toList(), isoNow())
            try {
                executor.execute { appendLineSafely(line, level) }
            } catch (_: Throwable) {
                // 线程池都提交不进去：直接 logcat
                try { Log.println(prio(level), TAG, line) } catch (_: Throwable) {}
            }
        } catch (_: Throwable) {
            // 连日志都拼不出来就算了，绝不外抛
        }
    }

    private fun appendLineSafely(line: String, level: Level) {
        try {
            val f = File(LOG_PATH)
            try { f.parentFile?.mkdirs() } catch (_: Throwable) {}
            if (shouldRotate(f.length())) {
                val old = File("$LOG_PATH.1")
                try { old.delete() } catch (_: Throwable) {}
                try { f.renameTo(old) } catch (_: Throwable) {}
            }
            FileOutputStream(f, true).use { it.write((line + "\n").toByteArray()) }
        } catch (_: Throwable) {
            try { Log.println(prio(level), TAG, line) } catch (_: Throwable) {}
        }
    }

    private fun prio(level: Level): Int = when (level) {
        Level.DEBUG -> Log.DEBUG
        Level.WARN -> Log.WARN
        Level.ERROR -> Log.ERROR
        else -> Log.INFO
    }

    private fun isoNow(): String =
        try {
            Instant.now().truncatedTo(ChronoUnit.SECONDS).toString()
        } catch (_: Throwable) {
            "1970-01-01T00:00:00Z"
        }
}
