# C5 旧方案归档：停用旧主流程 + 旧职位引用清理 + 全局 AGENTS 同步
> 归属：A 队 ｜ 生命周期：活（常设合同） ｜ 维护者：A（proxy）
> 类型：功能型（判断项；无真机项）｜ 1 批（治理批，≤1 天）｜ 状态机 `open→claimed→green|blocked→accepted`（运行态 `.pilot/C5/`）
## 1–2 合同号 / 类型
C5 ｜ 功能型（判断项：旧引用是否清零、归档正文是否零改动、全局文件是否真同步）；验收按 §7 分列。
## 3 事实快照（2026-11-14 12:1x 实测）
- HEAD `36a28c1`；`git status --short` 空；`origin/master..HEAD` = 0；C1–C4 accepted，无其它 open 合同。
- `grep -rn "执行主管" docs/ --include=*.md` 仅命中 `docs/archive/README.md`（2 处，归档区豁免）；活体「统筹主持」：TEAM 18 / HANDOVER 7 / 角色卡与索引若干。
- `docs/TEAM.md` §三 仍为 12 步旧主流程；§三·十一 才声明「现行」。`docs/roles/README.md` 仍列 B 队独立督导/审查员/成本管理员。
- 全局 `/root/.dsh/AGENTS.md` 首行为 dsh-app 受管标记；「会话寿命与角色分工（2026-11-12）」为旧四职位口径。
- 用户 2026-11-14 拍板：①审计/督导归 A 队、由代理人按需 spawn 一次性子会话；②全局 AGENTS.md 删受管行 + 先备份。
## 4 基线提交
- B 开工前 `git rev-parse HEAD` 写 `.pilot/C5/status.json` 的 `base`；改动判据 `<base>..HEAD`。成本基线已由 A 在 open 时落 `.pilot/C5/cost-before.json`（`cost_snapshot --before`）；**C5 起 claimed 缺该文件 `contract_check` 阻断**。
## 5 背景与目标
2026-11-12 旧方案（主持/执行主管/工匠/考官/督导 + TEAM §三 12 步主流程）已被 2026-11-14 合同制（A 代理人 / B 承包商 / TEAM §三·十~十二）取代，但旧口径仍散在 TEAM §二/§三、角色卡索引、HANDOVER、全局 AGENTS.md。目标：**单一真源**——旧主流程归档、旧职位引用清零、全局文件同步，新会话只按合同制重建。
## 6 任务清单（WBS）
- ① **停用旧主流程**：`docs/TEAM.md` §三（12 步）正文移入 `docs/archive/TEAM-主流程-12步-20261112.md`（只移动、不改一字）；§三 原位留 3 行「已归档 + 现行见 §三·十一/§三·十二 + 归档路径」；§二 重建步骤改合同制口径（A 代理人 + B 承包商，删「spawn 助理与工匠」旧打包说法）。归档为「用户拍板停用」例外，不受 archive 门槛限制，`BATCHES` 留痕。
- ② **旧职位引用清理（活体文档）**：「统筹主持 / 执行主管 / 独立督导（B 队）」改为合同制职位（A 代理人 / B 承包商 / 审计督导子会话），范围＝`docs/TEAM.md`、`docs/HANDOVER.md`、`docs/roles/README.md`、`docs/README.md`、`docs/STRUCTURE.md`、`docs/org/README.md`、`docs/org/REQUEST.md`、`docs/roles/a/{assistant,artisan,examiner}.md`、`docs/roles/org/{architect,advisor}.md`；**保留** 助理 / 工匠 / 考官 / 真机执行（B 成员沿用）。豁免：`docs/history/**`、`docs/audit/**` 正文、`docs/org/PLAN-*`、`docs/BATCHES.md`（历史台账）、`docs/generated/**`（生成物，含派生旧名不算活体引用）、`docs/contracts/C1–C4` 与 `PILOT.md`（样本不回改）。
- ③ **审计/督导归属（用户拍板）**：`docs/roles/README.md` 表把独立督导/审查员/成本管理员标「停设（B 队旧编制），职责转 A 队」；`docs/roles/b/audit-lead.md` 顶部加 3 行停用说明 + 新入口；新增 `docs/roles/a/supervisor.md`（审计督导子会话卡：代理人按需 spawn、fresh、只读、≤5 行回执、按 `docs/audit/AUDIT.md` 触发）；`docs/TEAM.md` §四 补归属句。**不改 `docs/audit/**` 正文**。
- ④ **全局 AGENTS.md 同步**：`cp /root/.dsh/AGENTS.md /root/.dsh/AGENTS.md.bak-20261114`；删除首行 dsh-app 受管标记；「会话寿命与角色分工（2026-11-12）」整段改为合同制口径（代理人对接用户 / 承包商执行 / B 成员沿用 / 回执 ≤10 行）。文件不入库，回执记**备份路径 + 改后 git 外 diff 摘要（≤3 行）**。
- ⑤ **C4 成本复盘对策落地**：按 `docs/history/RETROSPECTIVE-20261114-C4-cost.md` §三，本合同 §9 已写「真机首跑预检」与「spawn 显式标职位」；本批无真机项，不重开 C4。
- ⑥ **台账**：`BATCHES` 行（`合同:C5`）+ 把 `python3 tools/contract_close.py C4` 的追记行粘入（C4 已 accepted/已推送，现行 C3/C4 行状态列仍写「待复核/不 push」属过期）+ `test_results` 同步 + `FILES`/`METRICS` 重生成（计入 C4 成本、#9/#10）+ `HANDOFF` 收尾更新（必含 C5 归零项 + 下一批建议）。
## 7 验收
- **提交前（B 侧）**：`contract_check`（C5）+ `batch_facts` + `batch_close --dry-run` 全过；缺一不得提交。
### 7.1 机械项
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 tools/contract_check.py --contract docs/contracts/C5-legacy-archive.md --status .pilot/C5/status.json` | exit 0（claimed 缺 cost-before 为阻断） |
| M2 | `python3 run_tests.py` | exit 0，通过数 = `test_results.json` |
| M3 | `python3 tools/gen_files_index.py --check` | exit 0 |
| M4 | `grep -rn "执行主管" docs/TEAM.md docs/HANDOVER.md docs/roles/ docs/README.md docs/STRUCTURE.md docs/org/README.md docs/org/REQUEST.md` | 空（限活体，排除 §6 豁免区） |
| M5 | `grep -rn "统筹主持" docs/TEAM.md docs/HANDOVER.md docs/roles/README.md docs/README.md docs/STRUCTURE.md docs/org/README.md docs/org/REQUEST.md docs/roles/a/assistant.md docs/roles/a/artisan.md docs/roles/a/examiner.md docs/roles/org/architect.md docs/roles/org/advisor.md` | 空（新口径「代理人」） |
| M6 | `test -f docs/archive/TEAM-主流程-12步-20261112.md`；`grep -c "TEAM-主流程-12步-20261112" docs/TEAM.md` | 存在；≥1 |
| M7 | `git diff --name-only <base>..HEAD` | 全部落 §8 |
### 7.2 判断项
- 归档件与原文逐字一致（`git show <base>:docs/TEAM.md` 摘段 diff 为 0，只移动不改字）；全局 AGENTS.md 备份存在、角色段已换、受管行已删；审计归属三处（roles/README ↔ TEAM §四 ↔ supervisor.md）一致；豁免区未动。A 只读回执 + 证据路径，不读 diff。
### 7.3 真机项
- 无（本批纯 docs/配置）。
### 7.4 成本判据（双判据）
- 每批增量 ≤ 基线×0.85 且 ≤30M/批；基线见 `.pilot/C5/cost-before.json`（A 已落）；`cost-after` 在 accepted 后由 B 取写 `.pilot/C5/cost.json`。
## 8 写入范围
- 允许：`docs/contracts/C5-legacy-archive.md`、`docs/TEAM.md`、`docs/HANDOVER.md`、`docs/roles/README.md`、`docs/roles/a/supervisor.md`（新）、`docs/roles/a/{assistant,artisan,examiner}.md`、`docs/roles/org/{architect,advisor}.md`、`docs/org/REQUEST.md`、`docs/roles/b/audit-lead.md`、`docs/README.md`、`docs/STRUCTURE.md`、`docs/org/README.md`、`docs/history/RETROSPECTIVE-20261114-C4-cost.md`、`docs/archive/TEAM-主流程-12步-20261112.md`（新）、`docs/BATCHES.md`、`docs/HANDOFF.md`、`docs/generated/FILES.md`、`docs/generated/METRICS.md`（经脚本）、`tools/test_results.json`、`/root/.dsh/AGENTS.md`（+ 备份，不入库）
- 不允许：`native-emu/**`、`docs/audit/**`、`docs/roles/b/auditor.md`、`docs/roles/b/audit-cost.md`、`docs/history/**` 旧文正文、`docs/org/PLAN-*`、C1–C4 合同与 `PILOT.md`、keystore/签名；`.pilot/**` 不入库
## 9 禁止项
- 不改 C1–C4 样本合同与已推提交；不改 `docs/audit/**` 正文；不手改生成物；不伪造测试/成本数字；不空提交、不 force push；不夹带范围外改动；不改实现代码。
- 全局文件只按 WBS ④ 改：必须先备份、不得删备份、不得顺手改其他段。
- 真机类工作本批不做；后续真机项开工前须先确认 NativeEmu 前台（C4 复盘教训），回执写「首跑 PASS/FAIL + 重试次数」。
- 治理批 1 助理 + 1 考官（无工匠、无 realdevice）；spawn 子会话时显式写职位（降低「未标注职位」占比）。
## 10 变更规则
- 2026-11-14 12:3x A 修订 M4：原命令未排除 §6 豁免区（audit/history/org-PLAN/archive/合同 spec 自身引用），不可满足；改为限活体文件，验收实质不变（B 已按 §6 豁免口径执行并在 BATCHES 留痕）。
- B 可改执行路径；不可改验收口径、写入范围、目标；范围外先停手扩合同。
- 不可行：1 轮内 `.pilot/C5/status.json` 置 `blocked` + 回执 ≤3 行原因，停手等 A 裁定。
## 11 回执
- 位置 `.pilot/C5/result.md`（≤10 行；首行 `session: <id> ｜ 状态: green|blocked`）；必含提交号 / 产物路径 / M1–M7 / 判断项依据 / 全局文件备份路径 + diff 摘要 / 风险 / 待确认；accepted 后取 `cost-after` 写 `.pilot/C5/cost.json`。
