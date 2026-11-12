package com.dsh.emu.ui

import com.dsh.emu.EmuCore
import com.dsh.emu.game.MoveCaster

/**
 * 招式施放线程的机械逻辑：方向 → 按键掩码、可中断等待、取消后立即松键。
 *
 * 不碰 Android、不改游戏状态；JNI 按键与 `Thread.sleep` 由调用方注入，
 * 离线单测用假实现（[EmuCore] 的 `KEY_*` 是编译期常量，不会加载 native 库）。
 *
 * 取消语义（与 `closeKeys()` 路径对齐）：代际变化后不再按新键，正在按住的键尽快松开。
 */
object MoveCastThread {
    /** 等待切片：最多 20ms 看一次是否已取消，保证取消后尽快松键。 */
    const val SLICE_MS = 20L

    /** 2×2 招式格方向 → GBA 按键掩码。 */
    fun maskOf(dir: MoveCaster.Dir): Int = when (dir) {
        MoveCaster.Dir.UP -> EmuCore.KEY_UP
        MoveCaster.Dir.DOWN -> EmuCore.KEY_DOWN
        MoveCaster.Dir.LEFT -> EmuCore.KEY_LEFT
        MoveCaster.Dir.RIGHT -> EmuCore.KEY_RIGHT
    }

    /**
     * 可中断等待 [ms] 毫秒：每 [SLICE_MS] 看一次 [isCancelled]。
     * 返回 false 表示等待被取消（或被 [InterruptedException] 打断）。
     */
    fun sleepInterruptibly(ms: Long, isCancelled: () -> Boolean, sleep: (Long) -> Unit): Boolean {
        var left = ms
        while (left > 0) {
            if (isCancelled()) return false
            val chunk = if (left < SLICE_MS) left else SLICE_MS
            try {
                sleep(chunk)
            } catch (_: InterruptedException) {
                return false
            }
            left -= chunk
        }
        return !isCancelled()
    }

    /**
     * 按住 [mask] [ms] 毫秒，返回前必定松键（`setKeys(0)`）。
     *
     * - 按下前已取消：一个键都不按；
     * - 等待中被取消 / 被打断：提前松键；
     * - 任何异常：finally 松键，不把方向键/A 留在按下状态。
     */
    fun press(
        mask: Int,
        ms: Long,
        isCancelled: () -> Boolean,
        setKeys: (Int) -> Unit,
        sleep: (Long) -> Unit,
    ) {
        if (isCancelled()) return
        try {
            setKeys(mask)
            sleepInterruptibly(ms, isCancelled, sleep)
        } finally {
            setKeys(0)
        }
    }
}
