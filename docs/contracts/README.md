# 合同制试点目录（docs/contracts）

> 归属：A 队 ｜ 生命周期：活（试点期） ｜ 维护者：助理
> 2026-11-13 用户确认试点（A=代理人 / B=承包主持，共 2 个合同）；授权范围见 `docs/BATCHES.md` 试点落盘行。

## 目的

只在**本期 2 个试点批次**（C1 机械型、C2 功能型）内使用合同制；不做通用文档区，试点结束即归档或回滚。

## 目录约定

- 合同 spec 入仓库：`docs/contracts/C<编号>-<slug>.md`（只读口径，B 按合同执行）。
- 运行态不入库：`.pilot/<id>/`（`status.json`、`result.md`、成本快照），已在 `.gitignore` 忽略。
- 命名：`C<编号>-<slug>.md`；编号从 1 递增，slug 用英文短横线词。

## 状态机

`open → claimed → green | blocked → accepted`，每次流转写 `.pilot/<id>/status.json`：
`{"id":"C1","state":"claimed","by":"B","base":"<git rev-parse HEAD>","at":"2026-11-13 18:00"}`；只追加不改史，A 验收后置 `accepted`。

## 谁写什么

| 角色 | 写什么 | 不写什么 |
|---|---|---|
| A（代理人） | 合同 spec、验收结论 | 实现、回执正文 |
| B（承包主持） | `.pilot/<id>/result.md` 回执（含证据路径） | 合同口径 / 写入范围 |
| 助理 | 机械门禁与提交（按 B 批） | 不判定质量 |

- 回执 ≤10 行：状态 / 提交号 / 产物路径 / 门禁 / 风险 / 待确认；首行附 session id（成本归因）。
- 合同模板见 `CONTRACT-TEMPLATE.md`；合同只约束本批，变更须双方书面同意并留痕。
