# docs/ 目录说明

> 手写约定文件（人读）；**不代替** `docs/FILES.md`（自动索引，勿手改）。
> 分区与生命周期规则自 2026-11-13 起（方案 A）；只约束**新文件**，不追改旧文。

## 一、与 FILES.md 的分工

- `docs/FILES.md`：自动索引——每个已跟踪文件「是什么」；由 `python3 tools/gen_files_index.py` 生成，
  `--check` 为 0 才算同步，**不要手改**。
- 本文件：分区、归属、生命周期、命名、归档规则（手写，人读）。

## 二、分区表（2026-11-13 基线）

| 分区 | 放什么 | 当前文件 | 数量 |
|---|---|---|---|
| 活规范 | 流程 / 标准 / 当前事实 | `TEAM.md` `HANDOVER.md` `STRUCTURE.md` `OBSERVABILITY.md` `AUDIT.md` `NATIVE_EMU_TODO.md` `HANDOFF.md` `PROJECT_PLAN.md` `WORKPLAN.md` `TOOLS.md` `FAQ.md` `PORTING.md` `NATIVE_EMU.md` | 13 |
| 历史快照 | 已发生、只读追溯 | `CHANGELOG.md` `INCIDENTS.md` `AUDIT_LOG.md` `RETROSPECTIVE.md` `ARCHITECTURE.md` `NOTES.md` | 6 |
| 生成物 | 脚本产出、勿手改 | `FILES.md`、`METRICS.md` | 2 |
| 子目录 | 见下 | `roles/` `audit/` `org/` | 18 个文件 |

- 上表为**本次新增前已存在的 39 个文档**（平铺 21 + 子目录 18）分类。
- 本文件（`docs/README.md`）与 `docs/archive/README.md` 为 2026-11-13 新增的**规则文件**，不计入上表。
  当前 `docs/` 共 **41 个 `.md`**：平铺 22（+本文件）+ 子目录 19（`roles/` 7、`audit/` 5、`org/` 6、`archive/` 1）。

子目录职责：

- `docs/roles/`：7 张角色卡——A 队 `steward` / `artisan` / `examiner`、第三方 `architect`、B 队 `audit-lead` / `audit-cost` / `auditor`。
- `docs/audit/`：B 队（独立督导）专属——`TEAM.md` 手册、`ACTIONS.md` 活清单、`REQUEST.md` 请求、`REPORT-*` / `COST-*` 历史。
- `docs/org/`：组织规划接口——统筹主持写 `REQUEST.md`，组织规划写 `PLAN-<YYYYMMDD>.md`（同日多份加 `-2`、`-3`）。

## 三、新文件头元数据约定（只对新文件生效）

新文件首段加一行（按实际三选一，示例）：

```
> 归属：A 队 ｜ 生命周期：活 ｜ 维护者：执行主管
> 归属：独立督导 ｜ 生命周期：历史 ｜ 维护者：独立督导
> 归属：组织规划 ｜ 生命周期：生成 ｜ 维护者：执行主管（脚本生成）
```

- 归属：A 队 / 独立督导 / 组织规划
- 生命周期：活 / 历史 / 生成
- 维护者：实际写的人（用职位名，不用英文实例名）
- 旧文件不追改（历史不回改）。

## 四、命名约定

- 职位一律用中文名：**统筹主持 / 独立督导 / 组织规划 / 策略顾问**；英文实例名只出现在 `spawn_teammate` 与 `send_message`。
- 两本手册互指：`docs/TEAM.md`（A 队）↔ `docs/audit/TEAM.md`（B 队），别混读。
- 历史文件名带日期：`REPORT-YYYYMMDD.md`、`COST-YYYYMMDD.md`、`PLAN-YYYYMMDD.md`。

## 五、归档规则

- 新结案件（`PLAN-*` / `REPORT-*` / `COST-*` 及同类）满 **30 天**，或同一主题满 **3 份** → 移入 `docs/archive/`。
- 本期只立规则与空目录（`docs/archive/README.md`），**先不搬**；搬动由组织规划提案、执行主管执行。
- 归档只移动文件、不改正文（历史不回改）。

## 六、新增 / 移动文件后的动作

1. 跑 `python3 tools/gen_files_index.py`；`--check` 必须为 0（有未描述文件即红）。
2. 改 `STRUCTURE.md` / `WORKPLAN.md` 仍需主持确认（前者影响重构实施，后者是历史追溯）。
3. 生成物（`FILES.md`、`METRICS.md`）不得手改，只重跑脚本。

## 七、本轮边界（方案 A）

- 不搬任何现有文件、不改旧文。
- `docs/roles/` 按队拆分（P1）、审查件归并（P2，需独立督导同意）待后续排期。
- 代码侧结构不归本文件管，见 `docs/STRUCTURE.md`。
