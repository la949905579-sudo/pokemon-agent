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
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import com.dsh.emu.ui.*
import org.json.JSONObject
import java.io.File

class MainActivity : ComponentActivity() {
    /** 操作反馈（临时行）：存档失败/空槽/先载入 ROM 等，显示 2.8s 后自动消失。 */
    val statusText = mutableStateOf("")
    /** 常驻状态①（顶部状态栏）：TCP 桥状态，一直显示。 */
    val bridgeState = mutableStateOf("")
    /** 常驻状态②（顶部状态栏）：当前 ROM 名，一直显示。 */
    val romState = mutableStateOf("")
    /** 「地图」Tab 的行走预览（点格子只算路、不执行）；null=没有预览。 */
    val walkPlanState = mutableStateOf<WalkPlan?>(null)
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
        // 启动状态是常驻信息，放 bridgeState；不写 statusText（否则启动会闪一条临时行）
        bridgeState.value = if (ok) "TCP :55401" else "TCP 未启动"
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
        romState.value = if (ok) rom.name.take(24) else "未载入"
        if (!ok) statusText.value = "初始化失败（重试 4 次）"
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

// ---------- 下屏 UI ----------

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
/**
 * 「地图」Tab 的行走预览：起点/终点/tile 方向序列，加上预览时的地图身份
 * （地图数组地址；用于「开始走」前判断是不是已经换图了）。
 */
data class WalkPlan(
    val fromX: Int, val fromY: Int,
    val toX: Int, val toY: Int,
    val steps: List<String>,
    val mapName: String,
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
        // 行走预览也一起清（点 Tab / 载入 ROM / 收面板都算离开地图操作）
        activity.walkPlanState.value = null
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
            // 顶部常驻状态行：桥状态 + ROM 名（两个独立通道，互不覆盖）+ 地图坐标 + 帧率
            val bridgeState = activity.bridgeState.value
            val romState = activity.romState.value
            Text(
                buildString {
                    if (bridgeState.isNotBlank()) append(bridgeState)
                    if (romState.isNotBlank()) {
                        if (bridgeState.isNotBlank()) append("  ·  ")
                        append(romState)
                    }
                    if (bridgeState.isNotBlank() || romState.isNotBlank()) append("    ")
                    append(if (status.map.isNotBlank()) status.map else "—")
                    append("  (").append(status.x).append(", ").append(status.y).append(")")
                    append("   帧 ").append(frame).append("  FPS ").append(fps)
                },
                color = DIM, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                modifier = Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 2.dp),
            )
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
                        tabPage == Page.MAP -> TownMapPage(
                            s = status,
                            preview = activity.walkPlanState.value,
                            mapId = currentMapId(),
                            onPick = { tx, ty -> planWalk(activity, status, tx, ty) },
                            onStart = { startWalk(activity, status) },
                            onCancel = { cancelWalk(activity) },
                        )
                        tabPage == Page.TEAM -> TeamPage(status)
                        tabPage == Page.BAG -> PlaceholderPage("背包", "需要道具列表地址")
                        tabPage == Page.NICK -> PlaceholderPage("名字", "玩家名（需要文本地址）")
                        tabPage == Page.DEX -> PlaceholderPage("图鉴", "需要图鉴内存结构")
                        tabPage == Page.SAVE -> SavePage(activity, romReady)
                        tabPage == Page.OPTION -> OptionPage(activity, emuView, onUpdate = { tabPage = Page.UPDATE },
                            onRom = { activity.refreshRoms(); showRoms = true })
                        tabPage == Page.UPDATE -> UpdatePage(activity)
                        // 没手动开 Tab：常驻页自动切换（战斗中战斗页 / 否则整张城镇图）
                        else -> if (inBattle) BattlePage(status) else TownMapPage(
                            s = status,
                            preview = activity.walkPlanState.value,
                            mapId = currentMapId(),
                            onPick = { tx, ty -> planWalk(activity, status, tx, ty) },
                            onStart = { startWalk(activity, status) },
                            onCancel = { cancelWalk(activity) },
                        )
                    }
                }
                Column(Modifier.width(80.dp).fillMaxHeight().padding(start = 4.dp)) {
                    val tabs = listOf(
                        "地图" to Page.MAP, "队伍" to Page.TEAM, "背包" to Page.BAG,
                        "名字" to Page.NICK, "图鉴" to Page.DEX,
                        "存档" to Page.SAVE, "设置" to Page.OPTION,
                    )
                    for ((label, p2) in tabs) {
                        // 「地图」Tab 暂置灰不可点（常驻页已经是整张城镇图，以后重做）
                        val enabled = isPageTabEnabled(p2)
                        // 设置页里的「更新」子页也算设置 Tab 处于打开状态
                        val active = enabled && (tabPage == p2 ||
                            (p2 == Page.OPTION && tabPage == Page.UPDATE))
                        TabButton(label, active, Modifier.weight(1f), enabled = enabled) {
                            if (!enabled) return@TabButton   // 不可点的 Tab 点了没反应
                            showRoms = false
                            closeKeys()
                            // 再点同一个 Tab = 关闭，回到常驻页；点别的 Tab = 直接切换
                            val next = if (tabPage == p2) null else p2
                            tabPage = next
                            // 离开「地图」Tab 就清掉行走预览（路线已经不再显示）
                            if (next != Page.MAP) activity.walkPlanState.value = null
                        }
                    }
                }
            }
            // 临时状态行：存档/读档失败、空槽、先载入 ROM 这类提示只写进 statusText，
            // 之前没有地方渲染（写了等于没写）；这里显示 ~2.8 秒后自动清空。
            val statusMsg = activity.statusText.value
            LaunchedEffect(statusMsg) {
                if (statusMsg.isNotBlank()) {
                    kotlinx.coroutines.delay(2800)
                    // 期间没有更新成别的提示才清空；同一句话重复写不会重新计时
                    if (activity.statusText.value == statusMsg) activity.statusText.value = ""
                }
            }
            if (statusMsg.isNotBlank()) {
                Box(
                    Modifier.fillMaxWidth().height(18.dp).padding(horizontal = 8.dp),
                    contentAlignment = Alignment.CenterStart,
                ) {
                    Text(statusMsg, color = DIM, fontSize = 11.sp, maxLines = 1,
                        overflow = TextOverflow.Ellipsis)
                }
            }
            // 常驻折叠条：任何页面（包括战斗中）都能打开按键面板
            KeyBar(keysOpen) {
                if (keysOpen) {
                    closeKeys()
                } else {
                    WalkControl.generation++   // 打开面板也算离开地图操作，先停掉正在走的路线
                    activity.walkPlanState.value = null   // 路线预览也要清掉
                    keysOpen = true
                }
            }
        }
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
internal object WalkControl {
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

/** 当前地图身份（地图数组地址）；读不到返回 "?"，用于判断预览后是否换图。 */
private fun currentMapId(): String {
    val addr = com.dsh.emu.game.MapData.currentMapAddr()
    return if (addr == 0) "?" else "0x%x".format(addr)
}

/** 「地图」Tab 点格子：只算路径存预览，不执行移动。 */
private fun planWalk(activity: MainActivity, s: EmuStatus, tx: Int, ty: Int) {
    val tiles = s.mmTiles ?: run {
        activity.walkPlanState.value = null
        activity.statusText.value = "没有地图数据"
        return
    }
    val from = com.dsh.emu.game.MapWalker.Point(s.mmPx, s.mmPy)
    val to = com.dsh.emu.game.MapWalker.Point(tx, ty)
    val steps = com.dsh.emu.game.MapWalker.path(tiles, from, to)
    if (steps == null) {
        activity.walkPlanState.value = null
        activity.statusText.value = "走不到这里"
        return
    }
    if (steps.isEmpty()) {
        activity.walkPlanState.value = null
        activity.statusText.value = "已经在这里"
        return
    }
    activity.walkPlanState.value = WalkPlan(s.mmPx, s.mmPy, tx, ty, steps, currentMapId())
}

/** 「开始走」：校验地图没换，再复用 walkTo 真按方向键；先清预览。 */
private fun startWalk(activity: MainActivity, s: EmuStatus) {
    val plan = activity.walkPlanState.value ?: return
    val mapId = currentMapId()
    if (mapId == "?" || plan.mapName == "?") {
        // 地图身份都读不到时不能放行（"?" == "?" 会误判成没换图）
        activity.walkPlanState.value = null
        activity.statusText.value = "等地图数据"
        return
    }
    if (s.mmTiles == null) {
        activity.walkPlanState.value = null
        activity.statusText.value = "没有地图数据"
        return
    }
    if (plan.mapName != mapId) {
        activity.walkPlanState.value = null
        activity.statusText.value = "需要换图，暂不支持"
        return
    }
    activity.walkPlanState.value = null
    walkTo(activity, s, plan.toX, plan.toY)
}

/** 取消预览：清状态，并让可能在走的路线立刻停（代际 +1）。 */
private fun cancelWalk(activity: MainActivity) {
    activity.walkPlanState.value = null
    WalkControl.generation++
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
