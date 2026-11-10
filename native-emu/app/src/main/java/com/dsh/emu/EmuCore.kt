package com.dsh.emu

/**
 * JNI 契约层（P0）。
 * 按键位掩码（与 GBA 一致）：
 *   A=1<<0 B=1<<1 SELECT=1<<2 START=1<<3
 *   RIGHT=1<<4 LEFT=1<<5 UP=1<<6 DOWN=1<<7 R=1<<8 L=1<<9
 */
object EmuCore {
    init { System.loadLibrary("emu") }

    external fun init(romPath: String, biosPath: String): Boolean
    external fun start(): Boolean
    external fun pause()
    external fun resume()
    external fun stop()

    external fun runFrame(): Long
    external fun setKeys(mask: Int)
    external fun readMemory(addr: Int, len: Int): ByteArray?
    external fun writeMemory(addr: Int, data: ByteArray): Boolean
    external fun frameCount(): Long
    external fun setSpeed(num: Int, den: Int)
    external fun frameBuffer(): IntArray?
    external fun videoWidth(): Int
    external fun videoHeight(): Int

    // ---- 按键常量 ----
    const val KEY_A = 1 shl 0
    const val KEY_B = 1 shl 1
    const val KEY_SELECT = 1 shl 2
    const val KEY_START = 1 shl 3
    const val KEY_RIGHT = 1 shl 4
    const val KEY_LEFT = 1 shl 5
    const val KEY_UP = 1 shl 6
    const val KEY_DOWN = 1 shl 7
    const val KEY_R = 1 shl 8
    const val KEY_L = 1 shl 9
}
