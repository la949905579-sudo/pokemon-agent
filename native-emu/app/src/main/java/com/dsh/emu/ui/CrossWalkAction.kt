package com.dsh.emu.ui

import com.dsh.emu.EmuCore
import com.dsh.emu.MainActivity
import com.dsh.emu.Nlog
import com.dsh.emu.game.CrossMapPathfinder
import com.dsh.emu.game.CrossMapWalker
import com.dsh.emu.game.GameState
import com.dsh.emu.game.MapData

/**
 * 跨图执行器接线：把 [CrossMapWalker.Io] 接到 JNI（读地图/坐标、按方向键）+ 取消代际。
 *
 * 与同图「点击前往」共用 [WalkControl.generation]：取消/换页 +1 后线程立刻停并按 0。
 * 失败/取消只写一行 statusText（不补按、不重试），退出前统一清按键。
 */
internal object CrossWalkAction {

    /** 跑一遍跨图计划；返回是否在后台线程启动成功（计划为空返回 false）。 */
    fun start(activity: MainActivity, plan: CrossMapPathfinder.Plan) {
        val myGen = ++WalkControl.generation
        activity.statusText.value = "跨图前往：${plan.totalSteps} 步"
        Thread {
            val io = object : CrossMapWalker.Io {
                override fun readMapAddr(): Int = MapData.currentMapAddr()
                override fun readPos(): Pair<Int, Int>? = GameState.coords()?.let { it.x to it.y }

                override fun press(dir: String): Boolean {
                    if (myGen != WalkControl.generation) return false
                    val mask = when (dir) {
                        "UP" -> EmuCore.KEY_UP
                        "DOWN" -> EmuCore.KEY_DOWN
                        "LEFT" -> EmuCore.KEY_LEFT
                        else -> EmuCore.KEY_RIGHT
                    }
                    EmuCore.setKeys(mask)
                    if (!interruptibleSleep(180, myGen)) {
                        EmuCore.setKeys(0)
                        return false
                    }
                    EmuCore.setKeys(0)
                    return interruptibleSleep(90, myGen)
                }

                override fun sleep(ms: Long) {
                    interruptibleSleep(ms, myGen)
                }

                override fun clearKeys() {
                    EmuCore.setKeys(0)
                }

                override fun cancelled(): Boolean = myGen != WalkControl.generation
            }
            val result = CrossMapWalker.walk(plan, io)
            val ok = result is CrossMapWalker.Result.Ok
            val steps = when (result) {
                is CrossMapWalker.Result.Ok -> result.steps
                is CrossMapWalker.Result.Cancelled -> result.steps
                is CrossMapWalker.Result.Failed -> result.steps
            }
            val reason = when (result) {
                is CrossMapWalker.Result.Ok -> "ok"
                is CrossMapWalker.Result.Cancelled -> "cancelled"
                is CrossMapWalker.Result.Failed -> result.reason.name.lowercase() +
                    (if (result.detail.isBlank()) "" else "/" + result.detail)
            }
            Nlog.info("crosswalk.result", "ok" to ok, "steps" to steps, "reason" to reason)
            val msg = when (result) {
                is CrossMapWalker.Result.Ok -> "跨图到达：${result.steps} 步"
                is CrossMapWalker.Result.Cancelled -> "已取消跨图"
                is CrossMapWalker.Result.Failed -> "跨图中断：$reason（已走 $steps 步）"
            }
            activity.runOnUiThread {
                activity.statusText.value = msg
                activity.crossPlanState.value = null
            }
        }.start()
    }
}
