package com.dsh.emu.ui

import java.io.File
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/**
 * 即时存档卡槽：3 个槽，文件是 `filesDir/state1.sav` … `state3.sav`。
 * 这里只负责路径和显示文案；真正的读写走 `EmuCore.saveState / loadState`。
 */
internal object SaveSlots {
    const val COUNT = 3

    private val TIME_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")

    fun file(filesDir: File, slot: Int): File = File(filesDir, "state$slot.sav")

    fun exists(filesDir: File, slot: Int): Boolean =
        slot in 1..COUNT && file(filesDir, slot).isFile

    /** 槽位文案：有档 `槽 1 · 2026-11-12 17:05`，空档 `槽 1 · 空`。 */
    fun label(filesDir: File, slot: Int, zone: ZoneId = ZoneId.systemDefault()): String {
        val f = file(filesDir, slot)
        if (!f.isFile) return "槽 $slot · 空"
        return "槽 $slot · " + formatTime(f.lastModified(), zone)
    }

    fun formatTime(mtime: Long, zone: ZoneId = ZoneId.systemDefault()): String =
        TIME_FORMAT.format(Instant.ofEpochMilli(mtime).atZone(zone))
}

/** 卡槽操作：存档 / 读取 / 删除。 */
internal enum class SlotAction { SAVE, LOAD, DELETE }

/**
 * 三个操作共用一套「二次确认」规则（纯函数，方便单测）：
 * - 有档：覆盖存档 / 读取 / 删除都要二次确认；
 * - 空槽：三个操作都直接执行（各操作自己给「空槽」等提示）；
 * - 确认态按 (操作, 槽位) 记录，只有同一操作同一槽的第二次点击才算确认——
 *   这天然保证同一时刻只有一个确认态。
 */
internal object SlotConfirm {
    fun shouldRunNow(
        action: SlotAction,
        slot: Int,
        confirming: Pair<SlotAction, Int>?,
        hasSave: Boolean,
    ): Boolean {
        if (confirming != null && confirming.first == action && confirming.second == slot) return true
        return !hasSave
    }
}
