package com.dsh.emu.game

/**
 * 游戏内存地址表（从 Python 的 addresses.py 移植，全部实测过）。
 * 注释里的原变量名用于和 Python 版对照。
 */
object Addresses {
    const val PARTY_ADDR = 0x02024284        // gPlayerParty（6 只 × 100 字节）
    const val BATTLE_FLAG = 0x02024018       // 0 = 地图，非 0 = 战斗中
    const val DIALOG_FLAG = 0x03000F9C       // 对话框打开时非 0
    const val TURN_FLAG = 0x02023E82         // 1=主菜单 2=招式 4=动画 0=开场
    // Turn 状态第 2 字节（Python state.py 实测 + 2026-11-15 真机复核）：
    // 战斗内 E82=1 且 E83=0 = 「是/否」选项框；E83!=0（实测主菜单/招式/背包/队伍都是 4）
    // 才是真正的战斗菜单。少了这个判断会把选项框当主菜单按 A（默认确认）。
    const val BATTLE_MENU_FLAG = 0x02023E83
    const val PARTY_MENU_FLAG = 0x03000928
    // 背包菜单状态（item_menu.c 的 gBagMenuState，EWRAM 全局；struct BagStruct 见 item_menu.h）。
    // 2026-11-15 真机标定：+0 bagCallback(4) +4 location +5 bagOpen +6 pocket(u16)；
    // +8/+10/+12 = 口袋 0/1/2 的「可视行号」（窗口里高亮第几行，0=第一行），
    // +14/+16/+18 = 口袋 0/1/2 的「列表滚动偏移」（itemsAbove；道具 >6 件才非 0）。
    // 绝对行号 abs = 滚动偏移 + 可视行号；「取消」= 最后一行，其 abs 未知（件数不可直读），
    // 所以判断是否末行用「再按一次 DOWN 后 abs 是否变化」。2026-11-15 用 8 件测试道具真机标定：
    // row(+8) 与 scroll(+14) 各口袋独立，DOWN 一次 abs 恰 +1（含跨页滚动）。
    const val BAG_MENU_STATE = 0x0203ACFC
    const val BAG_POCKET = BAG_MENU_STATE + 6        // 0x0203AD02：0=道具 1=重要道具 2=精灵球
    const val BAG_ROW_BASE = BAG_MENU_STATE + 8      // 0x0203AD04：口袋 p 可视行号 = ROW + 2*p
    const val BAG_SCROLL_BASE = BAG_MENU_STATE + 14  // 0x0203AD0A：口袋 p 滚动偏移 = SCROLL + 2*p
    /** 旧名（= 可视行号基址）；保留给 Python 旧层对照。 */
    const val BAG_CURSOR_BASE = BAG_ROW_BASE
    /** 旧地址（口袋 2 的可视行号）；仅为兼容 Python 旧层保留。 */
    const val BAG_CURSOR = 0x0203AD08
    const val MAIN_CURSOR = 0x02023FF8
    const val MOVE_CURSOR = 0x02023FFC
    // 队伍菜单 slotId：0..5 = 队伍第 1..6 只，7 = 「取消」（PARTY_SIZE+1）；2026-11-15 真机标定。
    const val PARTY_CURSOR = 0x0203B0A9
    const val FACING_ADDR = 0x02036E38 + 0x18

    const val ENEMY_BASE = 0x02024080        // 敌方战斗摘要：+0 等级，+2 HP，+4 maxHP
    const val MY_BATTLE = 0x02023BE4         // 我方场上
    const val EN_BATTLE = 0x02023C3C         // 敌方场上
    const val MOVE_LAST = 0x02023D4C
    const val MOVE_MINE = 0x02023DC4

    const val X_ADDR = 0x02036E48
    const val Y_ADDR = 0x02036E4A
    const val TILE_OFF = 7                   // 地块坐标 = 原始 - 7

    // 菜单系统（2026-11-14 实测标定：存档「是/否」框）
    // sMenu（menu.c 的 static struct Menu，12 字节）：
    //   +0 left +1 top +2 cursorPos +3 minCursorPos +4 maxCursorPos +5 windowId
    //   +6 fontId +7 optionWidth +8 optionHeight +9 columns +10 rows +11 APressMuted
    const val MENU_STATE = 0x0203ADE4
    // gWindows[32]（window.c 的 struct Window，12 字节：WindowTemplate 8B + tileData 指针 4B）：
    //   +0 bg +1 tilemapLeft +2 tilemapTop +3 width +4 height +5 paletteNum
    //   +6 baseBlock(u16) +8 tileData(ptr)。窗框占 (tilemapLeft-1 .. tilemapLeft+width) 格。
    const val WINDOWS = 0x020204B4

    // 队伍结构（100 字节/只）
    const val PARTY_STRIDE = 100
    const val PARTY_LV = 0x54
    const val PARTY_HP = 0x56
    const val PARTY_PID = 0x00
    const val PARTY_OTID = 0x04
}
