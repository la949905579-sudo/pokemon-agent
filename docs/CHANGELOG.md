# CHANGELOG

> 版本规则：功能批一个条目；只记行为/接口变化。旧历史见 `docs/archive/2026-11/history/CHANGELOG.md`。

## 2026-11-14 M4/M5 迁移（无行为变化）
- 根目录 45 个 `.py` 收编 `pyplatform/`（命名避开 stdlib `platform`）；数据目录 `maps/`/`battles/`/`dialogs/` 并入 `games/pokemon_firered/`；`tests/`、`run_tests.py`、`start_push.sh`、`plugin.py`、`terrain.py` 路径同步；Python 测试 31/31 绿。

## 2026-11-14 工作流重设计（无行为变化）
- 流程改为单会话：任务卡 → 实现 → 本地构建/单测 → 真机自测 → 提交/推送；取消 A/B 合同制、审计、成本快照与全套台账。
- 归档旧治理文档到 `docs/archive/2026-11/`；删除治理工具链与 git hooks；Python 旧层冻结。
