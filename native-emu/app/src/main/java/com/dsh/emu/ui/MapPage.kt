package com.dsh.emu.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dsh.emu.EmuStatus

/**
 * 常驻「当前地图页」：以玩家为中心、tile 级的只读视口，随移动刷新。
 * 注意：和右侧 Tab 的「大地图」（整张当前地图、可点走）是两个独立组件，不共用。
 */
@Composable
internal fun CurrentMapPage(s: EmuStatus) {
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

/**
 * 「地图」Tab：当前所在城镇/道路的整张 tile 地图，点格子会真按方向键走过去。
 * 与常驻的 CurrentMapPage（以玩家为中心的只读视口）是两个独立组件，别复用。
 */
@Composable
internal fun TownMapPage(s: EmuStatus, onWalk: (Int, Int) -> Unit) {
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
