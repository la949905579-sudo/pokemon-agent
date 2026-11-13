package com.dsh.emu

import android.os.Bundle
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
import java.io.File

/**
 * 应用入口与组合根：只留 Activity 生命周期、状态容器与 [AppScreen] 组合根。
 *
 * 具体 UI 块在 `ui/` 下拆开：
 * - `ui/EmuView.kt` 上屏渲染视图；
 * - `ui/StatusParser.kt` 状态 JSON 解析 + 数据模型；
 * - `ui/LocalStatus.kt` 本地内存状态 → JSON；
 * - `ui/WalkControl.kt` 「点击前往」代际取消与行走；
 * - `ui/Pages.kt` 等各页面/Tab。
 * 行为等价迁移（批次4），未改 UI 文案/布局语义/按键掩码/地址。
 */
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

// ---------- 下屏 UI ----------

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
        // 同时取消正在进行的「点击招式施放」（战斗里切页/收面板/载 ROM 都走这里）
        BattleMoveAction.cancel()
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
                        else -> if (inBattle) BattlePage(status, onCastMove = { idx ->
                            BattleMoveAction.cast(activity, idx)
                        }) else TownMapPage(
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
