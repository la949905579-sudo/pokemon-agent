# TASKS（任务队列）

> 规则：每任务 3 行卡（目标 / 验收 / 范围）；同一时间只一个 `doing`；完成后标 `done` 并写一行结果。
> 当前状态（2026-11-16）：**模式已固化**；无进行中任务；**地图 M2 全部完成**（M2-A/B/C/D，最新 `build-78ad2cf`，App 0.2 versionCode 186）；Kotlin 197/197、Python 33/33；下一步候选：非标准选项框、镜头贴边、联机、结构债。

## doing
（无）

## todo（按优先级）
1. **非标准选项框（3+ 选项）支持**：现在只认标准「是/否」框（21,9,6,4），其它选项框只提示、不按键。
2. **镜头贴地图边时的锚点偏移标定**：纯真机标定，改 `TouchMap` 常量 + 单测，低风险。
3. **联机**：GBA link cable，方案调研。
4. **结构债**（随触碰模块顺手做，不单开）：`EmuView`/`WalkControl` 零散逻辑继续迁出；WYSIWYG 小清理（`Wysiwyg` KDoc 的 `[cancel]`→`[cancelAll]`、`MenuState.insideWindow` 去留、`Landscape` 重置里与 `cancelAll` 重复的 `WalkControl.generation++`）。

## 候补补充（未排期，待用户拍板；2026-11-16 交接时按实际踩坑整理）
- **Nlog 单测污染设备日志**：跑 Kotlin 单测会写 `/sdcard/Download/emu_native.log`（可见 `map.fallback addr=0x8260000` 等测试痕迹）。建议非 Android 环境不落盘。
- **CI 只跑了 gradle**：没有 `python3 run_tests.py`、`gen_map_assets --check`，资产/生成器易漂移；建议加进 workflow。
- **`run_tests.py` 按文件计数**：`33/33` 是测试文件数（不是用例数），加用例数字不变；建议改按用例计数或改文案。
- **后台屏实例/桥绑错实例**：`open background` 可能新开空载实例、桥仍连旧实例；建议 app singleTask 或测试脚本先 force-stop，桥加版本/帧数握手。
- **跨图遇敌即中断**：walker 遇野生战 STUCK 停；建议「遇敌→自动战斗→继续原计划」或按相遇风险避草。
- **跨图 UI 只列相邻图**：库已支持多跳，可加 ≤3 跳目的地列表（带跳数/步数）。
- **换图落点补齐 ≤2 步**：门口被 NPC 挡会 fail；建议提示失败原因并重规划。
- **地图页信息**：建议显示当前地图名（`to_name`）、遭遇概率、地形图例；「地图」Tab 仍置灰是否恢复待拍板。
- **自动战斗健壮性**：遇到过 `main_not_moves`、turn=4 长卡；补双打/换人/学招/战斗结束对话状态。
- **代码/仓库卫生**：`LocalStatus`/`CrossWalkAction` 无单测（可抽纯函数）；`CurrentMapPage` 死代码；assets 里 2 个 `override_*.json` App 不读；根 `map_links.json`+`games/pokemon_firered/maps` 11 张旧图已与 assets（365 图/3784 出口）不同步，建议标「实测样本」归档。
- **资产体积**：365 图 3.7MB、APK ~12MB；`behaviors` 2 hex/格可压成 1 byte 类别或 zlib（可选）。

## 暂缓
- （无）地图功能已于 2026-11-16 由用户批准解冻（先做数据接入，M1 完成；M2 见 todo 1）。

## done
- 2026-11-16 **地图 M2-D：struct-multi 布局地址消歧（⑤）**：新增 `find_layout_table`——按解包 `layouts.json` 顺序在 ROM 里定位 `gMapLayouts` 表（383 项），整表校验（空项=0、其余指针指向宽高完全一致的布局结构体）；`locate_all` 表优先：布局 → 结构体 → +0xC map 指针，地址唯一。修复原先 27 个 struct-multi 布局取第一个候选的错配（其中 20 个布局在游戏里的真实地址没有资产 → 运行期 fallback 读内存）。表找不到时仍退回旧启发式（假 ROM 单测覆盖）。
  - 数据：365 布局 → **365 个唯一地址**（0 歧义、0 缺失、无孤儿地址）；地图资产 345 → **365**；`map_links` 同步重生成 → **3784 出口**；实测表校验仍 12/13。
  - 单测：Python 33/33（新增 gMapLayouts 表整表校验 + 重复内容消歧 JSON 用例）、Kotlin 197/197。
  - 真机（`build-78ad2cf`，App 0.2 versionCode 186）：`map.assets ok=true indexed=365`、`map.links ok=true count=3784`、装机后无新增 `map.fallback`。
- 2026-11-16 **地图 M2-C：门/楼梯坐标口径校准（③ 数据层）**：`gen_map_assets` 默认把解包 `warp_events` 生成进 `map_links`（`side=null`：exit=解包触发格、落点=目标图同一 warp 坐标），不再用 `--merge-old` 补测门（差 1 格的测量口径会造错边）；`--with-doors` 改为 `--no-doors`；`--validate` 改按落点匹配、exit 容差 1 格单列。link 增加 `to_name`（解包目标地图 id），同布局多图共用资产（17 个宝可梦中心）也能显示正确城市；`CrossMapWalker` 换图等待支持门淡入（最多再等 3×800ms）。
  - 数据：连接 4033 边（门/楼梯 1275）→ 3751 出口（原 2769）；实测表 **12/13** 命中（4 条 exit 差 1 格 + 1 条落点属测量口径，已记录）。
  - 单测 Kotlin **197/197**、Python 33/33（新增：门边生成、容差校验、换图延迟×2、to_name 解析/优先、楼层命名）。
  - 装机 `build-b6ae868`（App 0.2 versionCode 185）；**真机门验证通过**：Viridian (0x82dd4c4) 站 (26,27) 按上踩门格 (26,26) → 地图 0x82d5844（PC 1F）、落点 (7,8)，与生成链接/解包 dest warp 一致；反向 (7,8) 按上 → Viridian (26,27)；App 日志 `map.terrain addr=0x82d5844 w=15 h=10 stairs=2 maps=17`。证据 `/sdcard/Download/DSH-Go/map-m2c-door-20261116.txt`。未跑：App 跨图 UI 点门目标的全链路（后台屏/主屏切换后实例不同步；walker 侧门逻辑有单测）。
- 2026-11-16 **地图 M2-B：跨图寻路 UI 入口（②）**：地图页底部「跨图 →」列出 `map_links` 相邻地图（按目标图去重、地图 id 友好名 MAP_ROUTE1→Route1），点选后后台 A*（新 `planToMap`：目标=目标图任意格、落点由搜索决定）→ 预览「去 X · N 段 M 步」→「开始走」由 `CrossMapWalker` 真按键走完（换图地图/落点校验，失败/取消 fail-closed 只提示）。
  - 新增 `game/CrossMapRoute.kt`、`ui/CrossWalkAction.kt`（Io 接线：读地图/坐标、按键、可中断 sleep、清键）；与同图行走共用取消代际；点格子预览/换 Tab/收面板都会作废跨图预览。
  - 真机实测发现并修复：换图瞬间玩家停在目标图边行（实测 Viridian y=39），链接表落点 y=37（持续按住走进去的落点）→ walker 先 WARP_MISMATCH 误失败；改为换图地图校验通过后沿换图方向补按最多 2 步到记录落点（`WARP_CATCHUP_LIMIT`），到不了才失败。
  - 单测 Kotlin **194/194**（+8：planToMap 3、邻图去重/命名 4、落点补齐 1）、Python 33/33。
  - 真机（`build-27c0752`，App 0.2 versionCode 184）：地图页出「跨图 → Route1/Route2/Route22」→ 点 ViridianCity 出「去 ViridianCity · 2 段 19 步」→ 开始走 → `crosswalk.result ok=true steps=22 reason=ok`，落点 (25,37) 与链接一致、地图 water=30/遭遇切到 Viridian；取消只清预览不移动（(25,37) 原地）。截图 `/sdcard/Download/DSH-Go/map-m2b-20261116.jpg`（Viridian 水面蓝色+遭遇+跨图按钮）、日志 `map-m2b-log-20261116.txt`。
  - 未真机验：多跳（>2 图）路线、side=null 的门换图、NPC 挡路/野生战中断（walker 会 STUCK 停，属预期 fail-closed）。
- 2026-11-16 **地图 M2-A：地形行为接入 + 地图页遭遇展示（①+④ 合并）**：`tools/gen_map_assets.py` 每图输出 `behaviors`（2 hex/格，布局 tileset 的 metatile 属性表）与 `maps`（地图 id 列表），并把 `encounters_leafgreen.json` 拷进 assets（345 图 / 124 张遭遇图；同址多布局行为取首布局，0 冲突）。App 侧 `MapData` 把行为归一成地形分类（0 挡/1 走/2 水/3 草/4 台阶），tiles 改为「步行可走」——按引擎 `sBehaviorSurfable` 表（16-19/21/26/27 + 水流 80-83）把水面判挡；`MB_SHALLOW_WATER(23)` 是可走浅水流、不挡（fresh 复核必修项，已对照 `metatile_behavior.c` 修正）；地图页/常驻图按地形着色，地图页底部一行遭遇（陆/水/碎岩/钓，种 + Lv 区间，横向滚动）。
  - 单测 **Kotlin 186/186**（+14：行为→地形/水挡/hex 解析/parseJson 端到端/遭遇摘要/状态解析）、Python 33/33；`--check` 扩展 behaviors/maps/遭遇表校验；345 资产 tiles 与旧版逐格一致、`map_links.json` 字节一致、Route1 行为网格与解包 `maps_decomp` 一致。
  - 真机（`build-5931f4a`，App 0.2 versionCode 182）：`map.assets indexed=345`、`map.terrain addr=0x82e4e2c w=24 h=40 water=0 grass=178 stairs=0`、`map.encounters ... text=陆 波波2-5/小拉达2-4`、新会话 0 fallback；截图 `/sdcard/Download/DSH-Go/map-m2a-20261116.jpg`（像素抽查命中 可走/草/挡 三色）；日志摘录 `map-m2a-log-20261116.txt`。
  - 未真机验：水面格点按提示（当前只读档在地图 Route1 无水域；水面判定有单测 + 引擎源码对照）；地图页「点格子预览」仍靠用户点画布（tap_xy 受限）。
- 2026-11-16 **地图功能接入 M1：全量资产 + 跨图连接表**：新增 `tools/gen_map_assets.py`——把解包 `map.bin` 字节在 ROM 里按内容反查地址（用布局结构体 + border 校验消歧：337 struct / 27 struct-multi / 1 raw / 0 missing），生成 **345 个** `assets/maps/map_<addr>.json`（365 布局，同内容共址）；用解包 `connections` 按实测规则算出口/落点（南北 exit 在边行、落点 y=2 / nh-3，东西同理，坐标平移 -offset）→ **2769 个出口（65 张有连接的图，3 处多目标）**；门坐标口径与实测差 1 格，默认合并实测 11 条（`--merge-old`）。
  - 交叉校验：现有 13 条真机走位记录 **13/13 命中**（3 条 side 口径不同）；旧 11 张资产 tiles 与重生成逐格一致。
  - `MapData` 改懒加载（启动只列目录，用到才解析；`map.assets indexed=345`），避免 345 文件主线程解析。
  - 单测：Kotlin 172/172、Python 33/33（新增 `tests/test_map_assets.py`：ROM 地址定位/连接规则/多目标合并/实测校验/资产 schema）。
  - 真机（`build-44e9b60`，版本 0.2 (44e9b60)）：日志 `map.assets indexed=345`、`map.links count=2769`、新会话 **0 条 `map.fallback`**（同一张 24×40 图在旧包曾回退读内存）；地图页正常渲染当前图 + 玩家点，截图 `/sdcard/Download/DSH-Go/map-assets-newsession-20261116.jpg`。
  - 未做（M2+）：跨图寻路 UI 入口（`CrossMapWalker` 仍未接线）、门/楼梯坐标口径校准（解包与实测差 1 格）、行为/遭遇在地图页展示、27 个 struct-multi 布局的地址消歧。
- 2026-11-16 **离线地图数据提取（小步：3 张图校验）**：新增 `tools/gen_maps_data.py`——读 pokefirered 解包 `layouts.json`/`map.bin` 的碰撞位（bits 10-11）生成可走格 JSON（`w/h/tiles` + `connections`/`warps` + `ram_crosscheck`），支持 `--match`（真机 RAM 地图 × 解包布局逐格比对）/ `--emit` / `--check`（离线自检）。
  - 真机交叉校验 **11/11 张现有 RAM 地图 diff=0**（含 48×40 三城/路、24×40、72×20、小室内图）→ 汉化版这些图与香草解包碰撞位完全一致；`DIGLETTS_CAVE` 南北入口布局同形（同尺寸另有 1 个 diff=0，标记歧义）。
  - **全量已出**：`--emit-all` 生成解包 maps 表全部 **425 张** → `games/pokemon_firered/maps_decomp/`（2.7MB，文件名=地图名；`--check` 425 个文件 PASS，含尺寸/layout/0-1/连接/传送字段校验）。室内图的 `connections` 在解包里是 null，统一归一成 `[]`。
  - 真机交叉校验 34 张布局与 RAM 数据 diff=0（11 张真机地图对应到的解包布局及共用同一布局的城/中心）；`--match` 11/11 diff=0。
  - 抽样：PalletTown 24×20 可走 59%、Route1 24×40 62%、Route5 48×40 26%、CeruleanCity 48×40 54%（连接 4 / 传送点 14）。
  - **行为语义 + 遭遇表已补**（第二轮）：
    - 每图新增 `behaviors`（每格 2 位十六进制行为 id，名字见 `games/pokemon_firered/data/metatile_behaviors.json`，111 个 `MB_*`）：走 `src/data/tilesets/metatiles.h` → 各 tileset `metatile_attributes.bin`（u32/个，behavior=bits0-8；primary 640、secondary 640..1023）。425 张里 **84 种行为被用到、0 个越界未知**；抽样符合预期（Route1 高草 0x02、台阶 0x3b、海路 Route19 0x15 海洋水、MtMoon 0x08 洞穴）。
    - `games/pokemon_firered/data/encounters_leafgreen.json`（208KB，132 张有遭遇的图）：从 `src/data/wild_encounters.json` 只取 `_LeafGreen` 版本（叶绿），含 land/water/rock_smash/fishing（old/good/super rod 分组）的物种 id、等级区间、槽位概率（来自 fields.encounter_rates）与可选 per-map `rate`；物种常量解析支持 `(NUM_SPECIES + n)` 表达式。
    - `--emit-all` 现在一次写地图 + 行为名表 + 遭遇表；`--check` 校验全部（含 behaviors 网格格式、图例、遭遇表结构）。`maps_decomp` 共 **3.2MB**（425 张 + behaviors）。
  - `--check` 可带 `--ref` 按解包 maps/layouts 校验尺寸与 layout；不带则只做自洽校验。Python 单测 32/32（`tests/test_maps_data.py` 用临时解包树，不依赖 /root/refs，含行为/遭遇/叶绿分支用例）。
  - 未做：海拔、地形/遭遇类型位（attribute 里 bits9+）、门/传送与行为联动、动态 NPC/剧情、地图 UI/寻路接入（地图功能仍暂缓）。
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
