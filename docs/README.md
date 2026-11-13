# docs/ 目录说明

> 手写规则文件；**自动索引见 `docs/generated/FILES.md`**（勿手改，脚本生成）。
> 2026-11-13 重建版：采用 B 档（`history/` + `generated/` 物理分区）。

## 一、与自动索引的分工

- `docs/generated/FILES.md`：自动清单——每个已跟踪文件「是什么」；由 `python3 tools/gen_files_index.py` 生成，`--check`=0 才算同步，**不要手改**。
- `docs/generated/METRICS.md`：自动度量，由 `tools/metrics.py` 生成，**不要手改**。
- 本文件：分区、归属、生命周期、命名、归档规则（手写、人读）。

## 二、分区（目标结构 + 当前状态）

| 分区 | 放什么 | 状态 |
|---|---|---|
| 顶层活规范 | `TEAM` `HANDOVER` `BATCHES` `STRUCTURE` `OBSERVABILITY` `NATIVE_EMU_TODO` `HANDOFF` `PROJECT_PLAN` `WORKPLAN` `TOOLS` `FAQ` `PORTING` `NATIVE_EMU` | 已就位 |
| `history/` | `CHANGELOG` `INCIDENTS` `RETROSPECTIVE` `NOTES` `ARCHITECTURE` | 已就位（M1，本批迁移） |
| `generated/` | `FILES` `METRICS` | 已就位（M1，本批迁移） |
| `roles/` | `a/`（A 队）、`org/`（第三方）、`b/`（B 队）+ `README.md` 索引 | 已就位（`b/` 三卡已迁入） |
| `contracts/` | 合同制（2026-11-14 转常设）：合同 spec `C<id>-<slug>.md`、`README`、`CONTRACT-TEMPLATE`、`PILOT`；运行态 `.pilot/` 不入库 | 已就位（C1/C2 试点 accepted，规则见 `TEAM` §三·十） |
| `audit/` | B 队专属：`TEAM` `ACTIONS` `REQUEST` `REPORT-*` `COST-*`、`AUDIT`、`AUDIT_LOG` | 已就位（M6 本批归并：`AUDIT.md`/`AUDIT_LOG.md` 已迁入） |
| `org/` | **方案箱**——组织规划接口：`REQUEST.md`、`PLAN-<日期>.md`、`README.md` | 已就位 |
| `archive/` | 已结案、不再维护的文档；门槛：满 30 天或同主题 3 份 | 空，规则生效 |

## 三、新文件头元数据（只对新文件生效，旧文不追改）

新文件首段加一行（四选一，按实际）：

```
> 归属：A 队 ｜ 生命周期：活 ｜ 维护者：助理
> 归属：独立督导 ｜ 生命周期：历史 ｜ 维护者：独立督导
> 归属：组织规划 ｜ 生命周期：生成 ｜ 维护者：助理（脚本生成）
> 归属：用户侧（策略顾问） ｜ 生命周期：活 ｜ 维护者：组织规划
```

- 归属：A 队 / 独立督导 / 组织规划 / 用户侧（策略顾问）
- 生命周期：活 / 历史 / 生成
- 维护者：实际写的人（中文职位名，不用英文实例名）
- **旧文件不追改**（历史不回改）。

## 四、命名约定

- **文件名英文，文档标题与内容中文**。
- 活规范：全大写单词名（`TEAM.md`、`HANDOVER.md`、`BATCHES.md`）。
- 记录类：`<类型>-YYYYMMDD.md`（`PLAN-` `REPORT-` `COST-`）；同日多份加 `-2`、`-3`。
- 方案箱留痕专用：`PLAN-<日期>-advisor.md`（策略顾问意见留痕，由用户或统筹主持落盘）。
- 目录说明：`README.md`。
- 角色卡：文件名 = **英文实例名小写**（`assistant.md`、`artisan.md`），卡内用中文职位名。
- 代码：Python `snake_case.py`、测试 `test_*.py`（统一 `tests/`）、Kotlin `PascalCase`。
- **禁止**：中文文件名、空格、`v2` / `final` / `new` / `tmp`、拼音缩写；**禁止在 `docs/` 顶层新建无前缀 `.md`**（必须是已规范文件或带日期前缀）。

## 五、归档

- 规则：`PLAN-*` / `REPORT-*` / `COST-*` 等结案件满 **30 天**，或同一主题满 **3 份** → 移入 `docs/archive/`。
- **每周盘点一次**（并入独立督导巡检后的例行动作）。
- 执行：组织规划提案 → 助理搬 → 助理跑生成器更新索引。
- **只移动、不改正文**（历史不回改）；被引用的路径在同批更新。
- 归档候选登记：`docs/history/ARCHITECTURE.md`（旧快照，已被 `STRUCTURE.md` 取代）等。

## 六、新增 / 移动文件后的动作

1. 跑 `python3 tools/gen_files_index.py`；`--check` 必须为 0（已接进提交前钩子）。
2. 生成物（`docs/generated/FILES.md` / `docs/generated/METRICS.md`）不得手改，只重跑脚本。
3. 改 `STRUCTURE.md` / `WORKPLAN.md` 仍需统筹主持确认（前者影响重构实施，后者是历史追溯）。
4. 迁移类改动必须**同批完成**，不留「半搬半留」的过渡态。

## 七、本轮边界（2026-11-13 重建）

- **M1**（`history/` + `generated/` 迁移）：**已完成**（本批 `docs(M1)`，7 个文件 `git mv` + 旧路径引用同步）。
- **M2** 角色卡按队拆：`a/`、`org/`、`b/` 均已就位（B 队三卡于 `6841960` 迁入）。
- **M6** 审查件归并 `docs/audit/`：**已完成**（本批 `docs(M6)`，2 文件 `git mv` + 全仓引用同步）。
- 代码侧结构不归本文件管，见 `docs/STRUCTURE.md`。
