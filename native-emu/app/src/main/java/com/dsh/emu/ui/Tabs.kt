package com.dsh.emu.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

internal enum class Page { MAP, TEAM, BAG, NICK, DEX, SAVE, OPTION, BATTLE, UPDATE }

/** 右侧 Tab 是否可点（「地图」Tab 暂置灰，以后重做）。纯函数方便单测。 */
internal fun isPageTabEnabled(page: Page): Boolean = page != Page.MAP

@Composable
internal fun TabButton(
    label: String,
    active: Boolean,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    onClick: () -> Unit,
) {
    // 不可点时：保持 CARD 背景与布局高度，只挂更暗的文字色，且不挂 clickable
    var boxModifier = modifier.fillMaxWidth().padding(vertical = 2.dp)
        .background(if (active && enabled) ACCENT else CARD, RoundedCornerShape(8.dp))
    if (enabled) boxModifier = boxModifier.clickable { onClick() }
    val textColor = if (!enabled) Color(0xFF555555) else if (active) Color.White else DIM
    Box(boxModifier, contentAlignment = Alignment.Center) {
        Text(label, color = textColor, fontSize = 11.sp)
    }
}
