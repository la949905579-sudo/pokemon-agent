package com.dsh.emu.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dsh.emu.game.CrossMapRoute
import com.dsh.emu.game.MapData
import com.dsh.emu.game.MapLinks
import com.dsh.emu.game.Terrain

/** 地图配色：挡 / 可走 / 水 / 高草 / 台阶（地形分类见 [Terrain]）。 */
private val BLOCKED_COLOR = Color(0xFF0D0D0D)
private val WALK_COLOR = Color(0xFF2E4B2A)
private val WATER_COLOR = Color(0xFF2A5C8A)
private val GRASS_COLOR = Color(0xFF3E7A33)
private val STAIRS_COLOR = Color(0xFF8C7A3A)

private fun terrainColor(cat: Int): Color = when (cat) {
    Terrain.WATER -> WATER_COLOR
    Terrain.GRASS -> GRASS_COLOR
    Terrain.STAIRS -> STAIRS_COLOR
    Terrain.WALK -> WALK_COLOR
    else -> BLOCKED_COLOR
}

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
                val cat = s.mmTerrain?.getOrNull(y0 + vy)?.getOrNull(x0 + vx)
                val pass = tiles.getOrNull(y0 + vy)?.getOrNull(x0 + vx) == 1
                drawRect(
                    color = if (cat != null) terrainColor(cat) else if (pass) WALK_COLOR else BLOCKED_COLOR,
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
 * 「地图」Tab：当前所在城镇/道路的整张 tile 地图。
 * 点格子只「预览」路线（黄线 + 终点标记 + N 步），要按「开始走」才真按方向键。
 * 底部还有「跨图」入口：列出相邻地图，点一个后台 A* 规划跨图路线，预览后再走。
 * 与常驻的 CurrentMapPage（以玩家为中心的只读视口）是两个独立组件，别复用。
 */
@Composable
internal fun TownMapPage(
    s: EmuStatus,
    preview: WalkPlan?,
    mapId: String,
    mapAddr: Int,
    crossPlan: CrossPlan?,
    onPick: (Int, Int) -> Unit,
    onStart: () -> Unit,
    onCancel: () -> Unit,
    onCrossPick: (CrossMapRoute.Destination) -> Unit,
    onCrossStart: () -> Unit,
    onCrossCancel: () -> Unit,
) {
    if (s.mmTiles == null || s.mmW <= 0 || s.mmH <= 0) {
        PlaceholderPage("地图", "等待地图数据…")
        return
    }
    // 相邻地图（map_links 按目标去重；地图 id 取 assets 的 maps 字段显示成友好名）
    val crossTargets = remember(mapId, mapAddr) {
        if (mapAddr == 0) emptyList() else CrossMapRoute.destinations(
            mapAddr,
            MapLinks.all(),
            mapIds = { addr -> MapData.assetLayer(addr)?.maps ?: emptyList() },
        )
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
                            onPick(tx, ty)
                        }
                    }
            ) {
                val w = s.mmW
                val h = s.mmH
                val cw = size.width / w
                val ch = size.height / h
                val tiles = s.mmTiles
                for (y in 0 until h) for (x in 0 until w) {
                    val cat = s.mmTerrain?.getOrNull(y)?.getOrNull(x)
                    drawRect(
                        color = when {
                            cat != null -> terrainColor(cat)
                            tiles?.getOrNull(y)?.getOrNull(x) == 1 -> WALK_COLOR
                            else -> BLOCKED_COLOR
                        },
                        topLeft = Offset(x * cw, y * ch),
                        size = Size(cw - 0.5f, ch - 0.5f),
                    )
                }
                // 行走预览：黄线逐段连 + 终点标记（只是预览，不执行移动）。
                // 换图后旧预览不预渲染：地图身份不一致就不画（预览状态保留，点开始走仍会提示换图）
                if (preview != null && preview.mapName == mapId) {
                    val pts = previewPoints(preview.fromX, preview.fromY, preview.steps)
                    for (i in 0 until pts.size - 1) {
                        val a = pts[i]
                        val b = pts[i + 1]
                        drawLine(
                            color = Color(0xFFFFD54F),
                            start = Offset((a.first + 0.5f) * cw, (a.second + 0.5f) * ch),
                            end = Offset((b.first + 0.5f) * cw, (b.second + 0.5f) * ch),
                            strokeWidth = 3f,
                        )
                    }
                    val end = pts.last()
                    drawCircle(
                        color = Color(0xFFFFD54F),
                        radius = minOf(cw, ch) * 0.4f,
                        center = Offset((end.first + 0.5f) * cw, (end.second + 0.5f) * ch),
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
        // 当前地图遭遇（一行，横向滚动；没有数据不占位）
        if (s.encounters.isNotBlank()) {
            Text(s.encounters, color = Color(0xFFB7D8A8), fontSize = 10.sp, maxLines = 1,
                softWrap = false,
                modifier = Modifier.fillMaxWidth().padding(top = 3.dp).horizontalScroll(rememberScrollState()))
        }
        when {
            // 跨图预览：去 X · N 段 M 步 → 开始走 / 取消
            crossPlan != null -> Row(
                Modifier.fillMaxWidth().padding(top = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("去 ${crossPlan.targetLabel} · ${crossPlan.plan.legs.size} 段 ${crossPlan.plan.totalSteps} 步",
                    color = Color(0xFF9AD0FF), fontSize = 11.sp, maxLines = 1,
                    modifier = Modifier.weight(1f))
                BarButton("开始走", active = true) { onCrossStart() }
                BarButton("取消", active = false) { onCrossCancel() }
            }
            preview != null -> Row(
                Modifier.fillMaxWidth().padding(top = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("${preview.steps.size} 步", color = Color(0xFFFFD54F), fontSize = 12.sp)
                BarButton("开始走", active = true, modifier = Modifier.weight(1f)) { onStart() }
                BarButton("取消", active = false, modifier = Modifier.weight(1f)) { onCancel() }
            }
            else -> Column(Modifier.fillMaxWidth().padding(top = 3.dp)) {
                if (crossTargets.isNotEmpty()) {
                    Row(
                        Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text("跨图 →", color = DIM, fontSize = 10.sp)
                        for (d in crossTargets) {
                            Text(d.label, color = Color(0xFF9AD0FF), fontSize = 10.sp,
                                modifier = Modifier
                                    .clickable { onCrossPick(d) }
                                    .background(CARD, RoundedCornerShape(6.dp))
                                    .padding(horizontal = 8.dp, vertical = 3.dp))
                        }
                    }
                } else {
                    Text("无相邻地图连接", color = DIM, fontSize = 10.sp)
                }
                Text("点格子预览路线（不会立刻走）", color = DIM, fontSize = 10.sp,
                    modifier = Modifier.padding(top = 2.dp))
            }
        }
    }
}
