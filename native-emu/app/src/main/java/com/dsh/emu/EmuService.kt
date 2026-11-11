package com.dsh.emu

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.PowerManager

/** 前台服务：避免 App 切后台被系统回收（自动化需要常驻）。 */
class EmuService : Service() {
    private fun log(m: String) {
        try { java.io.File("/sdcard/Download/service.log").appendText("$m\n") } catch (_: Throwable) {}
    }

    override fun onCreate() {
        super.onCreate()
        log("service: onCreate sdk=${Build.VERSION.SDK_INT}")
        val nm = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= 26) {
            val ch = NotificationChannel("emu", "模拟器", NotificationManager.IMPORTANCE_LOW)
            nm.createNotificationChannel(ch)
        }
        val notif: Notification = if (Build.VERSION.SDK_INT >= 26) {
            Notification.Builder(this, "emu")
                .setContentTitle("NativeEmu 运行中")
                .setContentText("模拟器在后台保持运行")
                .setSmallIcon(android.R.drawable.ic_media_play)
                .build()
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
                .setContentTitle("NativeEmu 运行中")
                .setContentText("模拟器在后台保持运行")
                .setSmallIcon(android.R.drawable.ic_media_play)
                .build()
        }
        try {
            startForeground(1, notif)
            log("service: startForeground ok")
        } catch (e: Throwable) {
            log("service: startForeground fail ${e.javaClass.simpleName}: ${e.message}")
        }
    }

    private var wakeLock: android.os.PowerManager.WakeLock? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        log("service: onStartCommand flags=$flags")
        if (wakeLock == null) {
            val pm = getSystemService(PowerManager::class.java)
            wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "NativeEmu:emu")
            wakeLock?.setReferenceCounted(false)
            wakeLock?.acquire()
            log("service: wakelock acquired")
        }
        return START_STICKY
    }

    override fun onDestroy() {
        try { wakeLock?.release() } catch (_: Throwable) {}
        wakeLock = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
