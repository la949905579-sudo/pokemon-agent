# C8 流程规范同步：代理人职责边界收窄 + C7 成本复盘落盘
> 归属：A 队 ｜ 生命周期：活（常设合同） ｜ 维护者：A（proxy）
> 类型：机械型（无真机项）｜ 1 批（治理小批 v1.8）｜ 状态机 `open→claimed→green|blocked→accepted`（运行态 `.pilot/C8/`）
## 1–2 合同号 / 类型
C8 ｜ 机械型；1 批；验收按 §7 分列。用户 2026-11-14 14:0x 授权「派 B 同步文档」，14:3x 授权「C7 复盘并入 C8」。
## 3 事实快照（2026-11-14 14:3x 实测）
- C7 收尾提交 `9e830a7`（待 push）；C1–C6 accepted、C7 accepted；无其它 open 合同。
- 用户硬性要求（2026-11-14 13:5x）：**代理人及其子代理不得从事任何实质性工作**，只做「经手 / 需求对接 / 任务派发 / 流程规范 / 结果审核」；A 审核允许 **1–2 条只读抽验**，不得跑测试/构建/写实现/做 git 操作。
- 现文档冲突：`TEAM.md` §三·十「A 只抽查 1 条机械项」、§三·十二「A open 后跑 `cost_snapshot --before` / A 跑 `contract_close`」、`roles/a/proxy.md` 边界、`contracts/README.md` 成本流程、`CONTRACT-TEMPLATE.md` §12、全局 `/root/.dsh/AGENTS.md` 角色段。
- C7 成本：perBatch **23,534,117 > threshold 19,355,272（超 21.6%）**，≤30M ✓ → 记超须复盘（`.pilot/C7/cost.json`）；复盘件属 `docs/history/**`，C7 合同 §8 禁改，故并入本批。
## 4 基线提交
- B claim 后第一件事：`python3 tools/cost_snapshot.py --before C8` 写 `.pilot/C8/cost-before.json`（**新流程：A 不再代跑**）并回路径/四字段；base = B 开工前 `git rev-parse HEAD`（应为 `9e830a7` push 后 HEAD）。
## 5 背景与目标
把用户 13:5x 的硬性要求写进规则真源，消除「A 干执行活」的旧条款；同时按 C4 先例把 C7 记超复盘落盘。目标：单一真源、后续批不再误判 A 越界，成本可见。
## 6 任务清单（WBS）
- ① **规则同步（A 职责边界收窄）**：
  - `docs/TEAM.md`：§一 1.1 代理人行改为「只经手/需求对接/任务派发/流程规范/结果审核；**不得从事实质性工作**」；§三·十 验收条改「A 只读回执与证据 + **至多 1–2 条只读抽验**，不跑测试/构建/写文件」；§三·十二 把「A open 跑 cost-before」「A 跑 contract_close」改为**B 执行、A 只收路径与输出**；新增「代理人禁止清单」（写实现/工具、跑测试构建、git 操作、代 B 取证落盘）。
  - `docs/roles/a/proxy.md`：职责/边界同步（删「抽查机械项」旧措辞，加禁止清单与五项职责）。
  - `docs/contracts/README.md`：成本快照/收尾流程改为 B 执行；A 只审核。
  - `docs/contracts/CONTRACT-TEMPLATE.md`：§12 启动提示词骨架注明「B claim 首步跑 cost_snapshot --before 并回四字段」；§11 回执要求贴命令+输出摘要。
  - 全局 `/root/.dsh/AGENTS.md`：先备份 `AGENTS.md.bak-20261114-143x`；只改「会话寿命与角色分工」段为五项职责 + 禁止清单（受管行已于 C5 删除，勿恢复）。
- ② **C7 成本复盘落盘**：新建 `docs/history/RETROSPECTIVE-20261114-C7-cost.md`（五节：现象/根因/对策/验收/归属；数字取 `.pilot/C7/cost.json`：perBatch 23,534,117 / baseline 22,770,908 / threshold 19,355,272 / 超 21.6%；根因：① A 写的 M5「<10%」不可达→blocked 一轮往返；② 本批含执行+blocked→resume 多轮会话；③ A 侧长文与取证推高主会话；对策：验收判据先做可达性自检、A 派发消息限行数/少长文、成本快照流程改 B 执行；归属：A 写要点、B 落盘、下批复核）。
- ③ 台账：`BATCHES` 行（`合同:C8`）+ `test_results` 同步 + `FILES`/`METRICS` 重生成 + `HANDOFF` 收尾（含下批建议）。
## 7 验收
### 7.1 机械项
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 tools/contract_check.py --contract docs/contracts/C8-a-boundary.md --status .pilot/C8/status.json` | exit 0 |
| M2 | `python3 run_tests.py` | exit 0，37/37（本批无 tests 变更） |
| M3 | `python3 tools/gen_files_index.py --check` | exit 0 |
| M4 | `grep -c "不得从事任何实质性工作\|不得从事实质性工作" docs/TEAM.md docs/roles/a/proxy.md` | 两文件均 ≥1 |
| M5 | `grep -n "cost_snapshot --before" docs/TEAM.md docs/contracts/README.md docs/contracts/CONTRACT-TEMPLATE.md` | 均含「B 执行/claim 首步」语境，不再写 A 代跑 |
| M6 | `test -f docs/history/RETROSPECTIVE-20261114-C7-cost.md`；五节关键词 `现象/根因/对策/验收/归属` 均命中；数字 `23,534,117`、`19,355,272` 与 `.pilot/C7/cost.json` 一致 | exit 0 |
| M7 | `git diff --name-only <base>..HEAD` | 全部落 §8 |
### 7.2 判断项
- 条款与用户 13:5x 硬要求逐条对应（五项职责 + 禁止清单 + 1–2 条只读抽验）；复盘根因不虚构、数字取自 cost.json；全局文件 diff 只命中角色段、备份存在、受管行未恢复。A 只读回执+路径，至多 2 条只读抽验。
### 7.3 真机项
- 无（纯 docs/规则）。
### 7.4 成本判据（双判据）
- 每批增量 ≤ 基线×0.85 且 ≤30M/批；基线 `.pilot/C8/cost-before.json`（B claim 首步落）；`cost-after` 由 B 在 A 置 accepted 后取。
## 8 写入范围
- 允许：`docs/contracts/C8-a-boundary.md`、`docs/TEAM.md`、`docs/roles/a/proxy.md`、`docs/contracts/README.md`、`docs/contracts/CONTRACT-TEMPLATE.md`、`docs/history/RETROSPECTIVE-20261114-C7-cost.md`（新）、`docs/BATCHES.md`、`docs/HANDOFF.md`、`docs/generated/FILES.md`、`docs/generated/METRICS.md`（经脚本）、`tools/test_results.json`、`/root/.dsh/AGENTS.md`（+备份，不入库）
- 不允许：C1–C7 合同与 `PILOT.md`、`docs/audit/**`、`docs/roles/b/**`、`docs/roles/org/**`、docs/history 旧文正文、`tools/**`（仅 test_results.json 允许）、`native-emu/**`、keystore；`.pilot/**` 不入库
## 9 禁止项
- 不改 C1–C7 样本合同与已推提交；不改 B 队台账正文；不手改生成物；不伪造测试/成本数字；不空提交、不 force push、不夹带范围外改动。
- 全局文件只按 WBS ① 改：先备份、只改角色段、不得恢复受管行、不得顺手改其他段。
- 治理批 1 助理 + 1 考官（本环境 B 无 spawn 权时由 Lead 起 fresh 考官）；无工匠、无真机项。
## 10 变更规则
- B 可改实现路径；不可改验收口径、写入范围、目标；范围外先停手扩合同。
- 不可行：1 轮内 `.pilot/C8/status.json` 置 `blocked` + 回执 ≤3 行原因，停手等 A 裁定。
## 11 回执
- 位置 `.pilot/C8/result.md`（≤10 行；首行 `session: <id> ｜ 状态: green|blocked`）；必含提交号 / 产物路径 / **cost-before 四字段** / M1–M7（含命令+输出摘要）/ 判断项依据 / 风险 / 待确认；accepted 后取 `cost-after` 写 `.pilot/C8/cost.json`。
