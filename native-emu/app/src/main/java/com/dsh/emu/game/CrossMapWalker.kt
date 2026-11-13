package com.dsh.emu.game

/**
 * 跨图计划的执行器：按 [CrossMapPathfinder.Plan] 逐段按键、处理换图、检测卡住/坐标异常/取消。
 *
 * 全部 IO 注入（读地图地址/坐标、按单步、等待、清键、取消判断）：
 * 不读内存、不碰 Android，离线单测用假世界即可覆盖；线上由 UI 层接线（本批不接 UI 入口）。
 *
 * 失败即停：不补按、不重试；卡住累计 [STUCK_LIMIT] 次 / 换图后地图或坐标不符 / 起点不符 → Failed。
 * 取消语义与 `closeKeys()` 一致：立刻停止按键并清键（[walk] 出口统一 clearKeys）。
 */
object CrossMapWalker {
    /** 换图后等待地图与坐标生效的时间。 */
    const val WARP_WAIT_MS = 800L

    /** 连续多少步「按键后坐标没变」算卡住。 */
    const val STUCK_LIMIT = 3

    /** 执行器依赖：线上接 JNI/线程，单测接假世界。全部同步调用。 */
    interface Io {
        /** 当前地图数组地址（与 plan 里的 map 同口径）；读不到返回 0。 */
        fun readMapAddr(): Int

        /** 当前 tile 坐标（已减去 7）；读不到返回 null。 */
        fun readPos(): Pair<Int, Int>?

        /** 按一步方向键（UP/DOWN/LEFT/RIGHT）；false = 已被取消，不再按键。 */
        fun press(dir: String): Boolean

        /** 等待（换图生效）；实现应可中断。 */
        fun sleep(ms: Long)

        /** 清按键掩码（取消/结束必须调用）。 */
        fun clearKeys()

        /** 已被取消：返回 true 后执行器不再按键。 */
        fun cancelled(): Boolean
    }

    sealed class Result {
        data class Ok(val steps: Int) : Result()
        data class Cancelled(val steps: Int) : Result()
        data class Failed(val reason: Reason, val steps: Int, val detail: String = "") : Result()
    }

    enum class Reason {
        START_MISMATCH,   // 起点地图不是计划的地图（可能刚被换图/取消）
        MAP_CHANGED,      // 段内地图变了（非计划换图）
        POS_UNREADABLE,   // 坐标读不到
        STUCK,            // 连续按键坐标不变
        WARP_MISMATCH,    // 换图后地图或落点坐标不符
        GOAL_MISMATCH,    // 走完但终点坐标不符
    }

    /** 执行计划；无论成功/失败/取消，退出前都会 [Io.clearKeys]。 */
    fun walk(plan: CrossMapPathfinder.Plan, io: Io): Result = try {
        walkInner(plan, io)
    } finally {
        io.clearKeys()
    }

    private fun walkInner(plan: CrossMapPathfinder.Plan, io: Io): Result {
        var steps = 0

        if (io.readMapAddr() != plan.start.map) return Result.Failed(Reason.START_MISMATCH, steps)
        var lastPos = io.readPos() ?: return Result.Failed(Reason.POS_UNREADABLE, steps)

        for (leg in plan.legs) {
            if (io.cancelled()) return Result.Cancelled(steps)
            if (io.readMapAddr() != leg.map) return Result.Failed(Reason.MAP_CHANGED, steps)
            lastPos = io.readPos() ?: return Result.Failed(Reason.POS_UNREADABLE, steps)
            var stuck = 0
            for ((i, dir) in leg.dirs.withIndex()) {
                if (io.cancelled()) return Result.Cancelled(steps)
                if (!io.press(dir)) return Result.Cancelled(steps)
                steps++
                val pos = io.readPos() ?: return Result.Failed(Reason.POS_UNREADABLE, steps)
                // 踩格触发的换图：最后一步走完地图已变，不按同图规则判卡住。
                val warpEntry = leg.warp != null && leg.warp.sideDir == null && i == leg.dirs.lastIndex
                if (!warpEntry && pos == lastPos) {
                    stuck++
                    if (stuck >= STUCK_LIMIT) return Result.Failed(Reason.STUCK, steps)
                } else {
                    stuck = 0
                }
                lastPos = pos
            }

            val warp = leg.warp ?: break
            if (warp.sideDir != null) {
                if (io.cancelled()) return Result.Cancelled(steps)
                if (!io.press(warp.sideDir)) return Result.Cancelled(steps)
                steps++
            }
            io.sleep(WARP_WAIT_MS)
            if (io.cancelled()) return Result.Cancelled(steps)
            if (io.readMapAddr() != warp.toMap) {
                return Result.Failed(Reason.WARP_MISMATCH, steps, "map")
            }
            val p = io.readPos() ?: return Result.Failed(Reason.POS_UNREADABLE, steps)
            if (p != (warp.toX to warp.toY)) {
                return Result.Failed(Reason.WARP_MISMATCH, steps, "pos")
            }
            lastPos = p
        }

        val end = io.readPos() ?: return Result.Failed(Reason.POS_UNREADABLE, steps)
        if (end != (plan.goal.x to plan.goal.y)) return Result.Failed(Reason.GOAL_MISMATCH, steps)
        return Result.Ok(steps)
    }
}
