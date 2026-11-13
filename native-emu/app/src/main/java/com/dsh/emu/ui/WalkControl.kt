package com.dsh.emu.ui

import com.dsh.emu.MainActivity

/**
 * 「点击前往」的取消代际：closeKeys()（点 Tab / 载入 ROM / 收按键面板）会把 generation +1，
 * 后台线程每走一步都检查代际；不一致就立刻停，不会把剩余步数走完。
 * 从 MainActivity.kt 原样迁出（行为等价，closeKeys 语义不变）。
 */
internal object WalkControl {
    @Volatile
    var generation = 0
}

/** 可中断的 sleep：每 20ms 看一次代际，取消后能尽快停（不用等满 180ms）。 */
internal fun interruptibleSleep(ms: Long, myGen: Int): Boolean {
    var left = ms
    while (left > 0) {
        if (myGen != WalkControl.generation) return false
        val chunk = if (left < 20L) left else 20L
        try { Thread.sleep(chunk) } catch (_: InterruptedException) { return false }
        left -= chunk
    }
    return myGen == WalkControl.generation
}

/** 当前地图身份（地图数组地址）；读不到返回 "?"，用于判断预览后是否换图。 */
internal fun currentMapId(): String {
    val addr = com.dsh.emu.game.MapData.currentMapAddr()
    return if (addr == 0) "?" else "0x%x".format(addr)
}

/** 「地图」Tab 点格子：只算路径存预览，不执行移动。 */
internal fun planWalk(activity: MainActivity, s: EmuStatus, tx: Int, ty: Int) {
    val tiles = s.mmTiles ?: run {
        activity.walkPlanState.value = null
        activity.statusText.value = "没有地图数据"
        return
    }
    val from = com.dsh.emu.game.MapWalker.Point(s.mmPx, s.mmPy)
    val to = com.dsh.emu.game.MapWalker.Point(tx, ty)
    val steps = com.dsh.emu.game.MapWalker.path(tiles, from, to)
    if (steps == null) {
        activity.walkPlanState.value = null
        activity.statusText.value = "走不到这里"
        return
    }
    if (steps.isEmpty()) {
        activity.walkPlanState.value = null
        activity.statusText.value = "已经在这里"
        return
    }
    activity.walkPlanState.value = WalkPlan(s.mmPx, s.mmPy, tx, ty, steps, currentMapId())
}

/** 「开始走」：校验地图没换，再复用 walkTo 真按方向键；先清预览。 */
internal fun startWalk(activity: MainActivity, s: EmuStatus) {
    val plan = activity.walkPlanState.value ?: return
    val mapId = currentMapId()
    if (mapId == "?" || plan.mapName == "?") {
        // 地图身份都读不到时不能放行（"?" == "?" 会误判成没换图）
        activity.walkPlanState.value = null
        activity.statusText.value = "等地图数据"
        return
    }
    if (s.mmTiles == null) {
        activity.walkPlanState.value = null
        activity.statusText.value = "没有地图数据"
        return
    }
    if (plan.mapName != mapId) {
        activity.walkPlanState.value = null
        activity.statusText.value = "需要换图，暂不支持"
        return
    }
    activity.walkPlanState.value = null
    walkTo(activity, s, plan.toX, plan.toY)
}

/** 取消预览：清状态，并让可能在走的路线立刻停（代际 +1）。 */
internal fun cancelWalk(activity: MainActivity) {
    activity.walkPlanState.value = null
    WalkControl.generation++
}

/** 点击小地图走到目标格：BFS 算方向序列，再逐个按键。 */
internal fun walkTo(activity: MainActivity, s: EmuStatus, tx: Int, ty: Int) {
    val tiles = s.mmTiles ?: run {
        activity.statusText.value = "没有地图数据"
        return
    }
    val from = com.dsh.emu.game.MapWalker.Point(s.mmPx, s.mmPy)
    val to = com.dsh.emu.game.MapWalker.Point(tx, ty)
    val steps = com.dsh.emu.game.MapWalker.path(tiles, from, to)
    if (steps == null) { activity.statusText.value = "走不到 ($tx,$ty)"; return }
    if (steps.isEmpty()) { activity.statusText.value = "已经在这里"; return }
    activity.statusText.value = "前往 ($tx,$ty)：${steps.size} 步"
    // 新的一次前往会让旧线程失效（代际自增），避免两次点击叠着走
    val myGen = ++WalkControl.generation
    Thread {
        try {
            for (dir in steps) {
                if (myGen != WalkControl.generation) break
                val mask = when (dir) {
                    "UP" -> com.dsh.emu.EmuCore.KEY_UP
                    "DOWN" -> com.dsh.emu.EmuCore.KEY_DOWN
                    "LEFT" -> com.dsh.emu.EmuCore.KEY_LEFT
                    else -> com.dsh.emu.EmuCore.KEY_RIGHT
                }
                com.dsh.emu.EmuCore.setKeys(mask)
                if (!interruptibleSleep(180, myGen)) break
                com.dsh.emu.EmuCore.setKeys(0)
                if (!interruptibleSleep(90, myGen)) break
            }
        } finally {
            // 线程因取消退出时也要清按键，不能留着方向键一直走
            com.dsh.emu.EmuCore.setKeys(0)
        }
    }.start()
}
