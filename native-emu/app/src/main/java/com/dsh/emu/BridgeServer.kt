package com.dsh.emu

import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.IOException
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket

/**
 * localhost TCP 桥：让外部（Python 自动化）读写内存 / 按键。
 *
 * 协议（每行一条命令，UTF-8）：
 *   ping                     -> pong
 *   read <addrHex> <len>     -> ok <hexBytes>
 *   write <addrHex> <hex>    -> ok
 *   press <keyMask> <ms>     -> ok
 *   frame                    -> ok <frameCount>
 *   quit                     -> bye
 */
class BridgeServer(private val port: Int = 55401) {
    private var server: ServerSocket? = null
    @Volatile private var running = false

    fun start(): Boolean {
        if (running) return true
        return try {
            server = ServerSocket(port, 8, InetAddress.getLoopbackAddress())
            running = true
            Thread { acceptLoop() }.apply { isDaemon = true; start() }
            log("bridge: listening on ${InetAddress.getLoopbackAddress().hostAddress}:$port")
            true
        } catch (e: IOException) {
            log("bridge: bind failed ${e.javaClass.simpleName}: ${e.message}")
            false
        }
    }

    private fun log(msg: String) {
        try { java.io.File("/sdcard/Download/bridge.log").appendText("$msg\n") } catch (_: Throwable) {}
    }

    fun stop() {
        running = false
        try { server?.close() } catch (_: Exception) {}
        server = null
    }

    private fun acceptLoop() {
        while (running) {
            val s = try { server?.accept() } catch (e: Exception) { null } ?: continue
            Thread { handle(s) }.apply { isDaemon = true; start() }
        }
    }

    private fun handle(s: Socket) {
        try {
            val r: BufferedReader = s.getInputStream().bufferedReader()
            val w: BufferedWriter = s.getOutputStream().bufferedWriter()
            while (true) {
                val line = r.readLine() ?: break
                val reply = try { handleLine(line.trim()) } catch (e: Throwable) { "err ${e.message}" }
                w.write(reply); w.newLine(); w.flush()
                if (reply == "bye") break
            }
        } catch (_: Throwable) {
        } finally {
            try { s.close() } catch (_: Exception) {}
        }
    }

    private fun handleLine(line: String): String {
        if (line.isEmpty()) return "ok"
        val parts = line.split(Regex("\\s+"))
        return when (parts[0].lowercase()) {
            "ping" -> "pong"
            "read" -> {
                val addr = parts[1].toLong(16).toInt()
                val len = parts[2].toInt()
                val data = EmuCore.readMemory(addr, len) ?: return "err no-core"
                "ok " + data.joinToString("") { "%02x".format(it) }
            }
            "write" -> {
                val addr = parts[1].toLong(16).toInt()
                val bytes = hexToBytes(parts[2])
                EmuCore.writeMemory(addr, bytes)
                "ok"
            }
            "press" -> {
                val mask = parts[1].toInt()
                val ms = parts.getOrNull(2)?.toLongOrNull() ?: 80L
                EmuCore.setKeys(mask)
                try { Thread.sleep(ms) } catch (_: InterruptedException) {}
                EmuCore.setKeys(0)
                "ok"
            }
            "frame" -> "ok ${EmuCore.frameCount()}"
            "quit" -> "bye"
            else -> "err unknown"
        }
    }

    private fun hexToBytes(s: String): ByteArray {
        val out = ByteArray(s.length / 2)
        for (i in out.indices) {
            out[i] = ((s[i * 2].digitToIntOrNull(16) ?: 0) shl 4 or
                      (s[i * 2 + 1].digitToIntOrNull(16) ?: 0)).toByte()
        }
        return out
    }
}
