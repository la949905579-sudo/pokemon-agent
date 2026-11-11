package com.dsh.emu.game

import com.dsh.emu.EmuCore

/** 内存读取封装：包装 JNI，提供常用类型。读不到返回 null。 */
object Memo {
    /** 可替换的读取实现（单测注入 fake，线上走 JNI）。 */
    var reader: (Int, Int) -> ByteArray? = { addr, n -> EmuCore.readMemory(addr, n) }

    fun bytes(addr: Int, n: Int): ByteArray? {
        val d = reader(addr, n) ?: return null
        return if (d.size >= n) d.copyOf(n) else null
    }

    fun u8(addr: Int): Int = bytes(addr, 1)?.get(0)?.toInt()?.and(0xFF) ?: -1

    fun u16(addr: Int): Int {
        val d = bytes(addr, 2) ?: return -1
        return (d[0].toInt() and 0xFF) or ((d[1].toInt() and 0xFF) shl 8)
    }

    fun u32(addr: Int): Long {
        val d = bytes(addr, 4) ?: return -1
        return ((d[0].toLong() and 0xFF)) or ((d[1].toLong() and 0xFF) shl 8) or
            ((d[2].toLong() and 0xFF) shl 16) or ((d[3].toLong() and 0xFF) shl 24)
    }

    fun s16(addr: Int): Int {
        val v = u16(addr)
        return if (v >= 0x8000) v - 0x10000 else v
    }
}
