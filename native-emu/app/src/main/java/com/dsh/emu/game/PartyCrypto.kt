package com.dsh.emu.game

/** 队伍宝可梦解密（PortablePokemon：48 字节 substruct 按 PID^OTID 异或 + 顺序表）。 */
object PartyCrypto {

    private val ORDERS = listOf(
        "GAEM", "GAME", "GEAM", "GEMA", "GMAE", "GMEA",
        "AGEM", "AGME", "AEGM", "AEMG", "AMGE", "AMEG",
        "EGAM", "EGMA", "EAGM", "EAMG", "EMGA", "EMAG",
        "MGAE", "MGEA", "MAGE", "MAEG", "MEGA", "MEAG",
    )

    data class Mon(
        val species: Int,
        val moves: List<Int>,
        val pp: List<Int>,
        val exp: Long,
    )

    private fun u32(b: ByteArray, o: Int): Long =
        (b[o].toLong() and 0xFF) or ((b[o + 1].toLong() and 0xFF) shl 8) or
            ((b[o + 2].toLong() and 0xFF) shl 16) or ((b[o + 3].toLong() and 0xFF) shl 24)

    private fun u16(b: ByteArray, o: Int): Int =
        (b[o].toInt() and 0xFF) or ((b[o + 1].toInt() and 0xFF) shl 8)

    /** 解密一只（buf 至少 base+100 字节）。失败返回 null。 */
    fun decrypt(buf: ByteArray, base: Int): Mon? {
        if (buf.size < base + 100) return null
        val pid = u32(buf, base)
        val otid = u32(buf, base + 4)
        val key = pid xor otid

        // 48 字节数据区（0x20 起）
        val words = LongArray(12) { i -> u32(buf, base + 0x20 + i * 4) xor key }
        val plain = ByteArray(48)
        for (i in 0 until 12) {
            val w = words[i]
            plain[i * 4] = (w and 0xFF).toByte()
            plain[i * 4 + 1] = ((w shr 8) and 0xFF).toByte()
            plain[i * 4 + 2] = ((w shr 16) and 0xFF).toByte()
            plain[i * 4 + 3] = ((w shr 24) and 0xFF).toByte()
        }

        val seq = ORDERS[(pid % 24).toInt()]
        val gi = seq.indexOf('G') * 12
        val ai = seq.indexOf('A') * 12

        val species = u16(plain, gi + 0)
        val exp = u32(plain, gi + 4)
        val moves = (0 until 4).map { u16(plain, ai + it * 2) }
        val pp = (0 until 4).map { plain[ai + 8 + it].toInt() and 0xFF }
        return Mon(species, moves, pp, exp)
    }
}
