package com.dsh.emu.game

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** 离线单测：地图 tiles 归一化 / 地址读取 / assets 优先与内存回退。 */
class MapDataTest {

    private val memory = HashMap<Int, Byte>()

    private fun put(addr: Int, vararg bytes: Int) {
        bytes.forEachIndexed { i, b -> memory[addr + i] = b.toByte() }
    }

    private fun putU16(addr: Int, v: Int) {
        put(addr, v and 0xFF, (v shr 8) and 0xFF)
    }

    private fun putU32(addr: Int, v: Long) {
        put(addr, (v and 0xFF).toInt(), ((v shr 8) and 0xFF).toInt(),
            ((v shr 16) and 0xFF).toInt(), ((v shr 24) and 0xFF).toInt())
    }

    @Before
    fun setUp() {
        memory.clear()
        MapData.resetForTest()
        Memo.reader = { addr, n -> ByteArray(n) { i -> memory[addr + i] ?: 0 } }
    }

    private fun setupHeader(hdr: Int, w: Int, h: Int, mapAddr: Int) {
        putU32(MapData.MAP_HDR_PTR, hdr.toLong())
        putU32(hdr, w.toLong())
        putU32(hdr + 4, h.toLong())
        putU32(hdr + 0x0C, mapAddr.toLong())
    }

    @Test
    fun normalizeCollisionBitsToPassable() {
        // 碰撞位 0=可走，非 0=挡 → 归一化成 1/0
        assertEquals(listOf(listOf(1, 0, 0, 0)), MapData.normalize(listOf(listOf(0, 1, 2, 3))))
        assertEquals(1, MapData.normalize(listOf(listOf(0)))[0][0])
    }

    @Test
    fun currentMapAddrReadsHeaderPointer() {
        val hdr = 0x08250000
        setupHeader(hdr, 15, 10, 0x0825477C)
        assertEquals(0x0825477C, MapData.currentMapAddr())
        assertEquals(15 to 10, MapData.mapSize())
    }

    @Test
    fun currentMapAddrRejectsGarbagePointer() {
        putU32(MapData.MAP_HDR_PTR, 0x4CE42F08L)  // 非法指针（terrain.py 注释里的实际垃圾值）
        assertEquals(0, MapData.currentMapAddr())
        assertNull(MapData.mapSize())
    }

    @Test
    fun fromMemoryNormalizesCollisionBits() {
        val mapAddr = 0x08260000
        // 3x2：碰撞位依次 0/1/0、3/2/0
        val collisions = intArrayOf(0, 1, 0, 3, 2, 0)
        for (i in collisions.indices) putU16(mapAddr + i * 2, (collisions[i] shl 10) or 5)
        val tiles = MapData.fromMemory(mapAddr, 3, 2)!!
        assertEquals(listOf(listOf(1, 0, 1), listOf(0, 0, 1)), tiles)
    }

    @Test
    fun assetLayerExposesInjectedMapForCrossMapPlan() {
        val tiles = listOf(listOf(1, 0), listOf(0, 1))
        MapData.putAssetTilesForTest(0x08260000, tiles)
        val layer = MapData.assetLayer(0x08260000)!!
        assertEquals(2, layer.w)
        assertEquals(2, layer.h)
        assertTrue(layer.fromAssets)
        assertEquals(tiles, layer.tiles)
        assertNull("未注入的图返回 null", MapData.assetLayer(0x08270000))
    }

    @Test
    fun currentPrefersAssets() {
        val hdr = 0x08250000
        val mapAddr = 0x0825477C
        setupHeader(hdr, 5, 5, mapAddr)   // mapSize 只认 5..120 的地图
        val assetTiles = List(5) { List(5) { 1 } }
        MapData.putAssetTilesForTest(mapAddr, assetTiles)
        // 内存里放一张完全不同的图，确认没被用到
        for (i in 0 until 25) putU16(mapAddr + i * 2, (1 shl 10))
        val layer = MapData.current()!!
        assertTrue(layer.fromAssets)
        assertEquals(mapAddr, layer.addr)
        assertEquals(assetTiles, layer.tiles)
    }

    @Test
    fun currentFallsBackToMemoryWhenNoAsset() {
        val hdr = 0x08250000
        val mapAddr = 0x08260000
        setupHeader(hdr, 5, 5, mapAddr)
        for (i in 0 until 25) putU16(mapAddr + i * 2, 0)  // 全可走
        putU16(mapAddr, 1 shl 10)                          // (0,0) 挡
        val layer = MapData.current()!!
        assertFalse(layer.fromAssets)
        assertEquals(0, layer.tiles[0][0])
        assertEquals(1, layer.tiles[0][1])
    }

    @Test
    fun currentNullWhenHeaderUnreadable() {
        Memo.reader = { _, _ -> null }
        assertNull(MapData.current())
    }
}
