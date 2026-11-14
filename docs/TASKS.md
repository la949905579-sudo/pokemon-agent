# TASKS（任务队列）

> 规则：每任务 3 行卡（目标 / 验收 / 范围）；同一时间只一个 `doing`；完成后标 `done` 并写一行结果。
> 当前状态：**模式已固化（2026-11-14）**；无进行中任务；最新 Release `build-d67eab1`（已装机）；下一步候选：背包/队伍子菜单点选 / 非标准选项框 / 镜头贴边 / 联机 / 结构债；地图相关全部暂缓。

## doing
（无）

## todo（按优先级）
1. **非标准选项框（3+ 选项）支持**：现在只认标准「是/否」框（21,9,6,4），其它选项框只提示、不按键。
2. **镜头贴地图边时的锚点偏移标定**：纯真机标定，改 `TouchMap` 常量 + 单测，低风险。
3. **联机**：GBA link cable，方案调研。
4. **结构债**（随触碰模块顺手做，不单开）：`EmuView`/`WalkControl` 零散逻辑继续迁出；WYSIWYG 小清理（`Wysiwyg` KDoc 的 `[cancel]`→`[cancelAll]`、`MenuState.insideWindow` 去留、`Landscape` 重置里与 `cancelAll` 重复的 `WalkControl.generation++`）。

## 暂缓
- **地图相关功能全部暂缓**（用户 2026-11-14 拍板）：A\* 跨图补采 / UI 入口 / 实机对照、地图新交互控件、地图数据与可视化改进；已实现地图功能保持现状。

## done
- 2026-11-15 **横屏战斗背包/队伍子菜单点选（翻口袋 + 道具行 + 队伍格子）**：新增 `game/SubmenuState.kt`——用 `gWindows[0]` 几何识别背包 `(11,1)18×12` / 队伍 `(1,3)10×7`（`E83==0` 走标准是/否）；真机标定 `gBagMenuState`：pocket=0x0203AD02、各口袋光标=0x0203AD04+2*pocket、队伍光标=0x0203B0A9(7=取消)。
  - 背包：◀▶ 箭头 (8,72)/(72,72) 点按=按 LEFT/RIGHT 翻口袋（回读 pocket）；列表行（win0 内区、行高 16）点按=回第一行逐行挪光标→二次确认→按 A（取消行=合上背包）；滚动箭头 (160,8)/(160,104) 排除行热区、点按=挪一格不按 A；底部条按图标态区分——光标在道具行（道具说明态）只提示，在「取消」行/空口袋（「合上背包」态）按 B 合上。
  - 队伍：大框 (1,3) / 右侧 5 行（行高 24）点按=挪光标→按 A；空位（slot≥队伍数）只提示；底部「取消」按钮 (24,17)6×2 按 B 返回。
  - 单测 172/172 绿（新增 `SubmenuStateTest`、`TouchMap` 子菜单热区、`partyCount`）；fresh 复核 2 轮（首轮 2 必修 + delta 2 必修全修）。
  - **>6 件道具滚动修复**（delta 复核必修）：真机标定 `+8+2p`=可视行、`+14+2p`=滚动偏移（写 8 件测试道具实测：DOWN 一次 abs=行+滚动恰 +1）；背包定位/末行探针/滚动箭头全部改用 abs（`SubmenuState.bagRow/bagScroll/bagAbs`）。真机闭环：滚动偏移=1 时点可见第 6 行 → `wysiwyg.bagitem targetAbs=6` → 用掉全复药、HP 23→35/35、道具槽 id19 消失；滚到底时点可见「取消」→ `targetAbs=8` 正确合上背包。
  - 真机（`build-e3be008`，已装机版本 0.2 (e3be008)）：日志 `wysiwyg.bagpocket ok=true`（口袋 0→1→2→1→0 往返 6 次）、`wysiwyg.bagbar onCancelRow=true`（空口袋合上）、`onCancelRow=false restoreRow=0`（道具说明态连点 3 次只提示不关）、`wysiwyg.bagitem ok=true`（取消行 A 合上）、`wysiwyg.party empty_slot`（空位不按 A）、`wysiwyg.submenu ok=true kind=party`（取消返回）；截图 `wysiwyg2-*.jpg`（横屏 moves/bag、竖屏 party）。
  - 未真机验：有效队伍换人（当时槽 1 无战斗、槽 2 队伍仅 1 只）、>6 种道具的滚动手感、双打队伍布局（识别不到时只保留底部取消，不会错按）。
- 2026-11-15 **横屏 WYSIWYG 补完（对话选项 + 战斗菜单其余项）**：新增 `game/MenuState.kt`（实测标定的 `sMenu@0x0203ADE4` / `gWindows@0x020204B4`：光标、选项数、行高、窗口几何 → 选项行命中）、`Addresses.BATTLE_MENU_FLAG=0x02023E83`；横屏对话/战斗「是/否」选项可点选（回读光标→逐行挪→二次确认→按 A，任何一步不满足只提示不按 A）；战斗主菜单「背包/宝可梦/逃跑」点选（E83!=0 才是真主菜单，按项回读 `TURN_FLAG/MAIN_CURSOR`）；背包/队伍子菜单点底部条 = 按 B 退出（取消条分区：背包 y≥114、队伍 y≥121）；`Wysiwyg` 加取消代际（离开横屏/开设置面板停手）。
  - fresh 复核 3 轮：首轮 4 必修全修；第二轮 2 必修 + 1 可选已修（`d67eab1`：cancelAll 停三路按键、E83==0 选项框可达、profile!=null 绝不按 A），真机复验通过（背包/取消条/逃跑/对话选项/纯文字 profile=null）；第三轮结论**可上线、无必修**（仅 3 条非阻塞清理建议，记入结构债）。
  - 真机验收（build `906d43a`，OTA 失败后用本机 HTTP 兜底装包）：`wysiwyg.dialog ok=true target=1 cursor=1 steps=1 count=2`（对话「否」）；`wysiwyg.battlemenu ok=true target=1/2/3 steps=1/2`（背包/宝可梦/逃跑）；`wysiwyg.submenu ok=true kind=bag/party`（底部取消条）；选项行外点击 `option=-1` 只提示不按 A；截图 `wysiwyg-landscape-bag-20261115.jpg`、`wysiwyg-portrait-20261115.jpg`。
  - 已知未做：背包道具行 / 队伍格子点选、非标准（3+ 选项）选项框（见 todo）。
- 2026-11-14 **横屏纯画面 + 触屏所见即所得**：横屏整屏铺满游戏画面、隐藏系统栏，仅留半透明设置图标（覆盖层面板：速度/自动战斗/载入 ROM/更新/重置/退出）；触屏映射（招式点按复用 `BattleMoveAction`、点「战斗」回读光标挪位+按 A+回读 `TURN_FLAG==2`、对话/战斗文字点按推进、点地图位置同图 BFS 走过去）；竖屏不变。
  - 新增 `ui/TouchMap.kt`（视口逆变换 + 热区表 + 镜头锚点 120,80，单测 `TouchMapTest`）、`ui/Wysiwyg.kt`、`ui/Landscape.kt`；`EmuView` 固定同一 Composition 位置，旋转不重建 SurfaceView。
  - 真机验收（build-`3f36e7a`，已 OTA）：横屏纯画面/面板/战斗菜单截图存 `/sdcard/Download/DSH-Go/wysiwyg-*.jpg`；点地图 → `wysiwyg.map from=10,10 target=16,12` 且坐标回读 `(16,12)`；点「战斗」 → `wysiwyg.fight ok=true turn=2`；点招式「抓」 → `battle.move idx=0 ok=true turn_before=2 turn_after=4`；动画期间点按被忽略；转回竖屏 UI 不变。
- 2026-11-14 **自动战斗开关**：设置页开关 + `ui/AutoBattle.kt` 后台循环（`AutoBattlePlanner`/`BattleDecider` 选招 → `BattleMoveAction` 施放；主菜单/对话 A 推进；连续 3 次失败自停；ROM 载入/重置/退出取消）；本地 Kotlin 单测绿；CI `1f305ad` success；**真机实测通过**：OTA 到新包后 2 场野生战均自动完成（`emu_native.log`：`battle.move idx=3 ok=true turn_before=2 turn_after=4`，转场 1→2→4；无 auto.battle 错误；开关开/关正常）。
- 2026-11-14 工作流重设计（单会话 + 本地构建/真机自测循环；归档旧治理文档；删除治理工具链；Python 冻结）。
- 2026-11-14 **名表 354**：补全 354 条（官方中文名 + Gen3 威力，`past_values` 还原）；数据源 `games/pokemon_firered/data/moves.json` + 生成器 `tools/gen_moves_data.py`（`--check` 通过）；`bdata.py` 改读 JSON、`GameData.kt` 重生成；新增 Kotlin `MoveTable354Test`；Python 测试更新（354 条 / 官方译名 / Gen3 数值，31/31 绿；Kotlin 单测绿）。
- 2026-11-14 **M4/M5 迁移**：45 个根 `.py` → `pyplatform/`；`maps/`/`battles/`/`dialogs/` → `games/pokemon_firered/`；路径引用同步（`plugin.py`/`terrain.py`/`start_push.sh`/`run_tests.py`/30 个测试 sys.path）；验收：Python 31/31 绿、import 冒烟过。
