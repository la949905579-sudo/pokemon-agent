# 合同制目录（docs/contracts）

> 归属：A 队 ｜ 生命周期：活 ｜ 维护者：代理人（`proxy`）
> 2026-11-14 转常设（试点 C1/C2 已 accepted）；规则唯一真源见 `docs/TEAM.md` §三·十，本文件只写目录约定与校验用法。

## 用途

合同制常设：A（`proxy`，代理人）写合同与验收，B（`contractor`，承包主持）只读合同执行；一个合同 = 1 批（≤1 天）。

## 目录约定

- 合同 spec 入仓库：`docs/contracts/C<编号>-<slug>.md`（只读口径，B 按合同执行）。
- 运行态不入库：`.pilot/<id>/`（`status.json`、`result.md`、成本快照），已在 `.gitignore` 忽略。
- 命名：`C<编号>-<slug>.md`；编号从 1 递增，slug 用英文短横线词。
- `CONTRACT-TEMPLATE.md` 模板；`PILOT.md` 为试点记录（保留，不再作为现行规则）。

## 状态机

`open → claimed → green | blocked → accepted`，每次流转写 `.pilot/<id>/status.json`：
`{"id":"C1","state":"claimed","by":"B","base":"<git rev-parse HEAD>","claimedAt":"...","commit":"...","session":"...","accepted":{...}}`。
必填：`base`（开工前 HEAD）、`claimedAt`、`commit`、`session`；accepted 时加 `accepted`（验收记录，**必含 `by` / `verdict`**，`at` 建议）。

## 校验（提交前）

```bash
python3 tools/contract_check.py --contract docs/contracts/C1-tests-consolidation.md --status .pilot/C1/status.json
```

校验：必填标题、合同 ≤60 行、status 字段 / 状态机、`base` 是合法提交、`result.md` ≤10 行、accepted 记录须含 `by` / `verdict`、accepted 时 `BATCHES` 含 `合同:<id>` 且 `git diff --name-only <base>..<commit>` 落在合同 §8 写入范围（豁免 `.pilot/**`）；全部通过 exit 0。

## 谁写什么

| 角色 | 写什么 | 不写什么 |
|---|---|---|
| A（`proxy`，代理人） | 合同 spec、验收结论 | 实现、回执正文 |
| B（`contractor`，承包主持） | `.pilot/<id>/result.md` 回执（含证据路径）、`status.json` | 合同口径 / 写入范围 |
| B 侧助理 | 机械门禁与提交、`BATCHES` 行、`test_results`、`FILES` | 不判定质量 |

- 回执 ≤10 行：状态 / 提交号 / 产物路径 / 门禁 / 风险 / 待确认；首行附 session id（成本归因）。
- 每批必带：`BATCHES` 行（备注 `合同:<id>`）+ `test_results` 同步 + `FILES` 重生成；`HANDOFF` 在批次收尾 / 交接前更新，不要求每批改。
- 合同只约束本批；变更须 A 书面同意并留痕。
