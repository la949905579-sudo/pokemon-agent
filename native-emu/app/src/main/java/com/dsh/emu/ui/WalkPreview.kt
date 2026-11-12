package com.dsh.emu.ui

/**
 * 行走预览的折线点：从起点开始按方向序列逐格推进，返回含起点和终点的点列表。
 * 纯函数，方便单测（不影响真实移动）。
 */
internal fun previewPoints(fromX: Int, fromY: Int, steps: List<String>): List<Pair<Int, Int>> {
    val out = ArrayList<Pair<Int, Int>>(steps.size + 1)
    var x = fromX
    var y = fromY
    out.add(x to y)
    for (d in steps) {
        when (d) {
            "UP" -> y -= 1
            "DOWN" -> y += 1
            "LEFT" -> x -= 1
            "RIGHT" -> x += 1
        }
        out.add(x to y)
    }
    return out
}
