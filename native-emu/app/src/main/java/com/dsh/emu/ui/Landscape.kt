package com.dsh.emu.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.dsh.emu.EmuCore
import com.dsh.emu.MainActivity

/**
 * 横屏纯游戏画面模式：
 * - 游戏画面整屏铺满（[EmuView]），除一个半透明设置图标外不显示任何 App 控件；
 * - 屏幕点击 = 游戏画面实际位置操作（映射见 [TouchMap] / [Wysiwyg]）；
 * - 设置图标打开半透明覆盖层（速度 / 自动战斗 / 载入 ROM / 更新 / 重置 / 退出）；
 * - 进入横屏时隐藏系统栏，退出横屏恢复。
 *
 * 竖屏完全不走这里（[MainActivity] 的 AppScreen 分支），行为不变。
 */
@Composable
internal fun LandscapeScreen(
    activity: MainActivity,
    emuView: EmuView,
    romReady: Boolean,
    status: EmuStatus,
) {
    var panelOpen by remember { mutableStateOf(false) }
    val viewSize = remember { mutableStateOf(IntSize.Zero) }
    val latestStatus = rememberUpdatedState(status)
    ImmersiveGame(activity)
    // 从竖屏切过来时按键面板会被折起：清掉可能残留的按键掩码（否则角色会一直走）
    LaunchedEffect(Unit) { EmuCore.setKeys(0) }

    // 临时操作提示（fail-closed 提示用）：2.8s 后自动消失，与竖屏同口径。
    val statusMsg = activity.statusText.value
    LaunchedEffect(statusMsg) {
        if (statusMsg.isNotBlank()) {
            kotlinx.coroutines.delay(2800)
            if (activity.statusText.value == statusMsg) activity.statusText.value = ""
        }
    }

    Box(Modifier.fillMaxSize().background(Color.Black)) {
        AndroidView(
            factory = { emuView },
            modifier = Modifier.fillMaxSize().onSizeChanged { viewSize.value = it },
        )
        if (!romReady) {
            Text(
                "点右上 ⚙ 载入 ROM",
                color = DIM, fontSize = 13.sp,
                modifier = Modifier.align(Alignment.Center),
            )
        }

        if (!panelOpen) {
            // 点击层：只负责把屏幕坐标换算成游戏像素后交给 Wysiwyg。
            Box(
                Modifier.fillMaxSize().pointerInput(Unit) {
                    detectTapGestures { off ->
                        val vs = viewSize.value
                        if (vs.width <= 0 || vs.height <= 0) return@detectTapGestures
                        val p = TouchMap.viewToGame(vs.width, vs.height, off.x, off.y)
                            ?: return@detectTapGestures
                        Wysiwyg.onTap(activity, latestStatus.value, p.x.toInt(), p.y.toInt())
                    }
                }
            )
            // 唯一的常显控件：半透明设置图标。
            Box(
                Modifier.align(Alignment.TopEnd).padding(10.dp).size(42.dp)
                    .background(Color.White.copy(alpha = 0.16f), CircleShape)
                    .clickable { panelOpen = true },
                contentAlignment = Alignment.Center,
            ) {
                Text("⚙", color = Color.White.copy(alpha = 0.85f), fontSize = 22.sp)
            }
        }

        // 临时提示（无面板时显示在底部中央；面板自己也会显示一行）
        if (!panelOpen && statusMsg.isNotBlank()) {
            Text(
                statusMsg, color = TXT, fontSize = 12.sp, maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 18.dp)
                    .background(Color(0xB3000000), RoundedCornerShape(8.dp))
                    .padding(horizontal = 12.dp, vertical = 6.dp),
            )
        }

        if (panelOpen) {
            BackHandler { panelOpen = false }
            LandscapePanel(activity, emuView) { panelOpen = false }
        }
    }
}

/** 横屏隐藏系统栏（沉浸）；离开横屏时恢复。 */
@Composable
private fun ImmersiveGame(activity: MainActivity) {
    val owner = LocalLifecycleOwner.current
    DisposableEffect(owner) {
        val controller = WindowCompat.getInsetsController(activity.window, activity.window.decorView)
        fun apply() {
            controller.hide(WindowInsetsCompat.Type.systemBars())
            controller.systemBarsBehavior =
                WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) apply()
        }
        owner.lifecycle.addObserver(observer)
        apply()
        onDispose {
            owner.lifecycle.removeObserver(observer)
            controller.show(WindowInsetsCompat.Type.systemBars())
        }
    }
}

private enum class PanelPage { MENU, ROM, UPDATE }

/** 半透明覆盖层设置面板（横屏）。 */
@Composable
private fun LandscapePanel(activity: MainActivity, emuView: EmuView, onClose: () -> Unit) {
    var page by remember { mutableStateOf(PanelPage.MENU) }
    val roms = activity.romListState.value
    val speed = activity.speedState.value
    val auto = AutoBattle.running.value
    val title = when (page) {
        PanelPage.MENU -> "设置"
        PanelPage.ROM -> "载入 ROM"
        PanelPage.UPDATE -> "更新"
    }
    Box(Modifier.fillMaxSize().background(Color(0x99000000))) {
        Column(
            Modifier.align(Alignment.CenterEnd).padding(12.dp).fillMaxHeight(0.94f)
                .widthIn(min = 240.dp, max = 360.dp)
                .background(Color(0xF21B1B1B), RoundedCornerShape(14.dp)).padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(title, color = TXT, fontSize = 15.sp)
                BarButton("关闭", true) { onClose() }
            }
            when (page) {
                PanelPage.MENU -> {
                    PanelItem("速度 ${speed}x") {
                        val next = when (activity.speedState.value) { 1 -> 2; 2 -> 4; else -> 1 }
                        activity.speedState.value = next
                        emuView.speed = next
                    }
                    PanelItem(if (auto) "自动战斗：开" else "自动战斗：关", active = auto) {
                        AutoBattle.toggle(activity)
                    }
                    PanelItem("载入 ROM") {
                        activity.refreshRoms()
                        page = PanelPage.ROM
                    }
                    PanelItem("更新") { page = PanelPage.UPDATE }
                    PanelItem("重置") {
                        WalkControl.generation++
                        AutoBattle.cancel()
                        activity.walkPlanState.value = null
                        val romReady = activity.romReadyState.value
                        val ok = romReady && EmuCore.resetGame()
                        activity.statusText.value = ActionHints.reset(romReady, ok)
                    }
                    PanelItem("退出") { exitApp(activity, emuView) }
                }
                PanelPage.ROM -> {
                    Text("选择 ROM（${roms.size}）", color = DIM, fontSize = 11.sp)
                    LazyColumn(Modifier.weight(1f).fillMaxWidth()) {
                        items(roms) { f ->
                            Text(
                                f.name, color = Color(0xFF9AD0FF), fontSize = 12.sp,
                                maxLines = 1, overflow = TextOverflow.Ellipsis,
                                modifier = Modifier.fillMaxWidth()
                                    .clickable {
                                        activity.loadRom(f)
                                        onClose()
                                    }
                                    .padding(vertical = 9.dp),
                            )
                        }
                        if (roms.isEmpty()) {
                            item {
                                Text("没找到 ROM（需要「所有文件访问权限」）", color = DIM, fontSize = 11.sp)
                            }
                        }
                    }
                    BarButton("返回", false, Modifier.fillMaxWidth()) { page = PanelPage.MENU }
                }
                PanelPage.UPDATE -> {
                    Box(Modifier.weight(1f).fillMaxWidth()) { UpdatePage(activity) }
                    BarButton("返回", false, Modifier.fillMaxWidth()) { page = PanelPage.MENU }
                }
            }
            val msg = activity.statusText.value
            if (msg.isNotBlank()) {
                Text(msg, color = DIM, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
        }
    }
}

@Composable
private fun PanelItem(label: String, active: Boolean = false, onClick: () -> Unit) {
    Box(
        Modifier.fillMaxWidth().height(40.dp)
            .background(if (active) ACCENT else CARD, RoundedCornerShape(10.dp))
            .clickable { onClick() },
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color = if (active) Color.White else TXT, fontSize = 13.sp)
    }
}
