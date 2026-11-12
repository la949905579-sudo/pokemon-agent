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

@Composable
internal fun TabButton(label: String, active: Boolean, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Box(
        modifier.fillMaxWidth().padding(vertical = 2.dp)
            .background(if (active) ACCENT else CARD, RoundedCornerShape(8.dp))
            .clickable { onClick() },
        contentAlignment = Alignment.Center
    ) {
        Text(label, color = if (active) Color.White else DIM, fontSize = 11.sp)
    }
}
