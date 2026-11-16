# CHANGELOG

> 版本规则：功能批一个条目；只记行为/接口变化。旧历史见 `docs/archive/2026-11/history/CHANGELOG.md`。

## 2026-11-16 地形行为接入 + 地图页遭遇（功能）
- `assets/maps` 每张图新增 `behaviors`（2 hex/格，来自布局 tileset 的 metatile 属性表）与 `maps`（地图 id 列表），`encounters_leafgreen.json` 随地图资产进 APK；`tools/gen_map_assets.py --check` 扩展校验。
- 步行判定改为 fail-closed：按引擎 `sBehaviorSurfable` 表把水面/瀑布/水流（16-19/21/26/27/80-83）判为不可走，`MB_SHALLOW_WATER(23)` 保持可走；跨图寻路同步生效。
- 地图页/常驻图按 水/草/台阶/挡 着色；地图页底部显示当前图遭遇（陆/水/碎岩/钓，种 + Lv 区间，横向滚动）；状态 JSON 带 terrain/encounters，日志 `map.terrain`/`map.encounters` 每图一次。
- 单测 Kotlin 186/186、Python 33/33；真机 `build-5931f4a`：`indexed=345`、0 fallback、terrain/encounters 日志与截图证据。

## 2026-11-16 全量地图资产 + 解包连接表（功能）
- 地图页/跨图寻路数据升级：`assets/maps` 从 11 张真机抓图扩到 **345 个 ROM 地址**（解包 365 布局按 `map.bin` 字节在 ROM 反查地址，结构体+border 消歧）；新增 `tools/gen_map_assets.py` 重新生成资产与 `map_links.json`（2769 个出口，来自解包 `connections`，规则与实测一致）。
- `MapData` 资产改为懒加载（启动只列目录，用到才解析），避免 345 个文件主线程解析卡顿。
- 交叉校验：现有真机走位记录 13/13 命中、旧 11 张资产逐格一致；真机 `map.assets indexed=345`、新会话 0 条 `map.fallback`。
- 未接线：跨图寻路 UI 入口（`CrossMapWalker`）、门/楼梯坐标口径、行为/遭遇展示。

## 2026-11-15 横屏战斗子菜单点选（功能）
- 背包：横屏点 ◀▶ 箭头翻口袋（道具/重要道具/精灵球，3 口袋）；点道具行回第一行逐行挪光标→二次确认→按 A（最后一行「取消」=合上背包）；列表右侧滚动箭头点按=挪一格；底部条按实机图标态区分——道具说明态只提示，光标在「取消」行/空口袋（「合上背包」态）才按 B 合上。
- 队伍：点左侧大框/右侧 5 行选中宝可梦（挪光标→按 A，可作换人或道具目标）；空位只提示；右下「取消」按钮返回战斗菜单。
- 识别改用 `gWindows[0]` 几何（背包 `(11,1)18×12`、队伍 `(1,3)10×7`），不再只看 `MAIN_CURSOR`（背包→选道具的队伍菜单会沿用 1）；子菜单内 `E83==0` 走标准是/否点选。新增 `game/SubmenuState.kt` 与地址（pocket `0x0203AD02`、光标 `0x0203AD04+2*pocket`、队伍光标 `0x0203B0A9`）。
- 背包 >6 件道具的滚动：列表定位改用「滚动偏移 + 可视行」的绝对行（真机标定 `+8/+14` 两组 u16），末行判断也按 abs 变化——修掉「DOWN 只滚窗口不动行」导致的误判/按 A 落在上一件道具。
- 单测 172/172 绿；fresh 复核 2 轮（首轮 2 必修 + delta 2 必修全修）；真机闭验：滚动后点可见第 6 行用掉全复药（HP 35/35、槽位 id 消失）、点「取消」正确合上背包。
- 真机（`build-e3be008`）：`wysiwyg.bagpocket ok=true` 口袋往返 6 次、`bagbar` 空口袋合上/道具说明态只提示、`bagitem ok=true` 取消行合上、`party empty_slot` 空位不按 A、`submenu ok=true kind=party`；截图 `/sdcard/Download/DSH-Go/wysiwyg2-*.jpg`。

## 2026-11-15 横屏 WYSIWYG 补完（功能）
- 对话/战斗「是/否」选项可点选：读 `sMenu` 光标/选项数 + `gWindows` 窗口几何（实测地址），点行 → 回读光标逐行挪到目标 → 二次确认 → 按 A；读不到/光标不到位只提示、不按 A。非标准（3+ 选项/其它布局）选项框不按 A，避免默认确认。
- 战斗主菜单「背包 / 宝可梦 / 逃跑」点选：`E83!=0` 才算真主菜单（`E83=0` 是战斗内是/否选项框）；回读 `MAIN_CURSOR` 逐格挪位 + 按 A + 按项回读 `TURN_FLAG/MAIN_CURSOR`（逃跑看战斗结束/过场）。
- 背包/队伍子菜单点底部条 = 按 B 退出（取消条分区：背包 y≥114、队伍 y≥121），避免横屏被困；`Wysiwyg` 增加取消代际（离开横屏/开设置面板停手）。
- 新增 `game/MenuState.kt`、`Addresses.MENU_STATE/WINDOWS/BATTLE_MENU_FLAG`；单测 `MenuStateTest`/`GameStateTest`/`TouchMapTest` 覆盖。
- 真机（`build-906d43a`）：对话选项 `wysiwyg.dialog ok=true target=1 cursor=1`；背包/宝可梦/逃跑 `wysiwyg.battlemenu ok=true target=1/2/3`；取消条 `wysiwyg.submenu ok=true kind=bag/party`；fresh 复核 3 轮（共 4+2 必修全修）结论「可上线」，`d67eab1` 真机复验通过。

## 2026-11-14 横屏纯画面 + 触屏所见即所得（功能）
- 横屏：整屏铺满游戏画面、隐藏系统栏，只留一个半透明设置图标；点开为**覆盖层**设置面板（速度 / 自动战斗 / 载入 ROM / 更新 / 重置 / 退出）。竖屏保持原双屏 UI 不变。
- 触屏映射（仅横屏，全部 fail-closed 回读）：点 2×2 招式实际位置施放（复用 `BattleMoveAction` 逐格回读 + 二次确认）；点「战斗」回读主菜单光标逐格挪位→按 A→回读 `TURN_FLAG==2`；对话/战斗文字点按=按 A 推进；点地图位置=同图 BFS 走过去（复用 `walkTo`，越界/无地图数据只提示不盲走）。背包/宝可梦/逃跑暂无可靠回读，点按提示「请竖屏」。
- 新增 `ui/TouchMap.kt`（视口逆变换 + 固定热区表 + 镜头锚点 120,80，`TouchMapTest` 覆盖）、`ui/Wysiwyg.kt`（场景分派）、`ui/Landscape.kt`（覆盖层/沉浸/面板）；`EmuView` 固定同一 Composition 位置，旋转不重建 SurfaceView。
- 真机实测（`build-3f36e7a`）：横屏纯画面/面板/战斗菜单截图 `wysiwyg-*.jpg`；点地图 → `wysiwyg.map from=10,10 target=16,12` 且坐标回读一致；点「战斗」→ `wysiwyg.fight ok=true turn=2`；点「抓」→ `battle.move idx=0 ok=true turn_before=2 turn_after=4`；动画期间点按被忽略；转回竖屏 UI 不变。

## 2026-11-14 自动战斗开关（功能）
- 设置页新增「自动战斗」开关：Kotlin 后台循环在战斗中自动选招并施放（`BattleDecider` + `BattleMoveAction`），主菜单/对话短按 A 推进；连续 3 次施放失败自动停止；ROM 载入/重置/退出时静默取消。
- 新增 `game/AutoBattlePlanner.kt`（纯逻辑，单测覆盖）与 `ui/AutoBattle.kt`（线程/状态）；属性克制沿用 354 招式表。

## 2026-11-14 名表 354（数据补全）
- 招式表由 56 条补全为 **354 条**（Gen3 火红/叶绿）：名字取官方中文（PokeAPI zh-hans），威力按 `past_values` 还原 Gen3 数值（如 挖洞 60 / 撞击 35 / 藤鞭 35）。
- 新增数据源 `games/pokemon_firered/data/moves.json` + 生成器 `tools/gen_moves_data.py`（支持 `--check` / `--from-dir` 离线组装）；`pyplatform/bdata.py` 改为读该 JSON；`GameData.kt` 重新生成；新增 Kotlin `MoveTable354Test`。

## 2026-11-14 M4/M5 迁移（无行为变化）
- 根目录 45 个 `.py` 收编 `pyplatform/`（命名避开 stdlib `platform`）；数据目录 `maps/`/`battles/`/`dialogs/` 并入 `games/pokemon_firered/`；`tests/`、`run_tests.py`、`start_push.sh`、`plugin.py`、`terrain.py` 路径同步；Python 测试 31/31 绿。

## 2026-11-14 工作流重设计（无行为变化）
- 流程改为单会话：任务卡 → 实现 → 本地构建/单测 → 真机自测 → 提交/推送；取消 A/B 合同制、审计、成本快照与全套台账。
- 归档旧治理文档到 `docs/archive/2026-11/`；删除治理工具链与 git hooks；Python 旧层冻结。
