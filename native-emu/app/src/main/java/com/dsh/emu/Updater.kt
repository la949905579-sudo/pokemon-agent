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

    fun download(url: String, dest: File): Boolean {
        return try {
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.instanceFollowRedirects = true
            conn.connectTimeout = 15000
            conn.readTimeout = 120000
            conn.inputStream.use { input ->
                dest.outputStream().use { out -> input.copyTo(out) }
            }
            dest.length() > 1_000_000
        } catch (e: Throwable) {
            false
        }
    }

    /** 调系统安装器（需要 REQUEST_INSTALL_PACKAGES + FileProvider）。 */
    fun install(activity: Activity, apk: File) {
        val uri: Uri = FileProvider.getUriForFile(activity, activity.packageName + ".fileprovider", apk)
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        activity.startActivity(intent)
    }
}
