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
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInteropFilter
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONObject
import java.io.File

enum class Page { MAP, TEAM, BAG, NICK, DEX, SAVE, OPTION, BATTLE, UPDATE }

class MainActivity : ComponentActivity() {
    val statusText = mutableStateOf("")
    val romReadyState = mutableStateOf(false)
    val runningState = mutableStateOf(false)
    val romListState = mutableStateOf<List<File>>(emptyList())
    val speedState = mutableStateOf(1)
    val downloadProgress = mutableStateOf(-1)
    val updateLatest = mutableStateOf<Updater.Release?>(null)
    val updateError = mutableStateOf("")
    var emuView: EmuView? = null
    private val bridge = BridgeServer(55401)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // 地图数据打包在 APK assets 里（13 张，~70KB），不再依赖 /sdcard 与 Python 推送
        try { com.dsh.emu.game.MapData.loadAssets(this) } catch (_: Throwable) {}
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
        if (ok) {
            EmuCore.start()
            runningState.value = true
            // 读 ROM 的 BaseStats 表拿成长类型（16MB 扫描，必须放后台）
            try {
                Thread { com.dsh.emu.game.Growth.prepare(rom) }.start()
            } catch (_: Throwable) {}
        }
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

/** 队伍里的一只；读不到的字段留空/负数，UI 显示 --（见 TeamPage 详情）。 */
data class TeamMove(val name: String, val pp: Int, val maxPp: Int?)
data class TeamMon(
    val name: String, val lv: Int, val hp: Int, val max: Int,
    val types: List<String> = emptyList(),
    val moves: List<TeamMove> = emptyList(),
    val exp: Long = -1L,
    /** 当前等级的经验下限 / 下一级阈值；-1 = 数据不够（UI 显示 --） */
    val expCur: Long = -1L,
    val expNext: Long = -1L,
    /** 已满级（100 级没有下一级阈值，UI 显示「已满级」而不是 --） */
    val expMax: Boolean = false,
)
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
                val types = mutableListOf<String>()
                t.optJSONArray("types")?.let { a ->
                    for (k in 0 until a.length()) a.optString(k, "").takeIf { it.isNotEmpty() }?.let { types.add(it) }
                }
                val moves = mutableListOf<TeamMove>()
                t.optJSONArray("moves")?.let { a ->
                    for (k in 0 until a.length()) {
                        val mo = a.optJSONObject(k) ?: continue
                        moves.add(TeamMove(
                            mo.optString("name", ""),
                            if (mo.has("pp")) mo.optInt("pp") else -1,
                            if (mo.has("max")) mo.optInt("max") else null,
                        ))
                    }
                }
                team.add(TeamMon(t.optString("name", "?"), t.optInt("lv"), t.optInt("hp"), t.optInt("max"),
                    types, moves, if (t.has("exp")) t.optLong("exp") else -1L,
                    if (t.has("expCur")) t.optLong("expCur") else -1L,
                    if (t.has("expNext")) t.optLong("expNext") else -1L,
                    t.optBoolean("expMax", false)))
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
    // null = 用户没手动打开 Tab：内容区显示常驻页（战斗中→战斗页，否则→当前地图页）
    var tabPage by remember { mutableStateOf<Page?>(null) }
    var frame by remember { mutableStateOf(0L) }
    var fps by remember { mutableStateOf(0) }
    var keys by remember { mutableStateOf(0) }
    var keysOpen by remember { mutableStateOf(false) }
    var showRoms by remember { mutableStateOf(false) }
    // 统一收起按键面板：必须同时清按键掩码。
    // 否则手指正按在面板上时切页/载入 ROM，面板关了但 setKeys 还留着旧掩码，角色会一直走。
    val closeKeys = {
        keysOpen = false
        keys = 0
        EmuCore.setKeys(0)
        // 同时取消正在进行的「点击前往」，否则角色会把剩余步数走完
        WalkControl.generation++
    }
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
    val status = if (localJson.isNotBlank()) {
        val local = parseStatus(localJson)
        // 地图数据以本地（assets/内存）为准；本地完全没有时才用 Python 推送兜底
        if (local.mmTiles == null && (pushed.mmTiles != null || pushed.mmW > 0)) {
            local.copy(mmW = pushed.mmW, mmH = pushed.mmH, mmPx = pushed.mmPx,
                mmPy = pushed.mmPy, mmTiles = pushed.mmTiles)
        } else local
    } else pushed
    val logs = UiState.logs.value
    // 常驻页自动切换：战斗中 → 战斗页，否则 → 当前地图页。
    // 手动打开 Tab 时保留 Tab，不会被战斗开始/结束顶掉（旧版「抢页」问题的根因）。
    val inBattle = status.battle.isNotBlank()

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

        // 下屏：左侧内容 + 右侧竖排 Tab + 最底边常驻按键折叠条
        Column(Modifier.weight(1f).fillMaxWidth().background(PANEL)) {
            Text("${if (status.map.isNotBlank()) status.map else "—"}  (${status.x}, ${status.y})   帧 $frame  FPS $fps",
                color = DIM, fontSize = 11.sp, modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp))
            Row(Modifier.weight(1f).fillMaxWidth().padding(start = 6.dp, top = 6.dp, end = 6.dp, bottom = 4.dp)) {
                Box(Modifier.weight(1f).fillMaxHeight()) {
                    when {
                        // 按键面板：展开时替换内容区（不是浮层叠加）
                        keysOpen -> KeyPadArea(keys) { k -> keys = k; EmuCore.setKeys(k) }
                        showRoms -> LazyColumn(Modifier.fillMaxSize()) {
                            items(roms) { f ->
                                Text(f.name, color = Color(0xFF9AD0FF), fontSize = 12.sp,
                                    modifier = Modifier.fillMaxWidth().clickable {
                                        showRoms = false
                                        closeKeys()
                                        activity.loadRom(f)
                                    }.padding(vertical = 6.dp))
                            }
                        }
                        tabPage == Page.MAP -> TownMapPage(status) { tx, ty ->
                            walkTo(activity, status, tx, ty)
                        }
                        tabPage == Page.TEAM -> TeamPage(status)
                        tabPage == Page.BAG -> PlaceholderPage("背包", "需要道具列表地址")
                        tabPage == Page.NICK -> PlaceholderPage("名字", "玩家名（需要文本地址）")
                        tabPage == Page.DEX -> PlaceholderPage("图鉴", "需要图鉴内存结构")
                        tabPage == Page.SAVE -> SavePage(activity, romReady)
                        tabPage == Page.OPTION -> OptionPage(activity, emuView, onUpdate = { tabPage = Page.UPDATE },
                            onRom = { activity.refreshRoms(); showRoms = true })
                        tabPage == Page.UPDATE -> UpdatePage(activity)
                        // 没手动开 Tab：常驻页自动切换（战斗中战斗页 / 否则当前地图页）
                        else -> if (inBattle) BattlePage(status) else CurrentMapPage(status)
                    }
                }
                Column(Modifier.width(80.dp).fillMaxHeight().padding(start = 4.dp)) {
                    val tabs = listOf(
                        "地图" to Page.MAP, "队伍" to Page.TEAM, "背包" to Page.BAG,
                        "名字" to Page.NICK, "图鉴" to Page.DEX,
                        "存档" to Page.SAVE, "设置" to Page.OPTION,
                    )
                    for ((label, p2) in tabs) {
                        // 设置页里的「更新」子页也算设置 Tab 处于打开状态
                        val active = tabPage == p2 ||
                            (p2 == Page.OPTION && tabPage == Page.UPDATE)
                        TabButton(label, active, Modifier.weight(1f)) {
                            showRoms = false
                            closeKeys()
                            // 再点同一个 Tab = 关闭，回到常驻页；点别的 Tab = 直接切换
                            tabPage = if (tabPage == p2) null else p2
                        }
                    }
                }
            }
            // 常驻折叠条：任何页面（包括战斗中）都能打开按键面板
            KeyBar(keysOpen) {
                if (keysOpen) {
                    closeKeys()
                } else {
                    WalkControl.generation++   // 打开面板也算离开地图操作，先停掉正在走的路线
                    keysOpen = true
                }
            }
        }
    }
}

/** 最底边的按键折叠条：点击开合；展开时向下拖拽也能收起。 */
@Composable
private fun KeyBar(open: Boolean, onToggle: () -> Unit) {    var dragDown by remember { mutableStateOf(0f) }
    Box(
        Modifier.fillMaxWidth().height(32.dp)
            .background(if (open) ACCENT else CARD, RoundedCornerShape(topStart = 8.dp, topEnd = 8.dp))
            .pointerInput(open) {
                detectVerticalDragGestures(
                    onDragStart = { dragDown = 0f },
                    onDragEnd = { if (open && dragDown > 24f) onToggle() },
                    onDragCancel = { dragDown = 0f },
                ) { _, dy -> dragDown += dy }
            }
            .clickable { onToggle() },
        contentAlignment = Alignment.Center
    ) {
        Text(if (open) "▼ 收起按键" else "▲ 按键", color = if (open) Color.White else DIM, fontSize = 12.sp)
    }
}

/**
 * 常驻「当前地图页」：以玩家为中心、tile 级的只读视口，随移动刷新。
 * 注意：和右侧 Tab 的「大地图」（整张当前地图、可点走）是两个独立组件，不共用。
 */
@Composable
private fun CurrentMapPage(s: EmuStatus) {
    val tiles = s.mmTiles
    if (tiles == null || s.mmW <= 0 || s.mmH <= 0) {
        PlaceholderPage("当前地图", "等待地图数据…")
        return
    }
    val viewW = 15
    val viewH = 9
    val px = s.mmPx
    val py = s.mmPy
    Box(Modifier.fillMaxSize().background(Color(0xFF14200F), RoundedCornerShape(12.dp))) {
        androidx.compose.foundation.Canvas(Modifier.fillMaxSize().padding(4.dp)) {
            val cw = size.width / viewW
            val ch = size.height / viewH
            val x0 = px - viewW / 2
            val y0 = py - viewH / 2
            for (vy in 0 until viewH) for (vx in 0 until viewW) {
                val pass = tiles.getOrNull(y0 + vy)?.getOrNull(x0 + vx) == 1
                drawRect(
                    color = if (pass) Color(0xFF2E4B2A) else Color(0xFF0D0D0D),
                    topLeft = Offset(vx * cw, vy * ch),
                    size = Size(cw - 0.5f, ch - 0.5f),
                )
            }
            // 玩家固定在视口中心
            drawCircle(
                color = Color(0xFFFF4040),
                radius = minOf(cw, ch) * 0.45f,
                center = Offset((viewW / 2 + 0.5f) * cw, (viewH / 2 + 0.5f) * ch),
            )
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

/**
 * 「地图」Tab：当前所在城镇/道路的整张 tile 地图，点格子会真按方向键走过去。
 * 与常驻的 CurrentMapPage（以玩家为中心的只读视口）是两个独立组件，别复用。
 */
@Composable
private fun TownMapPage(s: EmuStatus, onWalk: (Int, Int) -> Unit) {
    if (s.mmTiles == null || s.mmW <= 0 || s.mmH <= 0) {
        PlaceholderPage("地图", "等待地图数据…")
        return
    }
    Column(Modifier.fillMaxSize()) {
        Box(Modifier.fillMaxWidth().weight(1f).background(Color(0xFF14200F), RoundedCornerShape(12.dp))) {
            androidx.compose.foundation.Canvas(
                Modifier.fillMaxSize().padding(6.dp)
                    .pointerInput(s.mmW, s.mmH) {
                        detectTapGestures { off ->
                            if (s.mmW <= 0 || s.mmH <= 0) return@detectTapGestures
                            val tx = (off.x / size.width * s.mmW).toInt().coerceIn(0, s.mmW - 1)
                            val ty = (off.y / size.height * s.mmH).toInt().coerceIn(0, s.mmH - 1)
                            onWalk(tx, ty)
                        }
                    }
            ) {
                val w = s.mmW
                val h = s.mmH
                val cw = size.width / w
                val ch = size.height / h
                val tiles = s.mmTiles
                for (y in 0 until h) for (x in 0 until w) {
                    val pass = tiles?.getOrNull(y)?.getOrNull(x) == 1
                    drawRect(
                        color = if (pass) Color(0xFF2E4B2A) else Color(0xFF0D0D0D),
                        topLeft = Offset(x * cw, y * ch),
                        size = Size(cw - 0.5f, ch - 0.5f),
                    )
                }
                // 玩家位置（tile 坐标，和状态里一致）
                drawCircle(
                    color = Color(0xFFFF4040),
                    radius = minOf(cw, ch) * 0.45f,
                    center = Offset((s.mmPx + 0.5f) * cw, (s.mmPy + 0.5f) * ch),
                )
            }
        }
        Text("点格子前往（会真按方向键移动角色）", color = DIM, fontSize = 10.sp,
            modifier = Modifier.padding(top = 4.dp))
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
            for (pp in pads) {
                val dx = px - pp.cx
                val dy = py - pp.cy
                if (dx * dx + dy * dy <= pp.r * pp.r) return pp.mask
            }
            return 0
        }
        when (action) {
            android.view.MotionEvent.ACTION_DOWN, android.view.MotionEvent.ACTION_POINTER_DOWN -> {
                val i = ev.actionIndex
                val m = hit(i)
                if (m != 0) pointerMasks[ev.getPointerId(i)] = m
            }
            android.view.MotionEvent.ACTION_MOVE -> for (i in 0 until ev.pointerCount) {
                val id = ev.getPointerId(i)
                val m = hit(i)
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
        Column(Modifier.fillMaxSize()) {
            // 顶部：L / R
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                PadLabel("L", EmuCore.KEY_L, pads, 44.dp, (keys and EmuCore.KEY_L) != 0)
                PadLabel("R", EmuCore.KEY_R, pads, 44.dp, (keys and EmuCore.KEY_R) != 0)
            }
            // 中部：方向键 + A/B
            Row(Modifier.weight(1f).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    PadLabel("▲", EmuCore.KEY_UP, pads, pressed = (keys and EmuCore.KEY_UP) != 0)
                    Row {
                        PadLabel("◀", EmuCore.KEY_LEFT, pads, pressed = (keys and EmuCore.KEY_LEFT) != 0)
                        Spacer(Modifier.width(18.dp))
                        PadLabel("▶", EmuCore.KEY_RIGHT, pads, pressed = (keys and EmuCore.KEY_RIGHT) != 0)
                    }
                    PadLabel("▼", EmuCore.KEY_DOWN, pads, pressed = (keys and EmuCore.KEY_DOWN) != 0)
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        PadLabel("B", EmuCore.KEY_B, pads, 52.dp, (keys and EmuCore.KEY_B) != 0)
                        Spacer(Modifier.width(8.dp))
                        Column {
                            PadLabel("A", EmuCore.KEY_A, pads, 52.dp, (keys and EmuCore.KEY_A) != 0)
                            Spacer(Modifier.height(4.dp))
                        }
                    }
                }
            }
            // 底部：Select / Start
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically) {
                PadLabel("SE", EmuCore.KEY_SELECT, pads, 40.dp, (keys and EmuCore.KEY_SELECT) != 0)
                Spacer(Modifier.width(20.dp))
                PadLabel("ST", EmuCore.KEY_START, pads, 40.dp, (keys and EmuCore.KEY_START) != 0)
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
    val latest = activity.updateLatest.value
    val error = activity.updateError.value
    val progress = activity.downloadProgress.value
    val bodyScroll = rememberScrollState()
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
                checking = true
                activity.updateError.value = ""
                Thread {
                    val r = Updater.latest()
                    activity.runOnUiThread {
                        checking = false
                        if (r == null) activity.updateError.value = "检查失败（网络或没有 release）"
                        else activity.updateLatest.value = r
                    }
                }.start()
            }.padding(horizontal = 18.dp, vertical = 8.dp)) {
            Text(if (checking) "检查中…" else "检查更新", color = Color.White, fontSize = 12.sp)
        }
        if (error.isNotBlank()) Text(error, color = Color(0xFFFF8080), fontSize = 11.sp)
        latest?.let { r ->
            Spacer(Modifier.height(8.dp))
            Text("最新: ${r.tag}", color = TXT, fontSize = 12.sp)
            // 更新说明：保留换行，最多显示约 8 行高度，超出可滚动（别整段压成一行）
            Box(Modifier.fillMaxWidth().heightIn(max = 128.dp).verticalScroll(bodyScroll)) {
                Text(r.body, color = DIM, fontSize = 11.sp, modifier = Modifier.fillMaxWidth())
            }
            Spacer(Modifier.height(6.dp))
            Box(Modifier.background(if (progress >= 0) CARD else ACCENT, RoundedCornerShape(10.dp)).clickable {
                if (activity.downloadProgress.value >= 0) return@clickable
                activity.downloadProgress.value = 0
                Thread {
                    val f = File(activity.cacheDir, "update.apk")
                    val ok = Updater.download(r.url, f) { pct ->
                        activity.runOnUiThread { activity.downloadProgress.value = pct }
                    }
                    activity.runOnUiThread {
                        activity.downloadProgress.value = -1
                        if (ok) {
                            if (!Updater.install(activity, f)) {
                                if (!Updater.canInstall(activity)) {
                                    activity.statusText.value = "请在设置里允许「安装未知应用」后重试"
                                } else {
                                    activity.statusText.value = "安装失败，详见 ota.log"
                                }
                            }
                        } else {
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
private fun BattlePage(s: EmuStatus) {
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
    var detail by remember { mutableStateOf<TeamMon?>(null) }
    if (detail != null) {
        val m = detail!!
        Column(Modifier.fillMaxSize()) {
            Text(m.name, color = TXT, fontSize = 16.sp)
            Spacer(Modifier.height(6.dp))
            Text(if (m.types.isEmpty()) "属性 --" else "属性 ${m.types.joinToString(" / ")}", color = TXT, fontSize = 13.sp)
            Text("等级 ${m.lv}", color = TXT, fontSize = 13.sp)
            Text("HP ${m.hp}/${m.max}", color = TXT, fontSize = 13.sp)
            androidx.compose.material3.LinearProgressIndicator(
                progress = { if (m.max > 0) m.hp.toFloat() / m.max else 0f },
                modifier = Modifier.fillMaxWidth().height(6.dp), color = GREEN)
            // 经验进度：满级单独显示；阈值数据不够（未知物种/ROM 没读到）显示 --，不崩
            if (m.expMax) {
                Text(if (m.exp >= 0) "经验 ${m.exp}（已满级）" else "已满级", color = TXT, fontSize = 12.sp)
                androidx.compose.material3.LinearProgressIndicator(
                    progress = { 1f },
                    modifier = Modifier.fillMaxWidth().height(6.dp), color = Color(0xFF6FA8FF))
            } else if (m.exp >= 0 && m.expCur >= 0 && m.expNext > m.expCur) {
                val remain = (m.expNext - m.exp).coerceAtLeast(0)
                Text("经验 ${m.exp} / ${m.expNext}（还差 $remain 升级）", color = TXT, fontSize = 12.sp)
                androidx.compose.material3.LinearProgressIndicator(
                    progress = {
                        ((m.exp - m.expCur).toFloat() / (m.expNext - m.expCur)).coerceIn(0f, 1f)
                    },
                    modifier = Modifier.fillMaxWidth().height(6.dp), color = Color(0xFF6FA8FF))
            } else {
                Text(if (m.exp >= 0) "经验 ${m.exp}（升级阈值 --）" else "经验 --", color = TXT, fontSize = 12.sp)
            }
            Spacer(Modifier.height(8.dp))
            Text("招式", color = DIM, fontSize = 11.sp)
            for (i in 0 until 4) {
                val mv = m.moves.getOrNull(i)
                val name = mv?.name?.takeIf { it.isNotEmpty() } ?: "--"
                val ppText = if (mv != null && mv.pp >= 0) mv.pp.toString() else "--"
                val maxText = mv?.maxPp?.toString() ?: "--"
                val color = if (mv != null && mv.pp == 0) Color(0xFFFF6060) else TXT
                Text("${i + 1}. $name   PP $ppText/$maxText", color = color, fontSize = 12.sp)
            }
            Spacer(Modifier.weight(1f))
            BarButton("返回", true) { detail = null }
        }
        return
    }
    Column(Modifier.fillMaxSize()) {
        if (s.team.isEmpty()) {
            PlaceholderPage("队伍", "等待推送（或还没拿到宝可梦）")
        } else {
            for (m in s.team) {
                Row(Modifier.fillMaxWidth().padding(vertical = 3.dp).clickable { detail = m },
                    verticalAlignment = Alignment.CenterVertically) {
                    Text(m.name, color = TXT, fontSize = 13.sp, modifier = Modifier.weight(1f))
                    Text("Lv${m.lv}", color = DIM, fontSize = 11.sp, modifier = Modifier.width(42.dp))
                    Text("${m.hp}/${m.max}", color = if (m.max > 0 && m.hp * 3 < m.max) Color(0xFFFF6060) else TXT, fontSize = 11.sp)
                }
                androidx.compose.material3.LinearProgressIndicator(
                    progress = { if (m.max > 0) m.hp.toFloat() / m.max else 0f },
                    modifier = Modifier.fillMaxWidth().height(4.dp), color = GREEN)
            }
            Text("点名字看详情", color = DIM, fontSize = 10.sp)
        }
    }
}

@Composable
private fun SavePage(activity: MainActivity, romReady: Boolean) {
    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Box(Modifier.fillMaxWidth().weight(1f).background(CARD, RoundedCornerShape(10.dp)).clickable {
            if (romReady) activity.statusText.value =
                if (EmuCore.saveState(File(activity.filesDir, "state1.sav").absolutePath)) "已存档" else "存档失败"
        }, contentAlignment = Alignment.Center) { Text("即时存档", color = TXT, fontSize = 14.sp) }
        Box(Modifier.fillMaxWidth().weight(1f).background(CARD, RoundedCornerShape(10.dp)).clickable {
            if (romReady) activity.statusText.value =
                if (EmuCore.loadState(File(activity.filesDir, "state1.sav").absolutePath)) "已读档" else "读档失败"
        }, contentAlignment = Alignment.Center) { Text("读取存档", color = TXT, fontSize = 14.sp) }
    }
}

@Composable
private fun OptionPage(activity: MainActivity, emuView: EmuView, onUpdate: () -> Unit, onRom: () -> Unit) {
    val speed = activity.speedState.value
    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Box(Modifier.fillMaxWidth().weight(1f).background(CARD, RoundedCornerShape(10.dp)).clickable {
            val next = when (activity.speedState.value) { 1 -> 2; 2 -> 4; else -> 1 }
            activity.speedState.value = next
            emuView.speed = next
        }, contentAlignment = Alignment.Center) { Text("速度 ${speed}x", color = TXT, fontSize = 14.sp) }
        Box(Modifier.fillMaxWidth().weight(1f).background(CARD, RoundedCornerShape(10.dp)).clickable {
            onRom()
        }, contentAlignment = Alignment.Center) { Text("载入 ROM", color = TXT, fontSize = 14.sp) }
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
        // 当前地图 tiles：优先 assets/maps，缺图回退模拟器内存（MapData 里打 WARN）
        val mapLayer = com.dsh.emu.game.MapData.current()
        if (mapLayer != null) {
            val mm = org.json.JSONObject()
            mm.put("w", mapLayer.w)
            mm.put("h", mapLayer.h)
            mm.put("px", c?.x ?: 0)
            mm.put("py", c?.y ?: 0)
            val tiles = org.json.JSONArray()
            for (row in mapLayer.tiles) {
                val r = org.json.JSONArray()
                for (v in row) r.put(v)
                tiles.put(r)
            }
            mm.put("tiles", tiles)
            o.put("minimap", mm)
        }
        val team = org.json.JSONArray()
        for (m in party) {
            val t = org.json.JSONObject()
            t.put("name", m.name)
            t.put("lv", m.lv)
            t.put("hp", m.hp)
            t.put("max", m.maxHp)
            val types = org.json.JSONArray()
            for (ty in m.types) types.put(ty)
            t.put("types", types)
            val moves = org.json.JSONArray()
            for (i in m.moves.indices) {
                val mid = m.moves[i]
                val info = com.dsh.emu.game.GameData.moves[mid]
                val mo = org.json.JSONObject()
                mo.put("name", info?.first ?: "")
                mo.put("pp", m.pp.getOrNull(i) ?: -1)
                // 上限 PP 没有数据源（队伍结构里只有当前 PP），不带 max，UI 显示 --
                moves.put(mo)
            }
            t.put("moves", moves)
            t.put("exp", m.exp)
            // 升级进度：成长类型从 ROM BaseStats 读（读不到回退标准表），拿不到就不带这两个字段。
            // 满级没有「下一级阈值」，单独标出来，UI 显示「已满级」。
            if (m.lv >= 100) {
                t.put("expMax", true)
            } else {
                val prog = com.dsh.emu.game.Growth.progress(m.species, m.lv, m.exp)
                if (prog != null) {
                    t.put("expCur", prog.cur)
                    t.put("expNext", prog.next)
                }
            }
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
            val ei = com.dsh.emu.game.GameState.enemyInfo()
            foe.put("lv", ei?.lv ?: 0)
            foe.put("hp", ei?.hp ?: 0)
            foe.put("mhp", ei?.maxHp ?: 0)
            foe.put("species", ei?.species ?: 0)
            detail.put("foe", foe)
            o.put("battle_detail", detail)
        }
        o.toString()
    } catch (e: Throwable) {
        ""
    }
}


/**
 * 「点击前往」的取消代际：closeKeys()（点 Tab / 载入 ROM / 收按键面板）会把 generation +1，
 * 后台线程每走一步都检查代际；不一致就立刻停，不会把剩余步数走完。
 */
private object WalkControl {
    @Volatile
    var generation = 0
}

/** 可中断的 sleep：每 20ms 看一次代际，取消后能尽快停（不用等满 180ms）。 */
private fun interruptibleSleep(ms: Long, myGen: Int): Boolean {
    var left = ms
    while (left > 0) {
        if (myGen != WalkControl.generation) return false
        val chunk = if (left < 20L) left else 20L
        try { Thread.sleep(chunk) } catch (_: InterruptedException) { return false }
        left -= chunk
    }
    return myGen == WalkControl.generation
}

/** 点击小地图走到目标格：BFS 算方向序列，再逐个按键。 */
private fun walkTo(activity: MainActivity, s: EmuStatus, tx: Int, ty: Int) {
    val tiles = s.mmTiles ?: run {
        activity.statusText.value = "没有地图数据"
        return
    }
    val from = com.dsh.emu.game.MapWalker.Point(s.mmPx, s.mmPy)
    val to = com.dsh.emu.game.MapWalker.Point(tx, ty)
    val steps = com.dsh.emu.game.MapWalker.path(tiles, from, to)
    if (steps == null) { activity.statusText.value = "走不到 ($tx,$ty)"; return }
    if (steps.isEmpty()) { activity.statusText.value = "已经在这里"; return }
    activity.statusText.value = "前往 ($tx,$ty)：${steps.size} 步"
    // 新的一次前往会让旧线程失效（代际自增），避免两次点击叠着走
    val myGen = ++WalkControl.generation
    Thread {
        try {
            for (dir in steps) {
                if (myGen != WalkControl.generation) break
                val mask = when (dir) {
                    "UP" -> com.dsh.emu.EmuCore.KEY_UP
                    "DOWN" -> com.dsh.emu.EmuCore.KEY_DOWN
                    "LEFT" -> com.dsh.emu.EmuCore.KEY_LEFT
                    else -> com.dsh.emu.EmuCore.KEY_RIGHT
                }
                com.dsh.emu.EmuCore.setKeys(mask)
                if (!interruptibleSleep(180, myGen)) break
                com.dsh.emu.EmuCore.setKeys(0)
                if (!interruptibleSleep(90, myGen)) break
            }
        } finally {
            // 线程因取消退出时也要清按键，不能留着方向键一直走
            com.dsh.emu.EmuCore.setKeys(0)
        }
    }.start()
}
