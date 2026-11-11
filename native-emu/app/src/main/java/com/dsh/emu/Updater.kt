package com.dsh.emu

import android.app.Activity
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/** 从 GitHub Releases 检查并安装新版本。 */
object Updater {
    private const val OWNER = "la949905579-sudo"
    private const val REPO = "pokemon-agent"
    private const val API = "https://api.github.com"
    private const val ASSET = "app-debug.apk"

    data class Release(val tag: String, val url: String, val body: String)

    fun latest(): Release? {
        return try {
            val conn = URL("$API/repos/$OWNER/$REPO/releases/latest")
                .openConnection() as HttpURLConnection
            conn.setRequestProperty("Accept", "application/vnd.github+json")
            conn.connectTimeout = 10000
            conn.readTimeout = 15000
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
            if (tag.isNotEmpty() && url != null) Release(tag, url, body) else null
        } catch (e: Throwable) {
            null
        }
    }

    fun download(url: String, dest: File, onProgress: (Int) -> Unit = {}): Boolean {
        return try {
            // 下载前清掉旧安装包
            try { dest.delete() } catch (_: Throwable) {}
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.instanceFollowRedirects = true
            conn.setRequestProperty("User-Agent", "NativeEmu-Updater/1.0")
            conn.setRequestProperty("Accept", "application/octet-stream")
            conn.connectTimeout = 15000
            conn.readTimeout = 180000
            val total = conn.contentLengthLong
            var read = 0L
            conn.inputStream.use { input ->
                dest.outputStream().use { out ->
                    val buf = ByteArray(64 * 1024)
                    while (true) {
                        val n = input.read(buf)
                        if (n <= 0) break
                        out.write(buf, 0, n)
                        read += n
                        if (total > 0) onProgress(((read * 100) / total).toInt())
                    }
                }
            }
            onProgress(100)
            // 校验：必须是 zip（APK）且大小合理
            val ok = dest.length() > 1_000_000 && isApkFile(dest)
            if (!ok) dest.delete()
            ok
        } catch (e: Throwable) {
            try { dest.delete() } catch (_: Throwable) {}
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
        } catch (e: Throwable) { false }
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
            try {
                activity.startActivity(Intent(android.provider.Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES))
            } catch (_: Throwable) {}
        }
    }

    /** 安装前检查权限：没有就跳设置页并返回 false。 */
    fun install(activity: Activity, apk: File): Boolean {
        if (!canInstall(activity)) {
            openInstallSettings(activity)
            return false
        }
        val uri: Uri = FileProvider.getUriForFile(activity, activity.packageName + ".fileprovider", apk)
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        activity.startActivity(intent)
        return true
    }
}
