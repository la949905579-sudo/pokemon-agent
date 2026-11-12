package com.dsh.emu.ui

import java.io.File
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/**
 * 即时存档卡槽：3 个槽，文件是 `filesDir/state1.sav` … `state3.sav`。
 * 这里只负责路径和显示文案；真正的读写走 `EmuCore.saveState / loadState`。
 */
object SaveSlots {
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
