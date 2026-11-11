package com.dsh.emu

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.util.Log
import androidx.core.content.FileProvider
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.ConnectException
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL
import java.net.UnknownHostException
import java.time.Instant
import java.time.temporal.ChronoUnit

/** 从 GitHub Releases 检查并安装新版本。 */
object Updater {
    private const val OWNER = "la949905579-sudo"
    private const val REPO = "pokemon-agent"
    private const val API = "https://api.github.com"
    private const val ASSET = "app-debug.apk"

    /** 结构化日志落盘位置（跟 bridge.log / service.log 同目录），写不了就降级 logcat。 */
    private const val LOG_PATH = "/sdcard/Download/ota.log"
    private const val LOG_MAX_BYTES = 5L * 1024 * 1024
    private const val LOG_TAG = "OTA"

    data class Release(val tag: String, val url: String, val body: String)

    // ---------- 结构化日志（格式见 docs/OBSERVABILITY.md 第一节） ----------
    // 一行一个事件：ISO时间 LEVEL 事件 key=value ...
    // 纪律：写日志本身绝不许抛异常，否则会把检查/下载流程带崩。

    private fun nowIso(): String =
        try { Instant.now().truncatedTo(ChronoUnit.SECONDS).toString() }
        catch (_: Throwable) { "1970-01-01T00:00:00Z" }

    /** 常见网络异常映射成稳定错误码，方便 grep 统计（timeout / dns / connect）。 */
    private fun errCode(e: Throwable): String = when (e) {
        is SocketTimeoutException -> "timeout"
        is UnknownHostException -> "dns"
        is ConnectException -> "connect"
        else -> e.javaClass.simpleName
    }

    private fun log(level: String, event: String, vararg fields: Pair<String, Any?>) {
        try {
            val sb = StringBuilder()
            sb.append(nowIso()).append(' ').append(level.padEnd(5)).append(' ').append(event)
            for ((k, v) in fields) {
                val text = (v?.toString() ?: "-").replace('\n', ' ').replace('\r', ' ')
                sb.append(' ').append(k).append('=').append(text)
            }
            val line = sb.toString()
            var written = false
            try { appendToFile(line); written = true } catch (_: Throwable) { written = false }
            if (!written) {
                try { Log.println(prio(level), LOG_TAG, line) } catch (_: Throwable) {}
            }
        } catch (_: Throwable) {
            // 连日志都记不下来就算了，绝不外抛
        }
    }

    private fun prio(level: String): Int = when (level) {
        "ERROR" -> Log.ERROR
        "WARN" -> Log.WARN
        "DEBUG" -> Log.DEBUG
        "TRACE" -> Log.VERBOSE
        else -> Log.INFO
    }

    private fun appendToFile(line: String) {
        val f = File(LOG_PATH)
        try { f.parentFile?.mkdirs() } catch (_: Throwable) {}
        try {
            if (f.length() > LOG_MAX_BYTES) {
                // 规范第四节第 3 条：单文件 5MB 上限，超出滚动一份
                val old = File("$LOG_PATH.1")
                try { old.delete() } catch (_: Throwable) {}
                try { f.renameTo(old) } catch (_: Throwable) {}
            }
        } catch (_: Throwable) {}
        FileOutputStream(f, true).use { it.write((line + "\n").toByteArray()) }
    }

    private fun hostOf(url: String): String =
        try { URL(url).host ?: "?" } catch (_: Throwable) { "?" }

    fun latest(): Release? {
        return try {
            log("INFO", "ota.check", "stage" to "start")
            val conn = URL("$API/repos/$OWNER/$REPO/releases/latest")
                .openConnection() as HttpURLConnection
            conn.setRequestProperty("Accept", "application/vnd.github+json")
            conn.connectTimeout = 10000
            conn.readTimeout = 15000
            val httpCode = conn.responseCode
            if (httpCode != 200) {
                log("ERROR", "ota.check", "stage" to "http", "code" to httpCode)
                return null
            }
            val text = conn.inputStream.bufferedReader().readText()
            val o = JSONObject(text)
            val tag = o.optString("tag_name")
            val assets = o.optJSONArray("assets")
            var url: String? = null
            if (assets != null) {
                for (i in 0 until assets.length()) {
                    val a = assets.getJSONObject(i)
                    if (a.optString("name") == ASSET) {
                        url = a.optString("browser_download_url")
                        break
                    }
                }
            }
            val body = o.optString("body", "")
            if (tag.isNotEmpty() && url != null) {
                log("INFO", "ota.check", "stage" to "tag", "tag" to tag)
                Release(tag, url, body)
            } else {
                log("ERROR", "ota.check", "stage" to "asset",
                    "code" to (if (tag.isEmpty()) "no_tag" else "asset_missing"),
                    "tag" to tag, "asset" to ASSET)
                null
            }
        } catch (e: Throwable) {
            log("ERROR", "ota.check", "stage" to "fetch", "code" to errCode(e), "msg" to e.message)
            null
        }
    }

    fun download(url: String, dest: File, onProgress: (Int) -> Unit = {}): Boolean {
        return try {
            log("INFO", "ota.download", "stage" to "start", "host" to hostOf(url), "dest" to dest.name)
            // 下载前清掉旧安装包
            try {
                dest.delete()
            } catch (e: Throwable) {
                log("WARN", "ota.download", "stage" to "cleanup", "code" to errCode(e), "msg" to e.message)
            }
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.instanceFollowRedirects = true
            conn.setRequestProperty("User-Agent", "NativeEmu-Updater/1.0")
            conn.setRequestProperty("Accept", "application/octet-stream")
            conn.connectTimeout = 15000
            conn.readTimeout = 180000
            val httpCode = conn.responseCode
            val total = conn.contentLengthLong
            if (httpCode != 200) {
                log("ERROR", "ota.download", "stage" to "http", "code" to httpCode)
                try {
                    dest.delete()
                } catch (e: Throwable) {
                    log("WARN", "ota.download", "stage" to "cleanup", "code" to errCode(e), "msg" to e.message)
                }
                return false
            }
            log("INFO", "ota.download", "stage" to "open", "code" to httpCode, "bytes" to total)
            var read = 0L
            var lastLoggedPct = 0
            conn.inputStream.use { input ->
                dest.outputStream().use { out ->
                    val buf = ByteArray(64 * 1024)
                    while (true) {
                        val n = input.read(buf)
                        if (n <= 0) break
                        out.write(buf, 0, n)
                        read += n
                        if (total > 0) {
                            val pct = ((read * 100) / total).toInt()
                            onProgress(pct)
                            // 每 10% 只打一条，避免每块都刷屏
                            val bucket = (pct / 10) * 10
                            if (bucket >= lastLoggedPct + 10) {
                                log("INFO", "ota.download", "stage" to "progress", "pct" to bucket, "bytes" to read)
                                lastLoggedPct = bucket
                            }
                        }
                    }
                }
            }
            onProgress(100)
            log("INFO", "ota.download", "stage" to "done", "bytes" to read)
            // 校验：必须是 zip（APK）且大小合理
            val ok = dest.length() > 1_000_000 && isApkFile(dest)
            if (!ok) {
                val why = if (dest.length() <= 1_000_000) "too_small" else "not_zip"
                log("ERROR", "ota.verify", "stage" to "check", "ok" to false, "code" to why, "bytes" to dest.length())
                dest.delete()
            } else {
                log("INFO", "ota.verify", "stage" to "check", "ok" to true, "bytes" to dest.length())
            }
            ok
        } catch (e: Throwable) {
            log("ERROR", "ota.download", "stage" to "fetch", "code" to errCode(e), "msg" to e.message)
            try {
                dest.delete()
            } catch (e2: Throwable) {
                log("WARN", "ota.download", "stage" to "cleanup", "code" to errCode(e2), "msg" to e2.message)
            }
            false
        }
    }

    private fun isApkFile(f: File): Boolean {
        return try {
            java.io.FileInputStream(f).use { ins ->
                val b = ByteArray(4)
                if (ins.read(b) != 4) return false
                b[0] == 'P'.code.toByte() && b[1] == 'K'.code.toByte()
            }
        } catch (e: Throwable) {
            log("ERROR", "ota.verify", "stage" to "read", "code" to errCode(e), "msg" to e.message)
            false
        }
    }

    /** 调系统安装器（需要 REQUEST_INSTALL_PACKAGES + FileProvider）。 */
    /** 是否有「安装未知应用」权限（API 26+）。 */
    fun canInstall(context: android.content.Context): Boolean {
        return if (android.os.Build.VERSION.SDK_INT >= 26) {
            context.packageManager.canRequestPackageInstalls()
        } else true
    }

    /** 跳系统设置页允许安装。 */
    fun openInstallSettings(activity: Activity) {
        try {
            val i = Intent(android.provider.Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES).apply {
                data = Uri.parse("package:" + activity.packageName)
            }
            activity.startActivity(i)
        } catch (e: Throwable) {
            log("WARN", "ota.install", "stage" to "settings", "code" to errCode(e), "msg" to e.message)
            try {
                activity.startActivity(Intent(android.provider.Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES))
            } catch (e2: Throwable) {
                log("ERROR", "ota.install", "stage" to "settings", "code" to errCode(e2), "msg" to e2.message)
            }
        }
    }

    /** 安装前检查权限：没有就跳设置页并返回 false。 */
    fun install(activity: Activity, apk: File): Boolean {
        if (!canInstall(activity)) {
            log("WARN", "ota.install", "stage" to "perm", "ok" to false, "bytes" to apk.length())
            openInstallSettings(activity)
            return false
        }
        return try {
            val uri: Uri = FileProvider.getUriForFile(activity, activity.packageName + ".fileprovider", apk)
            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(uri, "application/vnd.android.package-archive")
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            activity.startActivity(intent)
            log("INFO", "ota.install", "stage" to "start", "ok" to true, "bytes" to apk.length())
            true
        } catch (e: Throwable) {
            log("ERROR", "ota.install", "stage" to "start", "code" to errCode(e), "msg" to e.message)
            false
        }
    }
}
