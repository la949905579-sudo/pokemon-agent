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
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInteropFilter
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONObject
import java.io.File

enum class Page { MINIMAP, MENU, LOG, KEYS }

class MainActivity : ComponentActivity() {
    val statusText = mutableStateOf("")
    val romReadyState = mutableStateOf(false)
    val runningState = mutableStateOf(false)
    val romListState = mutableStateOf<List<File>>(emptyList())
    var emuView: EmuView? = null
    private val bridge = BridgeServer(55401)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        try {
            startForegroundService(android.content.Intent(this, EmuService::class.java))
        } catch (_: Throwable) {}
        val ok = bridge.start()
        statusText.value = if (ok) "TCP :55401" else ""
        setContent { AppScreen(this) }
    }

    override fun onDestroy() {
        bridge.stop()
        super.onDestroy()
    }

    fun hasAllFiles(): Boolean =
        if (android.os.Build.VERSION.SDK_INT >= 30) android.os.Environment.isExternalStorageManager() else true

    fun openAllFilesSettings() {
        try {
            startActivity(android.content.Intent(
                android.provider.Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
                android.net.Uri.parse("package:$packageName")))
        } catch (e: Throwable) { statusText.value = "权限页打不开" }
    }

    fun scanRoms(): List<File> {
        if (!hasAllFiles()) return emptyList()
        val out = mutableListOf<File>()
        for (d in listOf("/sdcard/rom/gba", "/sdcard/Download", "/sdcard/Documents")) {
            File(d).listFiles()?.filter { it.isFile && it.name.lowercase().endsWith(".gba") }?.let { out.addAll(it) }
        }
        return out.distinctBy {
            try { it.canonicalPath } catch (e: Exception) { it.absolutePath }
        }.sortedBy { it.name }
    }

    fun refreshRoms() {
        if (!hasAllFiles()) { openAllFilesSettings(); return }
        romListState.value = scanRoms()
        statusText.value = if (romListState.value.isEmpty()) "没找到 ROM" else "${romListState.value.size} 个 ROM"
    }

    fun loadRom(rom: File) {
        statusText.value = "载入中..."
        var ok = false
        for (attempt in 0 until 4) {
            ok = EmuCore.init(rom.absolutePath, "")
            if (ok) break
            try { Thread.sleep(120) } catch (_: InterruptedException) {}
        }
        romReadyState.value = ok
        statusText.value = if (ok) rom.name.take(24) else "初始化失败（重试 4 次）"
        if (ok) { EmuCore.start(); runningState.value = true }
    }
}

class EmuView(context: Context) : SurfaceView(context), SurfaceHolder.Callback, Runnable {
    @Volatile private var running = false
    @Volatile private var shouldRun = false
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
        while (running) {
            val f = EmuCore.runFrame()
            if (f == 0L) { Thread.sleep(16); continue }
            val px = EmuCore.frameBuffer() ?: continue
            if (surfaceReady) {
                var b = bmp
                if (b == null || b.width != gw || b.height != gh) {
                    b = Bitmap.createBitmap(gw, gh, Bitmap.Config.ARGB_8888); bmp = b
                }
                b.setPixels(px, 0, gw, 0, 0, gw, gh)
                val c: Canvas? = try {
                    if (android.os.Build.VERSION.SDK_INT >= 26) holder.lockHardwareCanvas() else holder.lockCanvas()
                } catch (e: Throwable) { null }
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
        }
    }
}

// ---------- 下屏 UI ----------

private val BG = Color(0xFF101010)
private val PANEL = Color(0xFF1B1B1B)
private val CARD = Color(0xFF2C2C2C)
private val ACCENT = Color(0xFF7B5CE5)
private val TXT = Color(0xFFEBEBEB)
private val DIM = Color(0xFF8C8C8C)

data class TeamMon(val name: String, val lv: Int, val hp: Int, val max: Int)
data class EmuStatus(
    val map: String = "", val x: Int = 0, val y: Int = 0,
    val team: List<TeamMon> = emptyList(),
    val battle: String = "",
)

private fun parseStatus(json: String): EmuStatus {
    if (json.isBlank()) return EmuStatus()
    return try {
        val o = JSONObject(json)
        val team = mutableListOf<TeamMon>()
        o.optJSONArray("team")?.let { arr ->
            for (i in 0 until arr.length()) {
                val t = arr.getJSONObject(i)
                team.add(TeamMon(t.optString("name", "?"), t.optInt("lv"), t.optInt("hp"), t.optInt("max")))
            }
        }
        EmuStatus(o.optString("map", ""), o.optInt("x"), o.optInt("y"), team, o.optString("battle", ""))
    } catch (e: Exception) { EmuStatus() }
}

@OptIn(androidx.compose.ui.ExperimentalComposeUiApi::class)
@Composable
fun AppScreen(activity: MainActivity) {
    var page by remember { mutableStateOf(Page.MINIMAP) }
    var frame by remember { mutableStateOf(0L) }
    var fps by remember { mutableStateOf(0) }
    var keys by remember { mutableStateOf(0) }
    var showRoms by remember { mutableStateOf(false) }
    val emuView = remember { EmuView(activity).also { activity.emuView = it } }
    val romReady = activity.romReadyState.value
    val running = activity.runningState.value
    val roms = activity.romListState.value
    val status = parseStatus(UiState.statusJson.value)
    val logs = UiState.logs.value

    LaunchedEffect(romReady) { if (romReady) emuView.start() }

    LaunchedEffect(running) {
        if (!running) return@LaunchedEffect
        var last = EmuCore.frameCount()
        while (true) {
            kotlinx.coroutines.delay(1000)
            val now = EmuCore.frameCount()
            frame = now; fps = (now - last).toInt(); last = now
        }
    }

    Column(Modifier.fillMaxSize().background(BG)) {
        // 上屏
        Box(Modifier.weight(1f).fillMaxWidth().background(Color.Black), contentAlignment = Alignment.Center) {
            AndroidView(factory = { emuView }, modifier = Modifier.fillMaxSize())
            if (!romReady) Text("点 MENU → ROM 选择游戏", color = DIM, fontSize = 12.sp)
        }

        // 下屏
        Column(Modifier.weight(1f).fillMaxWidth().background(PANEL).padding(8.dp)) {
            Text("${if (status.map.isNotBlank()) status.map else "—"}  (${status.x}, ${status.y})   帧 $frame  FPS $fps",
                color = DIM, fontSize = 11.sp)

            Box(Modifier.weight(1f).fillMaxWidth()) {
                when {
                    showRoms -> LazyColumn(Modifier.fillMaxSize()) {
                        items(roms) { f ->
                            Text(f.name, color = Color(0xFF9AD0FF), fontSize = 12.sp,
                                modifier = Modifier.fillMaxWidth().clickable {
                                    showRoms = false
                                    activity.loadRom(f)
                                }.padding(vertical = 6.dp))
                        }
                    }
                    page == Page.MINIMAP -> MinimapPage(status)
                    page == Page.MENU -> MenuPage(
                        onRom = { activity.refreshRoms(); showRoms = true },
                        onSave = {
                            if (romReady) activity.statusText.value =
                                if (EmuCore.saveState(File(activity.filesDir, "state1.sav").absolutePath)) "已存档" else "存档失败"
                        },
                        onLoad = {
                            if (romReady) activity.statusText.value =
                                if (EmuCore.loadState(File(activity.filesDir, "state1.sav").absolutePath)) "已读档" else "读档失败"
                        },
                        onKeys = { page = Page.KEYS },
                        onLog = { page = Page.LOG },
                        onMap = { page = Page.MINIMAP },
                        onUpdate = {
                            Thread {
                                val rel = Updater.latest()
                                if (rel == null) {
                                    activity.statusText.value = "检查更新失败"
                                    return@Thread
                                }
                                activity.statusText.value = "下载 ${rel.tag}..."
                                val f = File(activity.cacheDir, "update.apk")
                                if (Updater.download(rel.url, f)) {
                                    activity.runOnUiThread { Updater.install(activity, f) }
                                } else {
                                    activity.statusText.value = "下载失败"
                                }
                            }.start()
                        },
                    )
                    page == Page.LOG -> LazyColumn(Modifier.fillMaxSize()) {
                        items(logs) { Text(it, color = TXT, fontSize = 11.sp) }
                    }
                    else -> KeyPadArea(keys) { keys = it; EmuCore.setKeys(it) }
                }
            }

            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                BarButton("KEYS", page == Page.KEYS) {
                    showRoms = false
                    page = if (page == Page.KEYS) Page.MINIMAP else Page.KEYS
                }
                BarButton("MENU", page == Page.MENU) {
                    showRoms = false
                    page = if (page == Page.MENU) Page.MINIMAP else Page.MENU
                }
                BarButton("LOG", page == Page.LOG) {
                    showRoms = false
                    page = if (page == Page.LOG) Page.MINIMAP else Page.LOG
                }
            }
        }
    }
}

@Composable
private fun BarButton(label: String, active: Boolean, onClick: () -> Unit) {
    Text(label, color = if (active) Color.White else DIM, fontSize = 12.sp,
        modifier = Modifier.clickable { onClick() }
            .background(if (active) ACCENT else CARD, RoundedCornerShape(8.dp))
            .padding(horizontal = 22.dp, vertical = 6.dp))
}

@Composable
private fun MinimapPage(s: EmuStatus) {
    Column(Modifier.fillMaxSize()) {
        Box(Modifier.fillMaxWidth().weight(1f).background(Color(0xFF1E321E), RoundedCornerShape(12.dp))) {
            for (i in 0 until 6) {
                Box(Modifier.offset((20 + i * 52).dp, 20.dp).size(40.dp, 30.dp).background(Color(0xFF325032)))
            }
            if (s.x != 0 || s.y != 0) {
                Box(Modifier.offset((20 + (s.x % 6) * 52).dp, (20 + (s.y % 3) * 34).dp).size(10.dp).background(Color(0xFFFF5050), CircleShape))
            }
        }
        Spacer(Modifier.height(6.dp))
        if (s.battle.isNotBlank()) Text("⚔ ${s.battle}", color = Color(0xFFFFB060), fontSize = 12.sp)
        for (m in s.team) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text(m.name, color = TXT, fontSize = 12.sp, modifier = Modifier.weight(1f))
                Text("Lv${m.lv}", color = DIM, fontSize = 11.sp, modifier = Modifier.width(48.dp))
                Text("${m.hp}/${m.max}", color = if (m.max > 0 && m.hp * 3 < m.max) Color(0xFFFF6060) else TXT, fontSize = 11.sp)
            }
        }
        if (s.team.isEmpty()) Text("等待 Python 推送状态…", color = DIM, fontSize = 11.sp)
    }
}

@Composable
private fun MenuPage(
    onRom: () -> Unit, onSave: () -> Unit, onLoad: () -> Unit,
    onKeys: () -> Unit, onLog: () -> Unit, onMap: () -> Unit,
    onUpdate: () -> Unit,
) {
    val items = listOf(
        "ROM" to onRom, "存档" to onSave, "读档" to onLoad,
        "按键" to onKeys, "日志" to onLog, "地图" to onMap,
        "更新" to onUpdate,
    )
    Column(Modifier.fillMaxSize()) {
        for (row in items.chunked(3)) {
            Row(Modifier.fillMaxWidth().weight(1f)) {
                for ((label, action) in row) {
                    Box(Modifier.weight(1f).fillMaxHeight().padding(4.dp)
                        .background(CARD, RoundedCornerShape(12.dp))
                        .clickable { action() }, contentAlignment = Alignment.Center) {
                        Text(label, color = TXT, fontSize = 14.sp)
                    }
                }
            }
        }
    }
}

@OptIn(androidx.compose.ui.ExperimentalComposeUiApi::class)
@Composable
private fun KeyPadArea(keys: Int, onChange: (Int) -> Unit) {
    var areaOrigin by remember { mutableStateOf(Offset.Zero) }
    val pads = remember { mutableStateListOf<PadPos>() }
    val pointerMasks = remember { mutableMapOf<Int, Int>() }
    Box(Modifier.fillMaxSize().onGloballyPositioned {
        areaOrigin = it.localToWindow(Offset.Zero)
    }.pointerInteropFilter { ev ->
        val action = ev.actionMasked
        fun hit(idx: Int): Int {
            val px = ev.getX(idx) + areaOrigin.x
            val py = ev.getY(idx) + areaOrigin.y
            for (p in pads) {
                val dx = px - p.cx; val dy = py - p.cy
                if (dx * dx + dy * dy <= p.r * p.r) return p.mask
            }
            return 0
        }
        when (action) {
            android.view.MotionEvent.ACTION_DOWN, android.view.MotionEvent.ACTION_POINTER_DOWN -> {
                val i = ev.actionIndex; val m = hit(i)
                if (m != 0) pointerMasks[ev.getPointerId(i)] = m
            }
            android.view.MotionEvent.ACTION_MOVE -> for (i in 0 until ev.pointerCount) {
                val id = ev.getPointerId(i); val m = hit(i)
                if (m != 0) pointerMasks[id] = m else pointerMasks.remove(id)
            }
            android.view.MotionEvent.ACTION_POINTER_UP -> pointerMasks.remove(ev.getPointerId(ev.actionIndex))
            android.view.MotionEvent.ACTION_UP, android.view.MotionEvent.ACTION_CANCEL -> pointerMasks.clear()
        }
        var mask = 0
        for (m in pointerMasks.values) mask = mask or m
        if (mask != keys) onChange(mask)
        true
    }) {
        Row(Modifier.fillMaxSize(), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                PadLabel("▲", EmuCore.KEY_UP, pads, pressed = (keys and EmuCore.KEY_UP) != 0)
                Row {
                    PadLabel("◀", EmuCore.KEY_LEFT, pads, pressed = (keys and EmuCore.KEY_LEFT) != 0)
                    Spacer(Modifier.width(18.dp))
                    PadLabel("▶", EmuCore.KEY_RIGHT, pads, pressed = (keys and EmuCore.KEY_RIGHT) != 0)
                }
                PadLabel("▼", EmuCore.KEY_DOWN, pads, pressed = (keys and EmuCore.KEY_DOWN) != 0)
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                PadLabel("B", EmuCore.KEY_B, pads, 52.dp, (keys and EmuCore.KEY_B) != 0)
                Spacer(Modifier.width(10.dp))
                PadLabel("A", EmuCore.KEY_A, pads, 52.dp, (keys and EmuCore.KEY_A) != 0)
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                PadLabel("ST", EmuCore.KEY_START, pads, 40.dp, (keys and EmuCore.KEY_START) != 0)
                Spacer(Modifier.height(8.dp))
                PadLabel("SE", EmuCore.KEY_SELECT, pads, 40.dp, (keys and EmuCore.KEY_SELECT) != 0)
            }
        }
    }
}

data class PadPos(val mask: Int, val cx: Float, val cy: Float, val r: Float)

@Composable
fun PadLabel(label: String, mask: Int, pads: MutableList<PadPos>, size: androidx.compose.ui.unit.Dp = 44.dp, pressed: Boolean = false) {
    val density = LocalDensity.current
    val radiusPx = with(density) { size.toPx() / 2f } * 0.92f
    Box(
        Modifier.size(size)
            .background(if (pressed) ACCENT else Color(0xFF333333), CircleShape)
            .onGloballyPositioned {
                val c = it.localToWindow(Offset(it.size.width / 2f, it.size.height / 2f))
                pads.removeAll { p -> p.mask == mask }
                pads.add(PadPos(mask, c.x, c.y, radiusPx))
            },
        contentAlignment = Alignment.Center
    ) {
        Text(label, color = Color.White, fontSize = 13.sp, textAlign = TextAlign.Center)
    }
}
