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
            val bindAddr = InetAddress.getByName("127.0.0.1")
            server = ServerSocket(port, 8, bindAddr)
            running = true
            Thread { acceptLoop() }.apply { isDaemon = true; start() }
            Nlog.info("bridge.conn", "ok" to true, "port" to port)
            true
        } catch (e: IOException) {
            Nlog.warn("bridge.conn", "ok" to false, "port" to port, "code" to e.javaClass.simpleName)
            false
        }
    }

    fun stop() {
        running = false
        try { server?.close() } catch (_: Exception) {}
        server = null
    }

    private fun acceptLoop() {
        while (running) {
            val s = try { server?.accept() } catch (e: Exception) { null } ?: continue
            Nlog.info("bridge.conn", "stage" to "connect", "port" to port)
            Thread { handle(s) }.apply { isDaemon = true; start() }
        }
    }

    /** 命令失败统一入口：同一 cmd 10s 内只记一次，未知命令也算。 */
    private fun logCmdError(line: String, reply: String) {
        val cmd = line.split(Regex("\\s+")).firstOrNull()?.take(24).orEmpty().ifEmpty { "?" }
        Nlog.warnThrottled("bridge.cmd:$cmd", "bridge.cmd", "ok" to false, "cmd" to cmd, "err" to reply)
    }

    private fun handle(s: Socket) {
        try {
            val r: BufferedReader = s.getInputStream().bufferedReader()
            val w: BufferedWriter = s.getOutputStream().bufferedWriter()
            while (true) {
                val line = r.readLine() ?: break
                val reply = try { handleLine(line.trim()) } catch (e: Throwable) { "err ${e.javaClass.simpleName}" }
                if (reply.startsWith("err")) logCmdError(line.trim(), reply)
                w.write(reply); w.newLine(); w.flush()
                if (reply == "bye") break
            }
        } catch (_: Throwable) {
        } finally {
            try { s.close() } catch (_: Exception) {}
            Nlog.info("bridge.conn", "stage" to "disconnect", "port" to port)
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
            "status" -> {
                // 外部推送的界面状态（JSON），下屏直接显示
                val json = line.substringAfter("status").trim()
                if (json.isNotEmpty()) {
                    com.dsh.emu.UiState.statusJson.value = json
                }
                "ok"
            }
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
