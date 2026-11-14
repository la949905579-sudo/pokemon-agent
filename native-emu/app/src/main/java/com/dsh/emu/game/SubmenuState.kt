package com.dsh.emu.game

/**
 * 战斗子菜单（背包 / 队伍）的只读状态适配层（2026-11-15 真机标定）。
 *
 * 为什么不用 MAIN_CURSOR 判断：战斗中 MAIN_CURSOR 会一直保留「从哪个战斗主菜单项进来」，
 * 背包里选道具弹出的「用在哪只宝可梦」队伍菜单，MAIN_CURSOR 仍是 1（背包）。
 * 所以用 `gWindows[0]` 的几何特征识别当前子菜单（窗口是每种界面固定模板）：
 * - 背包列表 win0 = (11,1) 18×12（item_menu.c 的 InitBagWindows）；
 * - 队伍大框 win0 = (1,3) 10×7（party_menu.c 的 PARTY_LAYOUT_SINGLE）。
 *
 * 只读：不做按键、不做重试；场景操纵在 `ui/Wysiwyg`（fail-closed）。
 */
object SubmenuState {

    /** 当前子菜单种类。 */
    enum class Kind(val logName: String) {
        BAG("bag"),
        PARTY("party"),
    }

    /** 背包：口袋数（道具 / 重要道具 / 精灵球，FRLG 只有 3 个口袋；招式学习器/树果在单独的 Case 里）。 */
    const val POCKET_COUNT = 3
    const val POCKET_ITEMS = 0
    const val POCKET_KEY_ITEMS = 1
    const val POCKET_POKE_BALLS = 2

    /** 背包列表一屏最多 6 行（窗口 12 tile 高，行高 16px；最后一行是「取消」）。 */
    const val BAG_MAX_ROWS = 6

    /** 队伍槽位数，以及「取消」在 slotId 里的取值（party_menu.c 的 SLOT_CANCEL = PARTY_SIZE + 1）。 */
    const val PARTY_SIZE = 6
    const val PARTY_CANCEL = PARTY_SIZE + 1

    /**
     * 由 `gWindows[0]` 的 12 字节结构判断子菜单种类；不是背包/队伍窗口返回 null（不猜）。
     * 字段：+0 bg +1 tilemapLeft +2 tilemapTop +3 width +4 height ...
     */
    fun kindFromWindow(win: ByteArray?): Kind? {
        if (win == null || win.size < 5) return null
        fun u(i: Int): Int = win[i].toInt() and 0xFF
        if (u(0) != 0) return null
        return when {
            u(1) == 11 && u(2) == 1 && u(3) == 18 && u(4) == 12 -> Kind.BAG
            u(1) == 1 && u(2) == 3 && u(3) == 10 && u(4) == 7 -> Kind.PARTY
            else -> null
        }
    }

    /** 线上读取当前子菜单种类；读不到 / 不在子菜单返回 null。 */
    fun readKind(): Kind? = kindFromWindow(Memo.bytes(Addresses.WINDOWS, 12))

    /** 背包当前口袋 0..2；读不到返回 -1。 */
    fun pocket(): Int {
        val p = Memo.u8(Addresses.BAG_POCKET)
        return if (p in 0 until POCKET_COUNT) p else -1
    }

    /** 指定口袋的「可视行号」（窗口里高亮第几行，0..BAG_MAX_ROWS-1）；读不到返回 -1。 */
    fun bagRow(pocket: Int): Int {
        if (pocket !in 0 until POCKET_COUNT) return -1
        val r = Memo.u8(Addresses.BAG_ROW_BASE + pocket * 2)
        return if (r in 0 until BAG_MAX_ROWS) r else -1
    }

    /** 指定口袋的列表滚动偏移（itemsAbove，>6 件道具时非 0）；读不到返回 -1。 */
    fun bagScroll(pocket: Int): Int {
        if (pocket !in 0 until POCKET_COUNT) return -1
        val s = Memo.u8(Addresses.BAG_SCROLL_BASE + pocket * 2)
        return if (s in 0..255) s else -1
    }

    /**
     * 绝对行号 = 滚动偏移 + 可视行号：点第几件道具、是否到「取消」都按它判断。
     * 读不到任一项返回 -1（调用方 fail-closed，不按 A）。
     */
    fun bagAbs(pocket: Int): Int {
        val row = bagRow(pocket)
        val scroll = bagScroll(pocket)
        if (row < 0 || scroll < 0) return -1
        return row + scroll
    }

    /** 队伍菜单 slotId：0..5，或 [PARTY_CANCEL]；读不到/-1 返回 -1。 */
    fun partyCursor(): Int {
        val c = Memo.u8(Addresses.PARTY_CURSOR)
        return if (c in 0 until PARTY_SIZE || c == PARTY_CANCEL) c else -1
    }
}
