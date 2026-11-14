# C10v2 主会话模型落盘：A/B 双主会话 + 文件总线 + 编制条款（架构核对最终版）
> 归属：A 队 ｜ 生命周期：活（常设合同） ｜ 维护者：A（proxy）
> 类型：机械型（无真机项）｜ 1 批（治理批 v2.0）｜ 状态机 `open→claimed→green|blocked→accepted`（运行态 `.pilot/C10/`）
## 1–2 合同号 / 类型
C10（v2，v1 已作废并回滚）｜ 机械型；1 批；验收按 §7。依据：用户 2026-11-14 16:0x–16:5x 决定 + 架构逐条核对结论。
## 3 事实快照（2026-11-14 16:5x 实测）
- 回滚基线：`bdc431e`（origin/master）；B 执行 `git reset --hard bdc431e` 后 2 条未推送 C10 提交（`ae151c3`/`83e451f`）撤销；全局 AGENTS 已恢复 C8 版（备份 `AGENTS.md.bak-20261114-1623`）。
- 运行态：`.pilot/BUS-PROTOCOL.md`（单文件总线协议）、`.pilot/BUS.md`、`.pilot/HANDOFF-DECISIONS-20261114.md`、本文件 `.pilot/C10-v2-draft.md`。
- `docs/HANDOFF.md` 第 3 行、第 17 行仍写「C9 收尾提交待 push」（实际已 push + accepted）。
## 4 基线提交
- B claim 首步：`python3 tools/cost_snapshot.py --before C10` 写 `.pilot/C10/cost-before.json` 并回四字段；base=`git rev-parse HEAD`（应=bdc431e）；status 置 claimed。
## 5 背景与目标
A/B 改为两条独立主会话 + 单文件总线轮询；旧条款仍是子代理模型，且架构核对已逐条定稿。目标：一次落盘最终版（含 C10 v1 事故教训：B 必须在步骤间轮询、收到 HOLD/STOP 立即停手）。
## 6 任务清单（WBS）
- ① **HANDOFF 修正**：第 3 行、第 17 行「C9 收尾提交待 push」→ 已 push（`bdc431e`）且 accepted，与前置检查表 #2 一致。
- ② **TEAM 主模型**：§一 1.1 标「代理人 / 承包商均为用户开的独立主会话，A 不 spawn B」；1.2 成员层：承包商（B 主会话）spawn 助理/工匠/考官；审计督导由 A spawn；真机执行 **A 派发**；组织规划 **A 按需发起**且分工/结构规划员由 **A 一并 spawn**；策略顾问 **停用**。§三·八 改为「A↔B 单文件总线」：`.pilot/BUS.md`、消息格式、B 启动即轮询/完成继续轮询/`END` 停、**每处理完一步必须轮询**、收到 `HOLD`/`STOP` 立即停手、A 后台监听且连续两次异常改用户提示。§三·十 合同制补「A/B 主会话 + 总线交接」。§六 生命线：A >40 轮或压缩≥1；B 单会话单合同、轮次 ≤30；B 寿命由审计督导巡检。§五.6 改为「A 可直接改合同 spec / 验收结论 / 流程条款，其他正文派 B 并留痕」。
- ③ **角色卡与索引**：`roles/a/proxy.md`（主会话、不 spawn B、总线节点、40 轮、写入范围含 `.pilot/**`、审核 ≤2 抽验）；`roles/a/contractor.md`（B 主会话、可 spawn 成员、每合同全新、总线轮询/END）；`roles/README.md`（策略顾问停用；组织规划/规划员 spawn 归属）；`roles/org/advisor.md` 顶部停用说明；`roles/b/audit-{lead,or,cost}*.md` 是否标停用按 M4/M5 结论（审查员/成本管理员停设沿用）。
- ④ **全局 `/root/.dsh/AGENTS.md`**：备份 `AGENTS.md.bak-20261114-1653`（实际时刻）；只改「会话寿命与角色分工」段为最终版；不得恢复受管行。
- ⑤ **台账**：`BATCHES` 行（`合同:C10`）+ `test_results` 同步 + `FILES`/`METRICS` 重生成 + `HANDOFF` 收尾（本批摘要 + 下批候选）。
- ⑥ **C5 漏触发补审**：随 B 寿命巡检时由审计督导子会话做一次轻量 T5 补审并留痕（不单开批）。
## 7 验收
### 7.1 机械项
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 tools/contract_check.py --contract docs/contracts/C10-main-session-model.md --status .pilot/C10/status.json` | exit 0 |
| M2 | `python3 run_tests.py` | exit 0，38/38 |
| M3 | `python3 tools/gen_files_index.py --check` | exit 0 |
| M4 | `grep -n "C9 收尾" docs/HANDOFF.md \| head -2` | 不含「待 push」，含已 push 事实 |
| M5 | `grep -c "BUS.md" docs/TEAM.md docs/roles/a/contractor.md`；`grep -c "独立主会话" docs/TEAM.md docs/roles/a/proxy.md`；`grep -c "立即停手" docs/TEAM.md` | 均 ≥1 |
| M6 | `grep -n "停用" docs/roles/README.md docs/roles/org/advisor.md`；`grep -c "40 轮" docs/TEAM.md` | 命中策略顾问停用；TEAM ≥1 |
| M7 | `git diff --name-only <base>..HEAD` | 全部落 §8 |
### 7.2 判断项
- 条款与架构核对结论逐条对应（S1 写入范围/§五.6、S2 单会话单合同/30 轮、S3 触发判定+C5 补审、S4/M6/M7 A 一并 spawn、M1 每批新开、M2 按需≤2、M3 复核口径+复用≤3、M4/M5 停设、P 汇报行数）；总线协议与 `.pilot/BUS-PROTOCOL.md` 一致；全局文件 diff 仅角色段。A 只读回执+路径，至多 2 条只读抽验。
### 7.3 真机项
- 无（纯 docs/规则）。
### 7.4 成本判据（双判据）
- 每批增量 ≤ 基线×0.85 且 ≤30M/批；基线 `.pilot/C10/cost-before.json`（B claim 首步落）；`cost-after` 由 B 在 A 置 accepted 后取。
## 8 写入范围
- 允许：`docs/contracts/C10-main-session-model.md`、`docs/HANDOFF.md`、`docs/TEAM.md`、`docs/roles/a/proxy.md`、`docs/roles/a/contractor.md`、`docs/roles/README.md`、`docs/roles/org/advisor.md`、`docs/roles/b/auditor.md`、`docs/roles/b/audit-cost.md`、`docs/roles/b/audit-lead.md`、`docs/BATCHES.md`、`docs/generated/FILES.md`、`docs/generated/METRICS.md`（经脚本）、`tools/test_results.json`、`/root/.dsh/AGENTS.md`（+备份，不入库）
- 不允许：C1–C9 合同与 `PILOT.md`、`docs/audit/**`、`docs/history/**`、`tools/**`（仅 test_results.json）、`native-emu/**`、keystore；`.pilot/**` 不入库
## 9 禁止项
- 不回改 BATCHES 历史追记与 docs/history 正文；不改 C1–C9 合同；不伪造测试/成本数字；不空提交、不 force push、不夹带范围外改动。
- 全局文件只按 WBS ④ 改：先备份、只改角色段、不得恢复受管行。
- **流程强制**：B 每处理完一步必须追加状态并轮询总线；收到 `HOLD`/`STOP` 立即停手（C10 v1 事故教训）。
- 治理批 1 助理 + 1 考官（B 主会话自行 spawn）；无工匠、无真机项。
## 10 变更规则
- B 可改实现路径；不可改验收口径、写入范围、目标；范围外先停手扩合同。
- 不可行：1 轮内 status 置 `blocked` + 总线追加 `BLOCKED`（≤3 行原因），停手等 A 裁定。
## 11 回执
- 位置 `.pilot/C10/result.md`（≤10 行；首行 `session: <id> ｜ 状态: green|blocked`）+ 总线追加 `GREEN`；必含提交号 / 产物路径 / cost-before 四字段 / M1–M7（命令+输出摘要）/ 判断项依据 / 风险。
