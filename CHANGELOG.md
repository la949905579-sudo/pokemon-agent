# CHANGELOG

版本规则：日期版 `YYYY.MM.DD-N`，git tag 为 `vYYYY.MM.DD-N`。
只记录**行为/接口变化**；重构细节看 commit。commit 前缀：`feat:` / `fix:` / `refactor:` / `docs:` / `test:`。

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
