package com.dsh.emu

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView

/**
 * P0 双屏骨架：
 *   上屏：SurfaceView（后续接 mGBA 帧缓冲）
 *   下屏：状态面板占位（P1 接自动化数据）
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { AppScreen() }
    }
}

@Composable
fun AppScreen() {
    var frame by remember { mutableStateOf(0L) }
    var fps by remember { mutableStateOf(0) }
    var running by remember { mutableStateOf(false) }

    // 简易帧驱动（P0-3 之前先用计数器验证渲染链路）
    LaunchedEffect(running) {
        if (!running) return@LaunchedEffect
        var last = System.currentTimeMillis()
        var cnt = 0
        while (true) {
            EmuCore.runFrame()
            frame = EmuCore.frameCount()
            cnt++
            val now = System.currentTimeMillis()
            if (now - last >= 1000) { fps = cnt; cnt = 0; last = now }
            kotlinx.coroutines.delay(16)
        }
    }

    Column(Modifier.fillMaxSize().background(Color(0xFF101010))) {
        // 上屏：游戏
        Box(
            Modifier.weight(2f).fillMaxWidth().background(Color.Black),
            contentAlignment = Alignment.Center
        ) {
            AndroidView(factory = { ctx ->
                android.view.SurfaceView(ctx)
            }, modifier = Modifier.fillMaxSize())
            Text("画面区（P0-3 接入 mGBA 帧缓冲）", color = Color(0xFF666666), fontSize = 12.sp)
        }

        // 下屏：状态 / 控制
        Box(
            Modifier.weight(1f).fillMaxWidth().background(Color(0xFF1B1B1B)),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("帧号 $frame   FPS $fps", color = Color.White, fontSize = 14.sp)
                Spacer(Modifier.height(8.dp))
                Row {
                    Button(onClick = { running = !running }) {
                        Text(if (running) "暂停" else "开始")
                    }
                }
                Spacer(Modifier.height(8.dp))
                Text("下屏（P1 接自动化面板）", color = Color(0xFF777777), fontSize = 12.sp)
            }
        }
    }
}
