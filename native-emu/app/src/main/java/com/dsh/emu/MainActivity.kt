package com.dsh.emu

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color as AndroidColor
import android.graphics.Paint
import android.graphics.Rect
import android.net.Uri
import android.os.Bundle
import android.view.SurfaceHolder
import android.view.SurfaceView
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import java.io.File

class MainActivity : ComponentActivity() {
    @Volatile var romPath: String? = null
    @Volatile var emuReady = false

    // 用 Compose 可观察状态，避免 Activity 重建后回调丢失
    val statusText = androidx.compose.runtime.mutableStateOf("未载入 ROM")
    val romReadyState = androidx.compose.runtime.mutableStateOf(false)
    val runningState = androidx.compose.runtime.mutableStateOf(false)

    private val romPicker = registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri == null) { statusText.value = "已取消"; return@registerForActivityResult }
        statusText.value = "载入中..."
        val err = importRom(uri)
        romReadyState.value = err.isEmpty()
        statusText.value = if (romReadyState.value) "ROM 已载入" else "失败: $err"
        if (romReadyState.value) {
            EmuCore.start()
            runningState.value = true
        }
    }

    fun launchRomPicker() {
        try { romPicker.launch(arrayOf("*/*")) }
        catch (e: Throwable) { statusText.value = "选择器失败: ${e.message}" }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // 如果私有目录已有 ROM（上次选择过），直接载入
        try {
            val f = File(filesDir, "rom.gba")
            if (f.exists() && f.length() > 0) {
                romPath = f.absolutePath
                emuReady = EmuCore.init(f.absolutePath, "")
                if (emuReady) {
                    EmuCore.start()
                    romReadyState.value = true
                    runningState.value = true
                    statusText.value = "ROM 已载入 (${f.length()} bytes)"
                }
            }
        } catch (e: Throwable) {
            statusText.value = "自动载入失败: ${e.message}"
        }
        setContent { AppScreen(this) }
    }

    /** SAF 选中的 URI 复制到私有目录（mGBA 需要真实路径）；返回 "" 表示成功 */
    fun importRom(uri: Uri): String {
        return try {
            val dst = File(filesDir, "rom.gba")
            contentResolver.openInputStream(uri)?.use { input ->
                dst.outputStream().use { input.copyTo(it) }
            } ?: return "打开输入流失败"
            val size = dst.length()
            if (size <= 0) return "复制后文件为空"
            android.util.Log.i("NativeEmu", "rom copied: ${dst.absolutePath} $size bytes")
            romPath = dst.absolutePath
            emuReady = EmuCore.init(dst.absolutePath, "")
            if (emuReady) "" else "mGBA 初始化失败 (size=$size)"
        } catch (e: Throwable) {
            android.util.Log.e("NativeEmu", "import failed", e)
            "${e.javaClass.simpleName}: ${e.message}"
        }
    }
}

/** mGBA 帧 -> SurfaceView */
class EmuView(context: Context) : SurfaceView(context), SurfaceHolder.Callback, Runnable {
    @Volatile private var running = false
    private var thread: Thread? = null
    private var bmp: Bitmap? = null
    private val paint = Paint()

    init {
        holder.addCallback(this)
    }

    fun start() {
        if (running) return
        running = true
        thread = Thread(this).also { it.start() }
    }

    fun stop() {
        running = false
        thread?.join(500)
    }

    override fun surfaceCreated(h: SurfaceHolder) {}
    override fun surfaceChanged(h: SurfaceHolder, f: Int, w: Int, hgt: Int) {}
    override fun surfaceDestroyed(h: SurfaceHolder) { running = false }

    override fun run() {
        val gw = EmuCore.videoWidth().coerceAtLeast(240)
        val gh = EmuCore.videoHeight().coerceAtLeast(160)
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
            val c: Canvas = holder.lockCanvas() ?: continue
            try {
                c.drawColor(AndroidColor.BLACK)
                // 3:2 等比居中
                val vw = c.width
                val vh = c.height
                val scale = minOf(vw.toFloat() / gw, vh.toFloat() / gh)
                val dw = (gw * scale).toInt()
                val dh = (gh * scale).toInt()
                val dst = Rect((vw - dw) / 2, (vh - dh) / 2, (vw + dw) / 2, (vh + dh) / 2)
                c.drawBitmap(b, null, dst, paint)
            } finally {
                holder.unlockCanvasAndPost(c)
            }
        }
    }
}

@Composable
fun AppScreen(activity: MainActivity) {
    var frame by remember { mutableStateOf(0L) }
    var fps by remember { mutableStateOf(0) }
    var keys by remember { mutableStateOf(0) }
    val emuView = remember { EmuView(activity) }
    val romReady = activity.romReadyState.value
    val status = activity.statusText.value
    val running = activity.runningState.value

    // ROM 就绪后启动渲染线程
    LaunchedEffect(romReady) {
        if (romReady) emuView.start()
    }

    // 统计帧率
    LaunchedEffect(running) {
        if (!running) return@LaunchedEffect
        var last = System.currentTimeMillis()
        var cnt = 0
        while (true) {
            frame = EmuCore.frameCount()
            cnt++
            val now = System.currentTimeMillis()
            if (now - last >= 1000) { fps = cnt; cnt = 0; last = now }
            kotlinx.coroutines.delay(100)
        }
    }

    Column(Modifier.fillMaxSize().background(Color(0xFF101010))) {
        // 上屏 1:1
        Box(
            Modifier.weight(1f).fillMaxWidth().background(Color.Black),
            contentAlignment = Alignment.Center
        ) {
            AndroidView(factory = { emuView }, modifier = Modifier.fillMaxSize())
            if (!romReady) {
                Text("点下屏「载入 ROM」开始", color = Color(0xFF777777), fontSize = 12.sp)
            }
        }

        // 下屏 1:1：状态 + 控制
        Box(
            Modifier.weight(1f).fillMaxWidth().background(Color(0xFF1B1B1B))
        ) {
            Column(
                Modifier.fillMaxSize().padding(12.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text("帧 $frame  FPS $fps  $status", color = Color.White, fontSize = 13.sp)
                Text("按键 0x${Integer.toHexString(keys)}", color = Color(0xFF888888), fontSize = 11.sp)

                Row(
                    Modifier.weight(1f).fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // 十字键
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        KeyPad("▲", EmuCore.KEY_UP) { keys = it; EmuCore.setKeys(it) }
                        Row {
                            KeyPad("◀", EmuCore.KEY_LEFT) { keys = it; EmuCore.setKeys(it) }
                            Spacer(Modifier.width(26.dp))
                            KeyPad("▶", EmuCore.KEY_RIGHT) { keys = it; EmuCore.setKeys(it) }
                        }
                        KeyPad("▼", EmuCore.KEY_DOWN) { keys = it; EmuCore.setKeys(it) }
                    }
                    // A/B
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        KeyPad("B", EmuCore.KEY_B, 54.dp) { keys = it; EmuCore.setKeys(it) }
                        Spacer(Modifier.width(10.dp))
                        KeyPad("A", EmuCore.KEY_A, 54.dp) { keys = it; EmuCore.setKeys(it) }
                    }
                }

                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    Button(onClick = { activity.launchRomPicker() }) { Text("载入 ROM") }
                    Button(onClick = {
                        val nr = !activity.runningState.value
                        activity.runningState.value = nr
                        if (nr) { EmuCore.resume(); emuView.start() } else { EmuCore.pause() }
                    }) { Text(if (running) "暂停" else "继续") }
                    Button(onClick = {
                        val m = EmuCore.KEY_START
                        keys = m; EmuCore.setKeys(m)
                        android.os.Handler(android.os.Looper.getMainLooper())
                            .postDelayed({ keys = 0; EmuCore.setKeys(0) }, 120)
                    }) { Text("Start") }
                }
                Text("P1 接自动化面板", color = Color(0xFF777777), fontSize = 11.sp)
            }
        }
    }
}

/** 按下发键、松开清零 */
@Composable
fun KeyPad(label: String, mask: Int, size: androidx.compose.ui.unit.Dp = 44.dp,
           onChange: (Int) -> Unit) {
    Box(
        Modifier
            .size(size)
            .background(Color(0xFF333333), CircleShape)
            .pointerInput(mask) {
                detectTapGestures(
                    onPress = {
                        onChange(mask)
                        tryAwaitRelease()
                        onChange(0)
                    }
                )
            },
        contentAlignment = Alignment.Center
    ) {
        Text(label, color = Color.White, fontSize = 15.sp, textAlign = TextAlign.Center)
    }
}
