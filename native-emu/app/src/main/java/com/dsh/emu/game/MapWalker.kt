package com.dsh.emu.game

/** 同地图内 BFS 寻路：把 tiles 通行数据转成方向序列。 */
object MapWalker {

    data class Point(val x: Int, val y: Int)

    /** 返回方向列表（"UP"/"DOWN"/"LEFT"/"RIGHT"），不可达返回 null。 */
    fun path(tiles: List<List<Int>>, from: Point, to: Point): List<String>? {
        if (tiles.isEmpty()) return null
        val h = tiles.size
        val w = tiles[0].size
        if (from.x !in 0 until w || from.y !in 0 until h) return null
        if (to.x !in 0 until w || to.y !in 0 until h) return null
        if (from == to) return emptyList()

        fun passable(x: Int, y: Int): Boolean =
            x in 0 until w && y in 0 until h && (tiles.getOrNull(y)?.getOrNull(x) ?: 0) == 1

        if (!passable(to.x, to.y)) return null

        val dirs = listOf("UP" to Point(0, -1), "DOWN" to Point(0, 1),
                          "LEFT" to Point(-1, 0), "RIGHT" to Point(1, 0))
        val prev = HashMap<Point, Pair<Point, String>?>()
        prev[from] = null
        val queue = ArrayDeque<Point>()
        queue.add(from)
        while (queue.isNotEmpty()) {
            val cur = queue.removeFirst()
            if (cur == to) break
            for ((name, d) in dirs) {
                val nx = cur.x + d.x
                val ny = cur.y + d.y
                val np = Point(nx, ny)
                if (!passable(nx, ny) || prev.containsKey(np)) continue
                prev[np] = cur to name
                queue.add(np)
            }
        }
        if (!prev.containsKey(to)) return null

        val steps = mutableListOf<String>()
        var cur = to
        while (cur != from) {
            val p = prev[cur] ?: return null
            steps.add(p.second)
            cur = p.first
        }
        steps.reverse()
        return steps
    }
}
