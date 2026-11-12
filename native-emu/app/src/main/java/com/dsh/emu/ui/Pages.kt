package com.dsh.emu.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dsh.emu.BuildConfig
import com.dsh.emu.EmuCore
import com.dsh.emu.EmuView
import com.dsh.emu.MainActivity
import com.dsh.emu.TeamMon
import com.dsh.emu.Updater
import java.io.File
import com.dsh.emu.EmuStatus

@Composable
internal fun BarButton(label: String, active: Boolean, onClick: () -> Unit) {
    Text(label, color = if (active) Color.White else DIM, fontSize = 12.sp,
        modifier = Modifier.clickable { onClick() }
            .background(if (active) ACCENT else CARD, RoundedCornerShape(8.dp))
            .padding(horizontal = 22.dp, vertical = 6.dp))
}

@Composable
internal fun UpdatePage(activity: MainActivity) {
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
internal fun PlaceholderPage(title: String, hint: String) {
    Box(Modifier.fillMaxSize().background(CARD, RoundedCornerShape(10.dp)), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(title, color = TXT, fontSize = 14.sp)
            Text(hint, color = DIM, fontSize = 11.sp)
        }
    }
}

@Composable
internal fun TeamPage(s: EmuStatus) {
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

/** 「存档」页：3 个卡槽，每槽「存档 / 读取 / 删除」；三个破坏性操作都要 3 秒内二次确认。 */
@Composable
internal fun SavePage(activity: MainActivity, romReady: Boolean) {
    // 同一时刻只允许一个确认态：(操作, 槽位)
    var confirming by remember { mutableStateOf<Pair<SlotAction, Int>?>(null) }
    var refresh by remember { mutableStateOf(0) }
    // 3 秒内没再点就自动复原
    LaunchedEffect(confirming) {
        if (confirming != null) {
            kotlinx.coroutines.delay(3000)
            confirming = null
        }
    }
    val labels = remember(refresh) {
        (1..SaveSlots.COUNT).map { SaveSlots.label(activity.filesDir, it) }
    }

    fun save(slot: Int) {
        if (!romReady) { activity.statusText.value = "先载入 ROM 再存档"; return }
        val ok = EmuCore.saveState(SaveSlots.file(activity.filesDir, slot).absolutePath)
        activity.statusText.value = if (ok) "槽 $slot 已存档" else "槽 $slot 存档失败"
        refresh++
    }

    fun load(slot: Int) {
        if (!romReady) { activity.statusText.value = "先载入 ROM 再读档"; return }
        if (!SaveSlots.exists(activity.filesDir, slot)) {
            activity.statusText.value = "槽 $slot 是空槽"
            return
        }
        val ok = EmuCore.loadState(SaveSlots.file(activity.filesDir, slot).absolutePath)
        activity.statusText.value = if (ok) "槽 $slot 已读档" else "槽 $slot 读档失败"
        refresh++
    }

    fun delete(slot: Int) {
        val f = SaveSlots.file(activity.filesDir, slot)
        if (!f.isFile) {
            activity.statusText.value = "槽 $slot 本来就是空的"
            return
        }
        val ok = try { f.delete() } catch (_: Throwable) { false }
        activity.statusText.value = if (ok) "槽 $slot 已删除" else "槽 $slot 删除失败"
        refresh++
    }

    /** 三个按钮走同一个入口：该确认的进确认态，确认过的执行。 */
    fun onAction(action: SlotAction, slot: Int, hasSave: Boolean, run: () -> Unit) {
        if (SlotConfirm.shouldRunNow(action, slot, confirming, hasSave)) {
            confirming = null
            run()
        } else {
            confirming = action to slot
        }
    }

    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        for (slot in 1..SaveSlots.COUNT) {
            val hasSave = SaveSlots.exists(activity.filesDir, slot)
            val confirmingSave = confirming == (SlotAction.SAVE to slot)
            val confirmingLoad = confirming == (SlotAction.LOAD to slot)
            val confirmingDelete = confirming == (SlotAction.DELETE to slot)
            Column(Modifier.fillMaxWidth().weight(1f).background(CARD, RoundedCornerShape(10.dp)).padding(8.dp)) {
                Text(labels[slot - 1], color = if (hasSave) TXT else DIM, fontSize = 13.sp)
                Spacer(Modifier.weight(1f))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    SlotButton(if (confirmingSave) "确认覆盖？" else "存档", confirmingSave) {
                        onAction(SlotAction.SAVE, slot, hasSave) { save(slot) }
                    }
                    SlotButton(if (confirmingLoad) "确认读取？" else "读取", confirmingLoad) {
                        onAction(SlotAction.LOAD, slot, hasSave) { load(slot) }
                    }
                    SlotButton(if (confirmingDelete) "确认删除？" else "删除", confirmingDelete) {
                        onAction(SlotAction.DELETE, slot, hasSave) { delete(slot) }
                    }
                }
            }
        }
    }
}

/** 卡槽里的小按钮（不用系统对话框，保持轻量）。 */
@Composable
private fun SlotButton(label: String, danger: Boolean, onClick: () -> Unit) {
    Text(label,
        color = if (danger) Color.White else TXT,
        fontSize = 12.sp,
        modifier = Modifier.background(
            if (danger) Color(0xFFB4453C) else Color(0xFF3A3A3A), RoundedCornerShape(8.dp))
            .clickable { onClick() }
            .padding(horizontal = 10.dp, vertical = 5.dp))
}

@Composable
internal fun OptionPage(activity: MainActivity, emuView: EmuView, onUpdate: () -> Unit, onRom: () -> Unit) {
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
        // 重置 / 退出：样式沿用 BarButton
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
            BarButton("重置", active = false) {
                val romReady = activity.romReadyState.value
                val ok = romReady && EmuCore.resetGame()
                activity.statusText.value = ActionHints.reset(romReady, ok)
            }
            Spacer(Modifier.width(10.dp))
            BarButton("退出", active = false) {
                exitApp(activity, emuView)
            }
        }
    }
}

/**
 * 完全退出：先把电池存档刷盘，再停服务、结束 Activity、杀进程。
 * 顺序不能反——先 stop() 走 core deinit，mGBA 在 savedata unmap 时 msync 写回 .sav；
 * 直接杀进程的话，游戏内存档可能还在页缓存里丢一部分。
 */
private fun exitApp(activity: MainActivity, emuView: EmuView) {
    // 1) 刷盘：deinit core（含 savedata unmap + msync）
    try { EmuCore.stop() } catch (_: Throwable) {}
    // 2) 停渲染线程 / 状态
    try { emuView.stop() } catch (_: Throwable) {}
    activity.romReadyState.value = false
    activity.runningState.value = false
    // 3) 停前台服务
    try {
        activity.stopService(android.content.Intent(activity, com.dsh.emu.EmuService::class.java))
    } catch (_: Throwable) {}
    // 4) 结束 Activity（触发 bridge.stop 等收尾）
    try { activity.finishAffinity() } catch (_: Throwable) {}
    // 5) 杀进程：稍等一点让上面几步跑完
    android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
        android.os.Process.killProcess(android.os.Process.myPid())
    }, 300)
}

/** 设置页操作的提示文案（纯函数，方便单测）。 */
internal object ActionHints {
    fun reset(romReady: Boolean, ok: Boolean): String = when {
        !romReady -> "先载入 ROM"
        ok -> "已重置"
        else -> "重置失败"
    }
}
