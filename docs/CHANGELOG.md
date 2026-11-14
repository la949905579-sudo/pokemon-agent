# CHANGELOG

> 版本规则：功能批一个条目；只记行为/接口变化。旧历史见 `docs/archive/2026-11/history/CHANGELOG.md`。

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
