package com.dsh.emu.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dsh.emu.EmuStatus
import androidx.compose.foundation.background
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.Alignment

@Composable
internal fun BattlePage(s: EmuStatus) {
    Column(Modifier.fillMaxSize().padding(4.dp)) {
        // 敌方
        Text("敌方  Lv${s.foeLv}   ${s.foeHp}/${s.foeMax}", color = Color(0xFFFF9090), fontSize = 12.sp)
        androidx.compose.material3.LinearProgressIndicator(
            progress = { if (s.foeMax > 0) s.foeHp.toFloat() / s.foeMax else 0f },
            modifier = Modifier.fillMaxWidth().height(6.dp), color = Color(0xFFFF6060))
        Spacer(Modifier.height(6.dp))
        // 我方
        Text("我方  Lv${s.meLv}   ${s.meHp}/${s.meMax}", color = TXT, fontSize = 12.sp)
        androidx.compose.material3.LinearProgressIndicator(
            progress = { if (s.meMax > 0) s.meHp.toFloat() / s.meMax else 0f },
            modifier = Modifier.fillMaxWidth().height(6.dp), color = GREEN)
        Spacer(Modifier.height(8.dp))
        // 4 招式（只显示，不点，避免误操作）
        Column(Modifier.weight(1f).fillMaxWidth()) {
            for (row in listOf(0, 1)) {
                Row(Modifier.weight(1f)) {
                    for (col in 0..1) {
                        val idx = row * 2 + col
                        val mv = s.moves.getOrNull(idx).orEmpty()
                        Box(Modifier.weight(1f).fillMaxHeight().padding(4.dp)
                            .background(CARD, RoundedCornerShape(10.dp)),
                            contentAlignment = Alignment.Center) {
                            Text(if (mv.isNotEmpty()) mv else "—", color = if (mv.isNotEmpty()) TXT else DIM, fontSize = 13.sp)
                        }
                    }
                }
            }
        }
    }
}
