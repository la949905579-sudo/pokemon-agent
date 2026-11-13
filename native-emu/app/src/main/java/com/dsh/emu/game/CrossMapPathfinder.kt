package com.dsh.emu.game

import java.util.PriorityQueue

/**
 * 跨图 A* 寻路：节点 = (地图地址, tile x, tile y)。
 *
 * 边：
 * - 同图四邻，`tiles==1` 可走（与 [MapWalker] 一致；assets 只有碰撞 0/1、无高度层）；
 * - 换图边：出口格 → 目标图落点（[MapLink]）。`side` 非空 = 站上出口格后再朝该方向一步触发；
 *   `side` 为空 = 踩上出口格即触发（该格本身不当普通节点，从相邻格直接过边）。
 *
 * 启发函数：同目标图取曼哈顿距离，其他地图取 0——可采纳且一致（换图边真实代价 ≥1，
 * 跨图节点到目标至少还要再走一步以上）。
 *
 * 数据缺失（某图 tiles 为 null）时该图不能走，相关连通域不可达 → 返回 null。
 * 纯函数：tiles/links 由调用方注入，便于离线单测；运行期用 [planDefault]。
 */
object CrossMapPathfinder {
    data class Pos(val map: Int, val x: Int, val y: Int)

    /** 换图动作：站上 ([exitX],[exitY]) 后，[sideDir] 非空则再朝该方向一步触发；null=踩格触发。 */
    data class Warp(
        val exitX: Int, val exitY: Int, val sideDir: String?,
        val toMap: Int, val toX: Int, val toY: Int,
    )

    /** 一段同图行走；最后一段 [warp]==null。 */
    data class Leg(val map: Int, val dirs: List<String>, val warp: Warp?)

    data class Plan(val start: Pos, val goal: Pos, val legs: List<Leg>) {
        /** 需要按的步数（含换图多按的一步；不含换图等待）。 */
        val totalSteps: Int get() = legs.sumOf { it.dirs.size }
    }

    private val DIRS = listOf(
        "UP" to (0 to -1), "DOWN" to (0 to 1),
        "LEFT" to (-1 to 0), "RIGHT" to (1 to 0),
    )

    /** 节点上限：防脏数据把 A* 拖爆。 */
    private const val MAX_NODES = 50_000

    /**
     * 规划从 [start] 到 [goal] 的跨图路线。
     *
     * @param tilesOf 地图地址 → tiles（`tiles[y][x]`，1=可走）；返回 null 表示没有该图数据。
     * @param linksFrom 地图地址 → 该图的出口连接。
     */
    fun plan(
        start: Pos,
        goal: Pos,
        tilesOf: (Int) -> List<List<Int>>?,
        linksFrom: (Int) -> List<MapLink>,
    ): Plan? {
        if (start == goal) return Plan(start, goal, listOf(Leg(start.map, emptyList(), null)))

        // 同图：直接降级成现有 MapWalker（行为与当前「点击前往」一致）。
        if (start.map == goal.map) {
            val tiles = tilesOf(start.map) ?: return null
            val dirs = MapWalker.path(
                tiles,
                MapWalker.Point(start.x, start.y),
                MapWalker.Point(goal.x, goal.y),
            ) ?: return null
            return Plan(start, goal, listOf(Leg(start.map, dirs, null)))
        }

        val tilesCache = HashMap<Int, List<List<Int>>?>()
        fun tilesFor(map: Int): List<List<Int>>? =
            tilesCache.getOrPut(map) { tilesOf(map) }

        fun walkable(map: Int, x: Int, y: Int): Boolean {
            val tiles = tilesFor(map) ?: return false
            val row = tiles.getOrNull(y) ?: return false
            return row.getOrNull(x) == 1
        }

        val linksCache = HashMap<Int, List<MapLink>>()
        fun linksFor(map: Int): List<MapLink> = linksCache.getOrPut(map) { linksFrom(map) }

        fun heuristic(p: Pos): Int =
            if (p.map == goal.map) Math.abs(p.x - goal.x) + Math.abs(p.y - goal.y) else 0

        val dist = HashMap<Pos, Int>()
        val cameFrom = HashMap<Pos, Edge>()
        val open = PriorityQueue<QNode>(compareBy({ it.f }, { it.g }, { it.pos.map }, { it.pos.x }, { it.pos.y }))
        dist[start] = 0
        open.add(QNode(heuristic(start), 0, start))
        var visited = 0

        while (open.isNotEmpty() && visited < MAX_NODES) {
            val cur = open.poll()
            if (dist[cur.pos] != cur.g) continue
            visited++
            if (cur.pos == goal) return reconstruct(start, goal, cameFrom)

            val map = cur.pos.map
            // 1) 同图四邻：普通可走；踩格换图的出口格不进去，直接当跨图边处理。
            for ((dir, d) in DIRS) {
                val nx = cur.pos.x + d.first
                val ny = cur.pos.y + d.second
                val warpTiles = linksFor(map).filter {
                    it.exitX == nx && it.exitY == ny && MapLinks.sideDir(it.side) == null
                }
                if (warpTiles.isNotEmpty()) {
                    for (link in warpTiles) {
                        for (dest in link.destinations()) {
                            val to = Pos(dest.toMap, dest.toX, dest.toY)
                            relaxed(cur.pos, to, 1, Edge(cur.pos, dir, Warp(nx, ny, null, dest.toMap, dest.toX, dest.toY)),
                                dist, cameFrom, open, ::heuristic)
                        }
                    }
                } else {
                    if (!walkable(map, nx, ny)) continue
                    val to = Pos(map, nx, ny)
                    relaxed(cur.pos, to, 1, Edge(cur.pos, dir, null), dist, cameFrom, open, ::heuristic)
                }
            }
            // 2) 自身出口格（side 非空）：站上出口格后再朝该方向一步换图。
            for (link in linksFor(map)) {
                if (link.exitX != cur.pos.x || link.exitY != cur.pos.y) continue
                val sideDir = MapLinks.sideDir(link.side) ?: continue
                for (dest in link.destinations()) {
                    val to = Pos(dest.toMap, dest.toX, dest.toY)
                    relaxed(cur.pos, to, 1,
                        Edge(cur.pos, null, Warp(cur.pos.x, cur.pos.y, sideDir, dest.toMap, dest.toX, dest.toY)),
                        dist, cameFrom, open, ::heuristic)
                }
            }
        }
        return null
    }

    /** 运行期入口：tiles 来自 assets（[MapData.assetLayer]），links 来自 [MapLinks]。 */
    fun planDefault(start: Pos, goal: Pos): Plan? = plan(
        start, goal,
        tilesOf = { addr -> MapData.assetLayer(addr)?.tiles },
        linksFrom = { addr -> MapLinks.linksFrom(addr) },
    )

    // ---------- 内部 ----------

    private data class QNode(val f: Int, val g: Int, val pos: Pos)

    /** 一条搜索树边：[dir] 为同图一步的方向；[warp] 非空表示这一步/这次换图跨了地图。 */
    private data class Edge(val from: Pos, val dir: String?, val warp: Warp?)

    private fun relaxed(
        from: Pos, to: Pos, cost: Int, edge: Edge,
        dist: HashMap<Pos, Int>,
        cameFrom: HashMap<Pos, Edge>,
        open: PriorityQueue<QNode>,
        heuristic: (Pos) -> Int,
    ) {
        val ng = (dist[from] ?: return) + cost
        val old = dist[to]
        if (old != null && old <= ng) return
        dist[to] = ng
        cameFrom[to] = edge
        open.add(QNode(ng + heuristic(to), ng, to))
    }

    private fun reconstruct(start: Pos, goal: Pos, cameFrom: HashMap<Pos, Edge>): Plan? {
        val edges = ArrayList<Edge>()
        var cur = goal
        while (cur != start) {
            val e = cameFrom[cur] ?: return null
            edges.add(e)
            cur = e.from
        }
        edges.reverse()

        val legs = ArrayList<Leg>()
        var legMap = start.map
        var dirs = ArrayList<String>()
        for (e in edges) {
            val warp = e.warp
            if (warp == null) {
                e.dir?.let { dirs.add(it) }
                continue
            }
            e.dir?.let { dirs.add(it) }   // 踩格触发的最后一步
            legs.add(Leg(legMap, dirs, warp))
            dirs = ArrayList()
            legMap = warp.toMap
        }
        legs.add(Leg(legMap, dirs, null))
        return Plan(start, goal, legs)
    }
}
