# TASKS（任务队列）

> 规则：每任务 3 行卡（目标 / 验收 / 范围）；同一时间只一个 `doing`；完成后标 `done` 并写一行结果。
> 当前状态：**无进行中任务**（M4/M5、名表 354 已完成，见 done）；等用户点名下一步。

## doing
- **自动化开关（自动战斗）**：设置页加「自动战斗」开关；Kotlin 后台循环：战斗菜单展开时按 `BattleDecider` 选最优招式 → 复用 `BattleMoveAction` 施放；主菜单/对话时按 A 推进；fail-closed，连续失败 3 次自动停；ROM 载入/重置/退出时静默取消。
  验收：本地 Kotlin 单测（planner 纯逻辑 + 现有战斗测试）全绿；CI 构建成功；真机冒烟：战斗中点开关后自动出招并打完一场，状态行有反馈。
  范围：`game/AutoBattlePlanner.kt`（新）、`ui/AutoBattle.kt`（新）、`ui/Pages.kt`（设置页开关）、`MainActivity.kt`（载入 ROM 取消）、`app/src/test/.../AutoBattlePlannerTest.kt`（新）。

## todo（按优先级）
1. **横屏 + 触屏所见即所得**
   - 目标：横屏只显示游戏画面（单屏铺满），仅一个半透明设置图标打开模拟器设置；所有操作＝点击画面实际位置（出招点招式位置、对话/菜单点选项、点地图位置人物前往）；竖屏不变。
   - 验收：横屏无其他控件；点招式实际位置成功施放（回读确认）；点地图位置走到目标（同图 BFS）；竖屏行为不变；真机截图证据。
   - 范围：`native-emu/app/src/main/**`（Compose 布局 + 点击映射 + 热区表资源）；待确认：设置面板形态（覆盖层 / 全屏页）。
2. **自动化开关**：工具页开关 + Kotlin 协程战斗循环（复用 BattleDecider/SwitchDecider）。
3. **联机**：GBA link cable，方案调研。
4. **结构债**（随触碰模块顺手做，不单开）：`EmuView`/`WalkControl` 零散逻辑继续迁出。

## 暂缓
- **地图相关功能全部暂缓**（用户 2026-11-14 拍板）：A\* 跨图补采 / UI 入口 / 实机对照、地图新交互控件、地图数据与可视化改进；已实现地图功能保持现状。

## done
- 2026-11-14 工作流重设计（单会话 + 本地构建/真机自测循环；归档旧治理文档；删除治理工具链；Python 冻结）。
- 2026-11-14 **名表 354**：补全 354 条（官方中文名 + Gen3 威力，`past_values` 还原）；数据源 `games/pokemon_firered/data/moves.json` + 生成器 `tools/gen_moves_data.py`（`--check` 通过）；`bdata.py` 改读 JSON、`GameData.kt` 重生成；新增 Kotlin `MoveTable354Test`；Python 测试更新（354 条 / 官方译名 / Gen3 数值，31/31 绿；Kotlin 单测绿）。
- 2026-11-14 **M4/M5 迁移**：45 个根 `.py` → `pyplatform/`；`maps/`/`battles/`/`dialogs/` → `games/pokemon_firered/`；路径引用同步（`plugin.py`/`terrain.py`/`start_push.sh`/`run_tests.py`/30 个测试 sys.path）；验收：Python 31/31 绿、import 冒烟过。
