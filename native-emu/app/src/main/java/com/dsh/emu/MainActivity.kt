package com.dsh.emu

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color as AndroidColor
import android.graphics.Paint
import android.graphics.Rect
import android.os.Bundle
import android.view.SurfaceHolder
import android.view.SurfaceView
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.PointerEventType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import java.io.File

class MainActivity : ComponentActivity() {
    val statusText = mutableStateOf("未载入 ROM")
    val romReadyState = mutableStateOf(false)
    val runningState = mutableStateOf(false)
    val romListState = mutableStateOf<List<File>>(emptyList())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { AppScreen(this) }
    }

    override fun onPause() {
        super.onPause()
        EmuCore.pause()
        runningState.value = false
    }

    override fun onResume() {
        super.onResume()
        // 回前台自动恢复（只有已载入 ROM 才恢复）
        if (romReadyState.value) {
            EmuCore.resume()
            runningState.value = true
        }
    }

    fun scanRoms(): List<File> {
        if (!hasAllFiles()) return emptyList()
        val dirs = listOf("/sdcard/rom/gba", "/sdcard/Download", "/sdcard/Documents")
        val out = mutableListOf<File>()
        for (d in dirs) {
            File(d).listFiles()?.filter { it.isFile && it.name.lowercase().endsWith(".gba") }
                ?.let { out.addAll(it) }
        }
        // Android 存储大小写不敏感，用 canonicalPath 去重
        return out.distinctBy {
            try { it.canonicalPath } catch (e: Exception) { it.absolutePath }
        }.sortedBy { it.name }
    }

    fun hasAllFiles(): Boolean =
        if (android.os.Build.VERSION.SDK_INT >= 30)
            android.os.Environment.isExternalStorageManager()
        else true

    fun openAllFilesSettings() {
        try {
            startActivity(android.content.Intent(
                android.provider.Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
                android.net.Uri.parse("package:$packageName")))
        } catch (e: Throwable) {
            statusText.value = "无法打开权限页: ${e.message}"
        }
    }

    fun refreshRoms() {
        if (!hasAllFiles()) { statusText.value = "需要「所有文件访问」权限"; openAllFilesSettings(); return }
        val list = scanRoms()
        romListState.value = list
        statusText.value = if (list.isEmpty()) "没找到 .gba 文件" else "找到 ${list.size} 个 ROM"
    }

    fun loadRom(rom: File) {
        statusText.value = "载入 ${rom.name}"
        val ok = EmuCore.init(rom.absolutePath, "")
        romReadyState.value = ok
        statusText.value = if (ok) "ROM 已载入: ${rom.name}" else "mGBA 初始化失败"
        if (ok) { EmuCore.start(); runningState.value = true }
    }
}

class EmuView(context: Context) : SurfaceView(context), SurfaceHolder.Callback, Runnable {
    @Volatile private var running = false
    private var thread: Thread? = null
    private var bmp: Bitmap? = null
    private val paint = Paint()

    init { holder.addCallback(this) }

    fun start() {
        if (running) return
        running = true
        thread = Thread(this).also { it.start() }
    }

    fun stop() { running = false }

    override fun surfaceCreated(h: SurfaceHolder) {}
    override fun surfaceChanged(h: SurfaceHolder, f: Int, w: Int, hgt: Int) {}
    override fun surfaceDestroyed(h: SurfaceHolder) { running = false }

    override fun run() {
        val gw = EmuCore.videoWidth().coerceAtLeast(240)
        val gh = EmuCore.videoHeight().coerceAtLeast(160)
        val targetNs = (1_000_000_000L / 59.7275).toLong()
        var nextNs = System.nanoTime()
        while (running) {
            val f = EmuCore.runFrame()
            if (f == 0L) { Thread.sleep(16); continue }
            val px = EmuCore.frameBuffer() ?: continue
            var b = bmp
            if (b == null || b.width != gw || b.height != gh) {
                b = Bitmap.createBitmap(gw, gh, Bitmap.Config.ARGB_8888)
                bmp = b
            }
            b.setPixels(px, 0, gw, 0, 0, gw, gh)
            val c: Canvas = (if (android.os.Build.VERSION.SDK_INT >= 26)
                holder.lockHardwareCanvas() else holder.lockCanvas()) ?: continue
            try {
                c.drawColor(AndroidColor.BLACK)
                val vw = c.width; val vh = c.height
                val scale = minOf(vw.toFloat() / gw, vh.toFloat() / gh)
                val dw = (gw * scale).toInt(); val dh = (gh * scale).toInt()
                c.drawBitmap(b, null, Rect((vw - dw) / 2, (vh - dh) / 2, (vw + dw) / 2, (vh + dh) / 2), paint)
            } finally { holder.unlockCanvasAndPost(c) }
            nextNs += targetNs
            val now = System.nanoTime()
            if (nextNs > now) { try { Thread.sleep((nextNs - now) / 1_000_000) } catch (_: InterruptedException) {} } else nextNs = now
        }
    }
}

@Composable
fun AppScreen(activity: MainActivity) {
    var frame by remember { mutableStateOf(0L) }
    var fps by remember { mutableStateOf(0) }
    var keys by remember { mutableStateOf(0) }
    var showRoms by remember { mutableStateOf(false) }
    val emuView = remember { EmuView(activity) }
    val romReady = activity.romReadyState.value
    val status = activity.statusText.value
    val running = activity.runningState.value
    val roms = activity.romListState.value

    LaunchedEffect(romReady) { if (romReady) emuView.start() }

    LaunchedEffect(running) {
        if (!running) return@LaunchedEffect
        var lastFrames = EmuCore.frameCount()
        while (true) {
            kotlinx.coroutines.delay(1000)
            val now = EmuCore.frameCount()
            frame = now
            fps = (now - lastFrames).toInt()
            lastFrames = now
        }
    }

    Column(Modifier.fillMaxSize().background(Color(0xFF101010))) {
        Box(Modifier.weight(1f).fillMaxWidth().background(Color.Black), contentAlignment = Alignment.Center) {
            AndroidView(factory = { emuView }, modifier = Modifier.fillMaxSize())
            if (!romReady) Text("点下方「ROM」选择游戏", color = Color(0xFF777777), fontSize = 12.sp)
        }

        Box(Modifier.weight(1f).fillMaxWidth().background(Color(0xFF1B1B1B))) {
            Column(Modifier.fillMaxSize().padding(8.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                Text("帧 $frame  FPS $fps  $status", color = Color.White, fontSize = 13.sp)
                Text("按键 0x${Integer.toHexString(keys)}", color = Color(0xFF888888), fontSize = 11.sp)

                if (showRoms) {
                    LazyColumn(Modifier.weight(1f).fillMaxWidth()) {
                        items(roms) { f ->
                            Text(f.name, color = Color(0xFF9AD0FF), fontSize = 13.sp,
                                modifier = Modifier.fillMaxWidth().clickable {
                                    showRoms = false
                                    activity.loadRom(f)
                                }.padding(vertical = 6.dp))
                        }
                    }
                } else {
                    Row(Modifier.weight(1f).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly,
                        verticalAlignment = Alignment.CenterVertically) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            KeyPad("▲", EmuCore.KEY_UP) { keys = it; EmuCore.setKeys(it) }
                            Row {
                                KeyPad("◀", EmuCore.KEY_LEFT) { keys = it; EmuCore.setKeys(it) }
                                Spacer(Modifier.width(24.dp))
                                KeyPad("▶", EmuCore.KEY_RIGHT) { keys = it; EmuCore.setKeys(it) }
                            }
                            KeyPad("▼", EmuCore.KEY_DOWN) { keys = it; EmuCore.setKeys(it) }
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            KeyPad("B", EmuCore.KEY_B, 54.dp) { keys = it; EmuCore.setKeys(it) }
                            Spacer(Modifier.width(10.dp))
                            KeyPad("A", EmuCore.KEY_A, 54.dp) { keys = it; EmuCore.setKeys(it) }
                        }
                    }
                }

                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                    Button(onClick = { activity.refreshRoms(); showRoms = true }) { Text("ROM") }
                    Button(onClick = {
                        if (!romReady) return@Button
                        val f = File(activity.filesDir, "state1.sav")
                        activity.statusText.value = if (EmuCore.saveState(f.absolutePath)) "已存档" else "存档失败"
                    }) { Text("存档") }
                    Button(onClick = {
                        if (!romReady) return@Button
                        val f = File(activity.filesDir, "state1.sav")
                        activity.statusText.value = if (EmuCore.loadState(f.absolutePath)) "已读档" else "读档失败"
                    }) { Text("读档") }
                    Button(onClick = {
                        val nr = !activity.runningState.value
                        activity.runningState.value = nr
                        if (nr) { EmuCore.resume(); emuView.start() } else EmuCore.pause()
                    }) { Text(if (running) "暂停" else "继续") }
                    Button(onClick = {
                        val m = EmuCore.KEY_START
                        keys = m; EmuCore.setKeys(m)
                        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({ keys = 0; EmuCore.setKeys(0) }, 120)
                    }) { Text("Start") }
                }
                Text("P1 接自动化面板", color = Color(0xFF777777), fontSize = 11.sp)
            }
        }
    }
}

/** 多指按键：每个按钮独立跟踪自己的 pointer */
@Composable
fun KeyPad(label: String, mask: Int, size: androidx.compose.ui.unit.Dp = 44.dp,
           onChange: (Int) -> Unit) {
    Box(
        Modifier
            .size(size)
            .background(Color(0xFF333333), CircleShape)
            .pointerInput(mask) {
                while (true) {
                    awaitPointerEventScope {
                        awaitFirstDown(requireUnconsumed = false)
                        onChange(mask)
                        waitForUpOrCancellation()
                        onChange(0)
                    }
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Text(label, color = Color.White, fontSize = 15.sp, textAlign = TextAlign.Center)
    }
}
