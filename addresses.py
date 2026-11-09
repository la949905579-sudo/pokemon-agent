"""游戏内存地址表（全部实测过）。"""

PARTY_ADDR = 0x02024284            # 真·队伍数据（FireRed gPlayerParty）
BATTLE_FLAG = 0x02024018
DIALOG_FLAG = 0x03000F9C
TURN_FLAG = 0x02023E82   # 1=主菜单(玩家输入) 2=招式菜单 4=事件/动画 0=开场消息
PARTY_MENU_FLAG = 0x03000928   # 队伍/换人菜单打开时非零，招式菜单时为 0
BAG_CURSOR = 0x0203AD08     # 背包菜单：道具光标（0=第一件道具，依次往下）
MAIN_CURSOR = 0x02023FF8   # 主菜单：0=战斗 1=背包 2=宝可梦 3=逃跑
MOVE_CURSOR = 0x02023FFC   # 招式菜单：0=左上 1=右上 2=左下 3=右下
PARTY_CURSOR = 0x0203B0A9   # 队伍/换人菜单：0-5，对应队伍第 1-6 只
FACING_ADDR = 0x02036E38 + 0x18   # 玩家对象 +0x18 低字节
