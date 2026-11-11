package com.dsh.emu

import androidx.compose.runtime.mutableStateOf

/** 外部（Python）推送的界面状态，下屏读取显示。 */
object UiState {
    val statusJson = mutableStateOf("")
    val logs = mutableStateOf<List<String>>(emptyList())

    fun addLog(line: String) {
        val cur = logs.value
        logs.value = (cur + line).takeLast(50)
    }
}
