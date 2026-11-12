package com.dsh.emu.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInteropFilter
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dsh.emu.EmuCore
import androidx.compose.foundation.shape.RoundedCornerShape

private data class PadPos(val mask: Int, val cx: Float, val cy: Float, val r: Float)

@Composable
private fun PadLabel(label: String, mask: Int, pads: MutableList<PadPos>, size: androidx.compose.ui.unit.Dp = 44.dp, pressed: Boolean = false) {
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

@OptIn(androidx.compose.ui.ExperimentalComposeUiApi::class)
@Composable
internal fun KeyPadArea(keys: Int, onChange: (Int) -> Unit) {
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

/** 最底边的按键折叠条：点击开合；展开时向下拖拽也能收起。 */
@Composable
internal fun KeyBar(open: Boolean, onToggle: () -> Unit) {    var dragDown by remember { mutableStateOf(0f) }
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
