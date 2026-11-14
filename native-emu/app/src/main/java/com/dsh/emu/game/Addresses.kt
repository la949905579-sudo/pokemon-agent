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
    const val PARTY_MENU_FLAG = 0x03000928
    const val BAG_CURSOR = 0x0203AD08
    const val MAIN_CURSOR = 0x02023FF8
    const val MOVE_CURSOR = 0x02023FFC
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
