package com.dsh.emu.game

/**
 * 招式菜单的只读适配层（ui → game）：界面层通过本对象读菜单状态，不直接碰 [Memo]/地址。
 *
 * 口径以 Python `addresses.py` 为单一真源：
 * - `TURN_FLAG`：1=主菜单 2=招式菜单 4=动画 0=开场；
 * - `MAIN_CURSOR`：主菜单光标 0=战斗 1=背包 2=宝可梦 3=逃跑；进入招式菜单后保留 0，
 *   所以 `0` 既是「战斗主菜单项」也是「从战斗项进入的招式菜单入口」；
 * - `MOVE_CURSOR`：招式菜单 2×2 四格 0..3。
 *
 * 读不到统一返回 -1，由 [MoveCaster] 的 fail-closed 守卫拒绝，不在这里兜底。
 */
object BattleMoveMenu {
    /** TURN_FLAG：读不到返回 -1。 */
    fun readTurn(): Int = GameState.turnFlag()

    /** MAIN_CURSOR：0=战斗（招式菜单入口）；读不到返回 -1。 */
    fun readMainCursor(): Int = Memo.u8(Addresses.MAIN_CURSOR)

    /** MOVE_CURSOR：0..3；读不到返回 -1。 */
    fun readMoveCursor(): Int = Memo.u8(Addresses.MOVE_CURSOR)
}
