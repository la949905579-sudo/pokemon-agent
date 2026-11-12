# CHANGELOG

版本规则：日期版 `YYYY.MM.DD-N`，git tag 为 `vYYYY.MM.DD-N`。
只记录**行为/接口变化**；重构细节看 commit。commit 前缀：`feat:` / `fix:` / `refactor:` / `docs:` / `test:`。

## v2026.11.12-3（NativeEmu v0.4.1）
### 新增
- 存档改成 3 个卡槽（`state1-3.sav`），显示保存时间，支持存档/读取/删除
- 覆盖、读取、删除都有 3 秒二次确认，避免误触丢进度

### 变更
- `MainActivity.kt` 拆分：963 → 536 行，界面代码移到 `ui/`（KeyPad/BattlePage/MapPage/Tabs/Pages/Theme/SaveSlots）
- 纯搬移，无行为变更；单测 47 → 52（新增存档槽位用例）；截至 2026-11-12 累计 **57**

### 修复
- 下屏内容区底部新增临时状态行（2.8 秒自动消失）：`statusText` 此前只写不读，所有提示用户看不到（INC-006）

### 新增
- 设置页加「重置」（软复位回游戏标题，存档保留）与「退出」（停服务、刷电池存档、退进程）

## v2026.11.12-2（NativeEmu v0.4）
### 新增
- 下屏底部常驻「按键」折叠条（点击开合/下滑收起），战斗中也可见；按键面板是唯一入口
- 常驻页：当前地图（15×9 中心视口，玩家居中）与战斗页按场景自动切换
- 「地图」Tab 改为整张城镇/道路图（点格子仍可前往），与「当前地图」是两个组件
- 队伍详情：属性、4 招式 PP、经验与升级进度条（成长类型优先从 ROM BaseStats 读）
- 13 张地图数据打包进 APK assets，不再依赖 Python 推送

### 修复
- 战斗页出现后按键打不开（切页逻辑抢页）
- 切 Tab / 载入 ROM 时按键掩码未清，角色可能持续移动
- 地图碰撞语义反了（JSON 里 0 才是可走，统一归一化成 1=可走）
- OTA 更新说明被截成一行（现在最多 8 行、可滚动）

## v2026.11.12-1（NativeEmu v0.3）
### 新增
- 下屏改为「左侧内容 + 右侧竖排 Tab」（地图/队伍/背包/名字/图鉴/存档/设置/按键）
- 队伍显示宝可梦中文名（关东 151 名表 + PortablePokemon 解密）
- 敌方等级/HP/最大 HP 读取
- 按键布局 A：L/R 肩键 + 方向键 + A/B + Start/Select 重排
- 加速 1x/2x/4x
- OTA 下载进度条 + APK 校验 + 安装权限引导
- 小地图缺省沿用上次推送数据（Kotlin 侧尚未解析 `maps/*.json`）
- 小地图点击前往：同图 BFS 寻路（`MapWalker`）+ 真按键（180ms/步），带 Kotlin 单测
- OTA 结构化日志：检查/下载进度/校验 sha/安装失败写入 `/sdcard/Download/ota.log`
- 签名改为 CI secret 注入，密钥库不再进仓库（并轮换了密钥）
- CI 构建成功自动发 Release（`build-<sha>`），不再需要个人 token

### 修复
- 战斗页自动切换：动画/击败对话框阶段不再跳回地图（battle_anim + 4 秒滞回）
- 队伍详情改为下屏内容区（不弹窗遮挡）
- 切换 Tab 时下载中断（状态提到 Activity）
- 更新日志只显示一行（改多行）
- 载入 ROM 移到设置页
- 构建失败时发布脚本误发旧包（加成功校验）
- CI 编译失败：`KeyPadArea` 残留重复的旧按键布局块（多一个右花括号）；补 `detectTapGestures` import

## v2026.11.11-1（NativeEmu v0.2）
### 新增
- 原生双屏 GBA 模拟器（mGBA 内核 + Kotlin/Compose + NDK）
- 下屏控制台：小地图 / 六宫格菜单 / 日志 / 按键页
- TCP 桥 `:55401`（read/write/press/frame/status），Python 侧 `emu_bridge.py`
- `memory.py` / `ra.py` 支持 `EMU_BACKEND=native` 切换
- 前台保活 + WakeLock；固定签名 + App 内 OTA 更新

### 修复
- mGBA 初始化顺序、编译宏不一致（结构体布局）、无 BIOS 时 `skipBios`
- 像素 ABGR→ARGB、帧率统计、多指按键 `ACTION_POINTER_UP`
- 存档 API 参数类型（内存缓冲区 vs VFile）
- 重新加载 ROM 被 `if (core_) return true` 拦截

## v2026.11.10-15（2026-11-10）
### 修复
- 固定跨图路线遇到 NPC 对话时直接走、导致整条路线失败（现在按 B 关对话后重试）

### 新增
- `travel_map` 自动跨通道：6号 ↔ 5号/华蓝，先走实测固定路线再 A*

### 验证
- 5号道路 -> 华蓝市：**11.4s**，ok
- 6号道路 -> 5号道路：**48.6s**（含 1 场战斗），ok

### 遗留
- 华蓝市内到道馆入口 (31,22) 的 goto 失败：BFS 有路（26 步），实走被挡，疑似小树苗/NPC，需单独排查

## v2026.11.10-14（2026-11-10）
### 变更
- 换人评分切换 **v2**：预计击杀回合差 + 敌方实际招式（`enemy_info` 新增 `moves`）
- 开场换人加**等级压制**：敌方比我方低 8 级以上不换

### 修复
- `enemy_info` 读敌方招式的地址错误（`ENEMY_BASE` → `ENEMY_SPECIES + 0x0C`）

### 验证
- 实机 2 场：无开场换人（敌 Lv15 vs 我 Lv29），3 回合 3 一致，0 槽位不同步

## v2026.11.10-13（2026-11-10）
### 变更
- 出场槽位：species 驱动；`party_order()` 由 active 推导（不再维护第二份状态）
- 换人目标改为 **species 身份**定位（菜单打开前后数组顺序会变）
- 换人成功判据改为「场上 species 变成目标」，不再只看 `turn==4`

### 修复
- 换人光标错位：队伍菜单内数组 = 界面顺序，主菜单数组 = 原始顺序，两套下标不能混用

### 验证
- 实机：active=喇叭芽时换大针蜂，`pos=4`、`ok=True`、`field species=15`

## v2026.11.10-12（2026-11-10）
### 新增（阶段 A：观测埋点，不改行为）
- `battle/start`、`battle/end` 日志：场次统计不再靠推断
- 换人评分 v2 影子观测：`score_shadow` 只写日志（回合差 + 敌方实际招式）
- `pathfind/goto`、`pathfind/travel` 计时日志（ms）

### 验证
- 实机：`geto 1 格 1379ms`、`score_shadow active=1 v2=[...]` 均正常

## v2026.11.10-11（2026-11-10）
### 修复
- NPC 挡路导致寻路失败：连续撞同一格 3 次时，临时记 60s 障碍并绕行（原来直接放弃）

### 实测
- 精灵中心门口 -> 6 号道路草地：**23.9s**（6.9s 出门 + 17s 到草地，含 NPC 绕行）
- 不含战斗时间（回程遇 1 战，额外约 100s）

## v2026.11.10-10（2026-11-10）
### 新增
- `map_route.py`：跨图 A*（连接表 + 全局坐标启发），支持规划与执行
- 复用房间（车站/通道）自动回退到实测固定路线
- `test_map_route.py`：同图/单段/复用边标记/无路/回退表

### 验证
- 实机 `travel_map(6号 -> 枯叶)`：`(14,31) -> (15,8)` 返回 ok

### 已知限制
- 多段且经过复用房间的路线（如 枯叶 -> 华蓝）仍需手动分段：先到 6 号 -> `route_6_to_5` -> 再 A*
- 连接表里通道/车站的边不完整，A* 可能选中不可走的 reused 边

## v2026.11.10-9（2026-11-10）
### 变更
- 坐标语义统一：新增 `state.to_tile()` / `to_raw()`，对外一律用**地块坐标**
- 障碍学习加 TTL（600 秒）+ **NPC 不记为墙**
- 到达判定二次复核（防坐标抖动/换图瞬态误判）
- 合并两套寻路入口：删除 `nav.goto`，`encounter` 统一走 `pathfind.goto`

### 验证
- 实机短程 `goto`：`(12,31) -> (14,31)` 返回 True，坐标复核通过

## v2026.11.10-8（2026-11-10）
### 新增
- `no_kill` 增加「压血」模式（`move_mode=chip`）：预估不会击杀时用低伤招，临界血自动退回变化招
- 测试 `test_intent` K/L

### 验证
- AI 注入 `no_kill` → 1 回合 win，`intent_rounds={'no_kill': 1}`

## v2026.11.10-7（2026-11-10）
### 新增
- `ai_agent.py`：最小 AI 闭环（观察 `/api/state` → 注入指令 → 触发 `/api/task farm` → 回读）
- `/api/intent` 返回 `last_battle`（rounds / match / intent_rounds）

### 验证
- AI 注入 `prolong` → 战斗 2 回合，`intent_rounds={'prolong': 2}`，回读 `win`

## v2026.11.10-6（2026-11-10）
### 新增
- 跨进程指令存储 `FileStore`（`logs/intent.json` + 排他锁）
- `api_server` / `farm` / `train` 入口自动启用文件 store

### 验证
- API 注入 `prolong` → 另一个进程 `active()` 能读到并编译成约束

## v2026.11.10-5（2026-11-10）
### 变更
- 指令改为**注册制编译**：`kind -> compile -> Constraints`
- 决策层与主循环只消费约束，不再判断 `kind`
- 新增指令 = `register_kind` + 一个 compile 函数（`test_intent` J 验收）

## v2026.11.10-4（2026-11-10）
### 新增
- 统一日志：`logs/run-YYYYMMDD.jsonl`（JSONL 单流）+ `logq.py` 查询
- 回合观测带 `party` 全队快照；换人日志带 `order_before/after`

### 变更
- 学招事件不再写 `learn_event.txt`，进统一日志
- `probe/round` 摘要进主日志（完整数据仍在 `rounds-*.jsonl`）

## v2026.11.10-3（2026-11-10）
### 修复
- `learn.py` 迁移后缺失 `snapshot` / `advance_dialog` 等依赖（实机两次暴露）
- 补 `test_learn.py` 四个分支测试

### 验证
- 实测普通换人**不改**真实队伍数组 `0x02024284`；`active_slot()` species 驱动正常

## v2026.11.10-2（2026-11-10）
### 变更
- 学招逻辑 `learn_moves_guard` 从 `action.py` 迁出到 `learn.py`（执行层只留按键/光标）
- 常量统一：`MOVE_CURSOR / PARTY_CURSOR / MAIN_CURSOR` 只从 `addresses.py` 引用
- 解除 `action ↔ switch` 循环依赖（action 不再引用 switch/learn，依赖变单向）

### 修复
- `learn.py` 缺失 `snapshot` 导入（迁移后实机验证发现）

## v2026.11.10-1（2026-11-10）
### 新增
- 指令层 `intent`：`prolong` / `no_kill` / `flee` / `only_class`，含生命周期、优先级、安全护栏、审计
- HTTP 指令接口：`POST/GET /api/intent`、`POST /api/intent/clear`
- `no_kill`：敌方低血且当前无变化招时换队友拖延（每场上限 2 次）
- `probe.summary()` 增加 `intent_rounds`

## v2026.11.09-1（2026-11-09）
### 新增
- 初始化：信息层 / 决策层 / 执行层 + 日志 + 离线测试
- 出招内存：我方/敌方 BattlePokemon `0x02023BE4` / `0x02023C3C`，`+0x0C` = 4 招
- `0x02023D4C`（最近行动招式）/ `0x02023DC4`（我方本回合招式）
- 可观测性：`battle_loop(on_round=...)`、`probe.Recorder`、`train.py`
- `farm.py` 自动练级（场数/目标等级/时限/血线）
- 敌方威胁评估（仅写日志，未接入决策）
- 20+ 离线测试：场景矩阵 A–J、指令 A–N、数据防错

### 修复
- 束缚误判：`+0x22` 只认 bit8（0x100）；实测 1037 时换人正常
- 无攻击招卡死：新增 `has_attack_move()`，自动换一只能打的
- 招式表 3 处：`28` 撒沙、`35` 缠绕、`56` 水炮 120、`145` 泡沫 20；补 `10/16/79/91`
- `test_travel` 偶发失败（改读地图 header 导致的实机依赖）

### 变更
- 出场槽位改为 **species 驱动**（`0x02023BE4` 为唯一依据，order 只作兜底）
- `battle_loop` 超时兜底：退菜单，必要时逃跑

### 移除
- `train_probe.py` 归档到 `legacy/`（由 `train.py` 替代）
