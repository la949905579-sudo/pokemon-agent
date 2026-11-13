package com.dsh.emu.ui

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color as AndroidColor
import android.graphics.Paint
import android.graphics.Rect
import android.view.SurfaceHolder
import android.view.SurfaceView
import com.dsh.emu.EmuCore
import com.dsh.emu.Nlog

/**
 * GBA 上屏视图：独立渲染线程按 59.7275fps 跑 runFrame 并把帧缓冲画到 Surface。
 * 从 MainActivity.kt 原样迁出（行为等价，无逻辑改动）。
 */
class EmuView(context: Context) : SurfaceView(context), SurfaceHolder.Callback, Runnable {
    @Volatile private var running = false
    @Volatile private var shouldRun = false
    @Volatile var speed = 1   // 1x / 2x / 4x：每帧跑几次 runFrame
    @Volatile private var surfaceReady = false
    private var thread: Thread? = null
    private var bmp: Bitmap? = null
    private val paint = Paint()

    init { holder.addCallback(this) }

    fun start() {
        shouldRun = true
        if (running) return
        running = true
        thread = Thread(this).also { it.start() }
    }

    fun stop() { shouldRun = false; running = false }

    override fun surfaceCreated(h: SurfaceHolder) {
        surfaceReady = true
        if (shouldRun && !running) { running = true; thread = Thread(this).also { it.start() } }
    }
    override fun surfaceChanged(h: SurfaceHolder, f: Int, w: Int, hgt: Int) { surfaceReady = true }
    override fun surfaceDestroyed(h: SurfaceHolder) { surfaceReady = false }

    override fun run() {
        val gw = EmuCore.videoWidth().coerceAtLeast(240)
        val gh = EmuCore.videoHeight().coerceAtLeast(160)
        val targetNs = (1_000_000_000L / 59.7275).toLong()
        var nextNs = System.nanoTime()
        var lastLoggedSpeed = speed
        var stalled = false
        while (running) {
            try {
            val sp = speed
            if (sp != lastLoggedSpeed) {
                lastLoggedSpeed = sp
                Nlog.info("emu.frame.speed", "n" to sp)
            }
            var f = 0L
            repeat(sp) { f = EmuCore.runFrame() }
            if (f == 0L) {
                // 卡帧：进入/恢复共用同一个限流 key，0/非 0 抖动最多 1 条/10s；正常帧不记日志
                if (!stalled) {
                    stalled = true
                    Nlog.warnThrottled("emu.frame.stall:enter", "emu.frame.stall", "stage" to "enter")
                }
                try { Thread.sleep(16) } catch (_: InterruptedException) {}
                continue
            }
            if (stalled) {
                stalled = false
                Nlog.infoThrottled("emu.frame.stall:recover", "emu.frame.stall", "stage" to "recover")
            }
            val px = EmuCore.frameBuffer() ?: continue
            if (surfaceReady) {
                var b = bmp
                if (b == null || b.width != gw || b.height != gh) {
                    b = Bitmap.createBitmap(gw, gh, Bitmap.Config.ARGB_8888); bmp = b
                }
                b.setPixels(px, 0, gw, 0, 0, gw, gh)
                val c: Canvas? = try {
                    if (android.os.Build.VERSION.SDK_INT >= 26) holder.lockHardwareCanvas() else holder.lockCanvas()
                } catch (e: Exception) { null }
                if (c != null) {
                    try {
                        c.drawColor(AndroidColor.BLACK)
                        val vw = c.width; val vh = c.height
                        val scale = minOf(vw.toFloat() / gw, vh.toFloat() / gh)
                        val dw = (gw * scale).toInt(); val dh = (gh * scale).toInt()
                        c.drawBitmap(b, null, Rect((vw - dw) / 2, (vh - dh) / 2, (vw + dw) / 2, (vh + dh) / 2), paint)
                    } finally { holder.unlockCanvasAndPost(c) }
                }
            }
            nextNs += targetNs
            val now = System.nanoTime()
            if (nextNs > now) { try { Thread.sleep((nextNs - now) / 1_000_000) } catch (_: InterruptedException) {} } else nextNs = now
            } catch (e: Exception) {
                // 渲染线程不能因为一帧异常就崩：记录（同一错误 10s 内一条）后继续下一帧
                // 只接 Exception，OOM 之类 Error 不吞
                Nlog.errorThrottled(
                    "frame:" + e.javaClass.simpleName,
                    "emu.frame.error",
                    "code" to e.javaClass.simpleName,
                    "msg" to e.message,
                )
                try { Thread.sleep(16) } catch (_: InterruptedException) {}
                nextNs = System.nanoTime()
            }
        }
    }
}
