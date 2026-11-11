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

enum class Page { MAP, TEAM, BAG, NICK, DEX, SAVE, OPTION, BATTLE, KEYS, UPDATE }

class MainActivity : ComponentActivity() {
    val statusText = mutableStateOf("")
    val romReadyState = mutableStateOf(false)
    val runningState = mutableStateOf(false)
    val romListState = mutableStateOf<List<File>>(emptyList())
    val speedState = mutableStateOf(1)
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
        while (running) {
            var f = 0L
            repeat(speed) { f = EmuCore.runFrame() }
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
private val GREEN = Color(0xFF50B478)

data class TeamMon(val name: String, val lv: Int, val hp: Int, val max: Int)
data class EmuStatus(
    val map: String = "", val x: Int = 0, val y: Int = 0,
    val team: List<TeamMon> = emptyList(),
    val battle: String = "",
    val foeLv: Int = 0, val foeHp: Int = 0, val foeMax: Int = 0,
    val meLv: Int = 0, val meHp: Int = 0, val meMax: Int = 0,
    val moves: List<String> = emptyList(),
    val mmW: Int = 0, val mmH: Int = 0, val mmPx: Int = 0, val mmPy: Int = 0,
    val mmTiles: List<List<Int>>? = null,
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
        val mm = o.optJSONObject("minimap")
        var mmTiles: List<List<Int>>? = null
        mm?.optJSONArray("tiles")?.let { arr ->
            val rows = mutableListOf<List<Int>>()
            for (y in 0 until arr.length()) {
                val row = arr.optJSONArray(y) ?: continue
                val cells = mutableListOf<Int>()
                for (x in 0 until row.length()) cells.add(row.optInt(x))
                rows.add(cells)
            }
            if (rows.isNotEmpty()) mmTiles = rows
        }
        val d = o.optJSONObject("battle_detail")
        val foe = d?.optJSONObject("foe")
        val me = d?.optJSONObject("me")
        val moves = mutableListOf<String>()
        me?.optJSONArray("moves")?.let { arr ->
            for (i in 0 until arr.length()) moves.add(arr.optString(i, ""))
        }
        EmuStatus(
            o.optString("map", ""), o.optInt("x"), o.optInt("y"), team, o.optString("battle", ""),
            foe?.optInt("lv") ?: 0, foe?.optInt("hp") ?: 0, foe?.optInt("mhp") ?: 0,
            me?.optInt("lv") ?: 0, me?.optInt("hp") ?: 0, me?.optInt("mhp") ?: 0,
            moves,
            mm?.optInt("w") ?: 0, mm?.optInt("h") ?: 0, mm?.optInt("px") ?: 0, mm?.optInt("py") ?: 0,
            mmTiles,
        )
    } catch (e: Exception) { EmuStatus() }
}

@OptIn(androidx.compose.ui.ExperimentalComposeUiApi::class)
@Composable
fun AppScreen(activity: MainActivity) {
    var page by remember { mutableStateOf(Page.MAP) }
    var frame by remember { mutableStateOf(0L) }
    var fps by remember { mutableStateOf(0) }
    var keys by remember { mutableStateOf(0) }
    var showRoms by remember { mutableStateOf(false) }
    val emuView = remember { EmuView(activity).also { activity.emuView = it } }
    val romReady = activity.romReadyState.value
    val running = activity.runningState.value
    val roms = activity.romListState.value
    // 优先用本地 Kotlin 读取；推送数据仅作兜底
    var localJson by remember { mutableStateOf("") }
    LaunchedEffect(romReady) {
        while (romReady) {
            localJson = buildLocalStatusJson()
            kotlinx.coroutines.delay(500)
        }
    }
    val pushed = parseStatus(UiState.statusJson.value)
    val status = if (localJson.isNotBlank()) parseStatus(localJson) else pushed
    val logs = UiState.logs.value

    LaunchedEffect(romReady) { if (romReady) emuView.start() }

    // 战斗期间以战斗页为主：不在 KEYS/MENU 就切 BATTLE（关掉 KEYS 后也会回来）
    // 战斗结束回小地图
    LaunchedEffect(status.battle, page) {
        if (status.battle.isNotBlank()) {
            if (page != Page.BATTLE) page = Page.BATTLE
        } else if (page == Page.BATTLE) {
            page = Page.MAP
        }
    }

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

        // 下屏：左侧内容 + 右侧竖排 Tab
        Column(Modifier.weight(1f).fillMaxWidth().background(PANEL)) {
            Text("${if (status.map.isNotBlank()) status.map else "—"}  (${status.x}, ${status.y})   帧 $frame  FPS $fps",
                color = DIM, fontSize = 11.sp, modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp))
            Row(Modifier.weight(1f).fillMaxWidth().padding(6.dp)) {
                Box(Modifier.weight(1f).fillMaxHeight()) {
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
                        page == Page.MAP -> MinimapPage(status)
                        page == Page.TEAM -> TeamPage(status)
                        page == Page.BAG -> PlaceholderPage("背包", "需要道具列表地址")
                        page == Page.NICK -> PlaceholderPage("名字", "玩家名（需要文本地址）")
                        page == Page.DEX -> PlaceholderPage("图鉴", "需要图鉴内存结构")
                        page == Page.SAVE -> SavePage(activity, romReady, onRom = { activity.refreshRoms(); showRoms = true })
                        page == Page.OPTION -> OptionPage(activity, emuView, onUpdate = { page = Page.UPDATE })
                        page == Page.UPDATE -> UpdatePage(activity)
                        page == Page.BATTLE -> BattlePage(status, keys, { k -> keys = k; EmuCore.setKeys(k) })
                        else -> KeyPadArea(keys) { keys = it; EmuCore.setKeys(it) }
                    }
                }
                Column(Modifier.width(80.dp).fillMaxHeight().padding(start = 4.dp)) {
                    val tabs = listOf(
                        "地图" to Page.MAP, "队伍" to Page.TEAM, "背包" to Page.BAG,
                        "名字" to Page.NICK, "图鉴" to Page.DEX,
                        "存档" to Page.SAVE, "设置" to Page.OPTION,
                    )
                    for ((label, p2) in tabs) {
                        TabButton(label, page == p2, Modifier.weight(1f)) { showRoms = false; page = p2 }
                    }
                    Spacer(Modifier.height(4.dp))
                    TabButton("按键", page == Page.KEYS, Modifier.weight(1f)) { showRoms = false; page = Page.KEYS }
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
        Box(Modifier.fillMaxWidth().weight(1f).background(Color(0xFF14200F), RoundedCornerShape(12.dp))) {
            androidx.compose.foundation.Canvas(Modifier.fillMaxSize().padding(6.dp)) {
                val w = s.mmW.coerceAtLeast(1)
                val h = s.mmH.coerceAtLeast(1)
                val cw = size.width / w
                val ch = size.height / h
                val tiles = s.mmTiles
                for (y in 0 until h) for (x in 0 until w) {
                    val pass = tiles?.getOrNull(y)?.getOrNull(x)?.let { it == 1 } ?: true
                    drawRect(
                        color = if (pass) Color(0xFF2E4B2A) else Color(0xFF0D0D0D),
                        topLeft = androidx.compose.ui.geometry.Offset(x * cw, y * ch),
                        size = androidx.compose.ui.geometry.Size(cw - 0.5f, ch - 0.5f),
                    )
                }
                // 玩家位置（按比例映射到格子）
                val px = (s.mmPx.toFloat() / w).coerceIn(0f, 0.999f)
                val py = (s.mmPy.toFloat() / h).coerceIn(0f, 0.999f)
                drawCircle(Color(0xFFFF4040), radius = minOf(cw, ch) * 0.45f,
                    center = androidx.compose.ui.geometry.Offset(px * size.width + cw / 2, py * size.height + ch / 2))
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
    speed: Int,
    onSpeed: () -> Unit,
    onRom: () -> Unit, onSave: () -> Unit, onLoad: () -> Unit,
    onKeys: () -> Unit, onLog: () -> Unit, onMap: () -> Unit,
    onUpdate: () -> Unit,
) {
    val items = listOf(
        "ROM" to onRom, "存档" to onSave, "读档" to onLoad,
        "按键" to onKeys, "日志" to onLog, "地图" to onMap,
        "更新" to onUpdate, "${speed}x" to onSpeed,
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


@Composable
private fun UpdatePage(activity: MainActivity) {
    var checking by remember { mutableStateOf(false) }
    var latest by remember { mutableStateOf<Updater.Release?>(null) }
    var error by remember { mutableStateOf("") }
    var progress by remember { mutableStateOf(-1) }
    val buildTime = remember {
        try {
            java.text.SimpleDateFormat("MM-dd HH:mm", java.util.Locale.getDefault())
                .format(java.util.Date(BuildConfig.BUILD_TIME.toLong()))
        } catch (e: Exception) { "?" }
    }
    Column(Modifier.fillMaxSize().padding(4.dp)) {
        Text("版本 ${BuildConfig.VERSION_NAME} (${BuildConfig.GIT_SHA})", color = TXT, fontSize = 12.sp)
        Text("构建 $buildTime", color = DIM, fontSize = 11.sp)
        Spacer(Modifier.height(8.dp))
        Box(Modifier.background(if (checking) CARD else ACCENT, RoundedCornerShape(10.dp))
            .clickable {
                if (checking) return@clickable
                checking = true; error = ""
                Thread {
                    val r = Updater.latest()
                    activity.runOnUiThread {
                        checking = false
                        if (r == null) error = "检查失败（网络或没有 release）" else latest = r
                    }
                }.start()
            }.padding(horizontal = 18.dp, vertical = 8.dp)) {
            Text(if (checking) "检查中…" else "检查更新", color = Color.White, fontSize = 12.sp)
        }
        if (error.isNotBlank()) Text(error, color = Color(0xFFFF8080), fontSize = 11.sp)
        latest?.let { r ->
            Spacer(Modifier.height(8.dp))
            Text("最新: ${r.tag}", color = TXT, fontSize = 12.sp)
            Text(r.body.take(400), color = DIM, fontSize = 11.sp)
            Spacer(Modifier.height(6.dp))
            Box(Modifier.background(if (progress >= 0) CARD else ACCENT, RoundedCornerShape(10.dp)).clickable {
                if (progress >= 0) return@clickable
                progress = 0
                Thread {
                    val f = File(activity.cacheDir, "update.apk")
                    val ok = Updater.download(r.url, f) { pct ->
                        activity.runOnUiThread { progress = pct }
                    }
                    activity.runOnUiThread {
                        if (ok) {
                            progress = -1
                            if (!Updater.install(activity, f)) {
                                activity.statusText.value = "请在设置里允许「安装未知应用」后重试"
                            }
                        } else {
                            progress = -1
                            activity.statusText.value = "下载失败"
                        }
                    }
                }.start()
            }.padding(horizontal = 18.dp, vertical = 8.dp)) {
                Text(if (progress >= 0) "下载中 $progress%" else "下载并安装", color = Color.White, fontSize = 12.sp)
            }
            if (progress >= 0) {
                Spacer(Modifier.height(6.dp))
                androidx.compose.material3.LinearProgressIndicator(
                    progress = { progress / 100f },
                    modifier = Modifier.fillMaxWidth().height(6.dp),
                    color = ACCENT,
                )
            }
        }
    }
}


@Composable
private fun BattlePage(s: EmuStatus, keysState: Int, onChange: (Int) -> Unit) {
    Column(Modifier.fillMaxSize().padding(4.dp)) {
        // 敌方
        Text("敌方  Lv${s.foeLv}   ${s.foeHp}/${s.foeMax}", color = Color(0xFFFF9090), fontSize = 12.sp)
        androidx.compose.material3.LinearProgressIndicator(
            progress = { if (s.foeMax > 0) s.foeHp.toFloat() / s.foeMax else 0f },
            modifier = Modifier.fillMaxWidth().height(6.dp), color = Color(0xFFFF6060))
        Spacer(Modifier.height(6.dp))
        // 我方
        Text("我方  Lv${s.meLv}   ${s.meHp}/${s.meMax}", color = TXT, fontSize = 12.sp)
        androidx.compose.material3.LinearProgressIndicator(
            progress = { if (s.meMax > 0) s.meHp.toFloat() / s.meMax else 0f },
            modifier = Modifier.fillMaxWidth().height(6.dp), color = GREEN)
        Spacer(Modifier.height(8.dp))
        // 4 招式（只显示，不点，避免误操作）
        Column(Modifier.weight(1f).fillMaxWidth()) {
            for (row in listOf(0, 1)) {
                Row(Modifier.weight(1f)) {
                    for (col in 0..1) {
                        val idx = row * 2 + col
                        val mv = s.moves.getOrNull(idx).orEmpty()
                        Box(Modifier.weight(1f).fillMaxHeight().padding(4.dp)
                            .background(CARD, RoundedCornerShape(10.dp)),
                            contentAlignment = Alignment.Center) {
                            Text(if (mv.isNotEmpty()) mv else "—", color = if (mv.isNotEmpty()) TXT else DIM, fontSize = 13.sp)
                        }
                    }
                }
            }
        }
        // 战斗中也要能按键：把按键区嵌进来
        Box(Modifier.fillMaxWidth().height(120.dp)) {
            KeyPadArea(keysState, onChange)
        }
    }
}


@Composable
private fun TabButton(label: String, active: Boolean, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Box(
        modifier.fillMaxWidth().padding(vertical = 2.dp)
            .background(if (active) ACCENT else CARD, RoundedCornerShape(8.dp))
            .clickable { onClick() },
        contentAlignment = Alignment.Center
    ) {
        Text(label, color = if (active) Color.White else DIM, fontSize = 11.sp)
    }
}

@Composable
private fun PlaceholderPage(title: String, hint: String) {
    Box(Modifier.fillMaxSize().background(CARD, RoundedCornerShape(10.dp)), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(title, color = TXT, fontSize = 14.sp)
            Text(hint, color = DIM, fontSize = 11.sp)
        }
    }
}

@Composable
private fun TeamPage(s: EmuStatus) {
    Column(Modifier.fillMaxSize()) {
        if (s.team.isEmpty()) {
            PlaceholderPage("队伍", "等待推送（或还没拿到宝可梦）")
        } else {
            for (m in s.team) {
                Row(Modifier.fillMaxWidth().padding(vertical = 3.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(m.name, color = TXT, fontSize = 13.sp, modifier = Modifier.weight(1f))
                    Text("Lv${m.lv}", color = DIM, fontSize = 11.sp, modifier = Modifier.width(42.dp))
                    Text("${m.hp}/${m.max}", color = if (m.max > 0 && m.hp * 3 < m.max) Color(0xFFFF6060) else TXT, fontSize = 11.sp)
                }
                androidx.compose.material3.LinearProgressIndicator(
                    progress = { if (m.max > 0) m.hp.toFloat() / m.max else 0f },
                    modifier = Modifier.fillMaxWidth().height(4.dp), color = GREEN)
            }
        }
    }
}

@Composable
private fun SavePage(activity: MainActivity, romReady: Boolean, onRom: () -> Unit) {
    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Box(Modifier.fillMaxWidth().weight(1f).background(CARD, RoundedCornerShape(10.dp)).clickable {
            if (romReady) activity.statusText.value =
                if (EmuCore.saveState(File(activity.filesDir, "state1.sav").absolutePath)) "已存档" else "存档失败"
        }, contentAlignment = Alignment.Center) { Text("即时存档", color = TXT, fontSize = 14.sp) }
        Box(Modifier.fillMaxWidth().weight(1f).background(CARD, RoundedCornerShape(10.dp)).clickable {
            if (romReady) activity.statusText.value =
                if (EmuCore.loadState(File(activity.filesDir, "state1.sav").absolutePath)) "已读档" else "读档失败"
        }, contentAlignment = Alignment.Center) { Text("读取存档", color = TXT, fontSize = 14.sp) }
        Box(Modifier.fillMaxWidth().weight(1f).background(CARD, RoundedCornerShape(10.dp)).clickable {
            onRom()
        }, contentAlignment = Alignment.Center) { Text("载入 ROM", color = TXT, fontSize = 14.sp) }
    }
}

@Composable
private fun OptionPage(activity: MainActivity, emuView: EmuView, onUpdate: () -> Unit) {
    val speed = activity.speedState.value
    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Box(Modifier.fillMaxWidth().weight(1f).background(CARD, RoundedCornerShape(10.dp)).clickable {
            val next = when (activity.speedState.value) { 1 -> 2; 2 -> 4; else -> 1 }
            activity.speedState.value = next
            emuView.speed = next
        }, contentAlignment = Alignment.Center) { Text("速度 ${speed}x", color = TXT, fontSize = 14.sp) }
        Box(Modifier.fillMaxWidth().weight(1f).background(ACCENT, RoundedCornerShape(10.dp)).clickable {
            onUpdate()
        }, contentAlignment = Alignment.Center) { Text("更新", color = Color.White, fontSize = 14.sp) }
    }
}


/** 用 Kotlin GameState 直接读内存，组装下屏用的 JSON（与 Python 推送格式一致）。 */
private fun buildLocalStatusJson(): String {
    return try {
        val c = com.dsh.emu.game.GameState.coords()
        val party = com.dsh.emu.game.GameState.party()
        val scene = com.dsh.emu.game.GameState.scene()
        val battle = if (scene.startsWith("battle")) scene else ""
        val o = org.json.JSONObject()
        o.put("map", scene)
        o.put("x", c?.x ?: 0)
        o.put("y", c?.y ?: 0)
        o.put("battle", battle)
        val team = org.json.JSONArray()
        for (m in party) {
            val t = org.json.JSONObject()
            t.put("name", "#" + (m.slot + 1))
            t.put("lv", m.lv)
            t.put("hp", m.hp)
            t.put("max", m.maxHp)
            team.put(t)
        }
        o.put("team", team)
        if (battle.isNotBlank()) {
            val detail = org.json.JSONObject()
            val moves = org.json.JSONArray()
            for (mid in com.dsh.emu.game.GameState.myMoves()) {
                val info = com.dsh.emu.game.GameData.moves[mid]
                moves.put(if (info != null) info.first else "")
            }
            val me = org.json.JSONObject()
            me.put("lv", party.firstOrNull()?.lv ?: 0)
            me.put("hp", party.firstOrNull()?.hp ?: 0)
            me.put("mhp", party.firstOrNull()?.maxHp ?: 0)
            me.put("moves", moves)
            detail.put("me", me)
            val foe = org.json.JSONObject()
            foe.put("lv", 0)
            foe.put("hp", 0)
            foe.put("mhp", 0)
            detail.put("foe", foe)
            o.put("battle_detail", detail)
        }
        o.toString()
    } catch (e: Throwable) {
        ""
    }
}
