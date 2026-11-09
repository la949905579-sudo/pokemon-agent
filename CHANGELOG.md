# CHANGELOG

版本规则：日期版 `YYYY.MM.DD-N`，git tag 为 `vYYYY.MM.DD-N`。
只记录**行为/接口变化**；重构细节看 commit。commit 前缀：`feat:` / `fix:` / `refactor:` / `docs:` / `test:`。

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
