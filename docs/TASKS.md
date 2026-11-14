# TASKS（任务队列）

> 规则：每任务 3 行卡（目标 / 验收 / 范围）；同一时间只一个 `doing`；完成后标 `done` 并写一行结果。
> 当前状态：**模式已固化（2026-11-14）**；无进行中任务；最新 Release `build-3f36e7a`（已 OTA）；下一步候选：横屏 WYSIWYG 后续 / 联机 / 结构债；地图相关全部暂缓。

## doing
1. **横屏 WYSIWYG 补完：对话选项 + 战斗菜单其余项**（2026-11-14 开工）
   - 目标：横屏下点对话框「是/否」等选项能选中（回读光标确认再按 A）；战斗主菜单「背包 / 宝可梦 / 逃跑」点选可用，各自有可回读信号验证；子菜单至少能点「取消」安全退出。
   - 验收：真机点对话选项 → 光标回读 = 目标选项且 A 生效（日志/状态证据）；背包/宝可梦/逃跑点选被接受并回读确认；竖屏不变；新增纯逻辑 Kotlin 单测；真机截图 + 日志证据。
   - 范围：`native-emu/app/src/main/java/com/dsh/emu/game` + `ui`（新内存地址需实测标定 → 危险区，收尾加 1 次 fresh 复核）；热区表重标定；`docs/` 同步。

## todo（按优先级）
1. **镜头贴地图边时的锚点偏移标定**（横屏小尾巴）：纯真机标定，改 `TouchMap` 常量 + 单测，低风险。
2. **联机**：GBA link cable，方案调研。
3. **结构债**（随触碰模块顺手做，不单开）：`EmuView`/`WalkControl` 零散逻辑继续迁出。

## 暂缓
- **地图相关功能全部暂缓**（用户 2026-11-14 拍板）：A\* 跨图补采 / UI 入口 / 实机对照、地图新交互控件、地图数据与可视化改进；已实现地图功能保持现状。

## done
- 2026-11-14 **横屏纯画面 + 触屏所见即所得**：横屏整屏铺满游戏画面、隐藏系统栏，仅留半透明设置图标（覆盖层面板：速度/自动战斗/载入 ROM/更新/重置/退出）；触屏映射（招式点按复用 `BattleMoveAction`、点「战斗」回读光标挪位+按 A+回读 `TURN_FLAG==2`、对话/战斗文字点按推进、点地图位置同图 BFS 走过去）；竖屏不变。
  - 新增 `ui/TouchMap.kt`（视口逆变换 + 热区表 + 镜头锚点 120,80，单测 `TouchMapTest`）、`ui/Wysiwyg.kt`、`ui/Landscape.kt`；`EmuView` 固定同一 Composition 位置，旋转不重建 SurfaceView。
  - 真机验收（build-`3f36e7a`，已 OTA）：横屏纯画面/面板/战斗菜单截图存 `/sdcard/Download/DSH-Go/wysiwyg-*.jpg`；点地图 → `wysiwyg.map from=10,10 target=16,12` 且坐标回读 `(16,12)`；点「战斗」 → `wysiwyg.fight ok=true turn=2`；点招式「抓」 → `battle.move idx=0 ok=true turn_before=2 turn_after=4`；动画期间点按被忽略；转回竖屏 UI 不变。
- 2026-11-14 **自动战斗开关**：设置页开关 + `ui/AutoBattle.kt` 后台循环（`AutoBattlePlanner`/`BattleDecider` 选招 → `BattleMoveAction` 施放；主菜单/对话 A 推进；连续 3 次失败自停；ROM 载入/重置/退出取消）；本地 Kotlin 单测绿；CI `1f305ad` success；**真机实测通过**：OTA 到新包后 2 场野生战均自动完成（`emu_native.log`：`battle.move idx=3 ok=true turn_before=2 turn_after=4`，转场 1→2→4；无 auto.battle 错误；开关开/关正常）。
- 2026-11-14 工作流重设计（单会话 + 本地构建/真机自测循环；归档旧治理文档；删除治理工具链；Python 冻结）。
- 2026-11-14 **名表 354**：补全 354 条（官方中文名 + Gen3 威力，`past_values` 还原）；数据源 `games/pokemon_firered/data/moves.json` + 生成器 `tools/gen_moves_data.py`（`--check` 通过）；`bdata.py` 改读 JSON、`GameData.kt` 重生成；新增 Kotlin `MoveTable354Test`；Python 测试更新（354 条 / 官方译名 / Gen3 数值，31/31 绿；Kotlin 单测绿）。
- 2026-11-14 **M4/M5 迁移**：45 个根 `.py` → `pyplatform/`；`maps/`/`battles/`/`dialogs/` → `games/pokemon_firered/`；路径引用同步（`plugin.py`/`terrain.py`/`start_push.sh`/`run_tests.py`/30 个测试 sys.path）；验收：Python 31/31 绿、import 冒烟过。
