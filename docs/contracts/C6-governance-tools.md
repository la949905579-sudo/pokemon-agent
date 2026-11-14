# C6 治理工具批 v1.6：写范围表对齐 + 合同工具三修 + 快照追记
> 归属：A 队 ｜ 生命周期：活（常设合同） ｜ 维护者：A（proxy）
> 类型：机械型（无真机项）｜ 1 批（治理批）｜ 状态机 `open→claimed→green|blocked→accepted`（运行态 `.pilot/C6/`）
## 1–2 合同号 / 类型
C6 ｜ 机械型；治理批 v1.6；验收按 §7 分列（全部命令可判定）。
## 3 事实快照（2026-11-14 12:4x 实测）
- HEAD `2a4a551`；`git status --short` 空；`origin/master..HEAD`=0；C1–C5 accepted，无其它 open 合同。
- `tools/write_scopes.json` 仍含旧 4 角色（统筹主持 / 独立督导 / 审查员 / 成本管理员），缺 C5 新编制「审计督导」（`python3 -c … roles` 可验）。
- `tools/contract_close.py:163` 追记尾句恒为「待考官『可发布』→ B push」——已 push 批次也这么写，与事实不符（C5 考官建议①）。
- `tools/batch_facts.py:48` `last_batch_row` 只取 `|` 表行，`>` 追记行被忽略 → C5 已 push 仍显示「待复核/⏳」（C5 收尾发现⑦）。
- `tools/contract_check.py:68` `in_scope` 支持字面 / `/**` / glob，**不展开** `{a,b}`（C5 §8 曾因此误判，A 改显式路径；考官建议④）。
- tests 35 个 `test_*.py`；`gen_files_index --check`=0。
## 4 基线提交
- B 开工前 `git rev-parse HEAD` 写 `.pilot/C6/status.json` 的 `base`；判据 `<base>..HEAD`。成本基线由 A open 时落 `.pilot/C6/cost-before.json`；claimed 缺该文件 `contract_check` 阻断。
## 5 背景与目标
C5 收尾暴露 4 个工具/映射缺口（写范围表旧编制、contract_close 追记文案、batch_facts 忽略追记、contract_check 花括号），加上 C4 复盘 R3「成本按角色可归因」。目标：把缺口收敛成机械门禁，减少下批人工口径解释与返工。
## 6 任务清单（WBS）
- ① `tools/write_scopes.json` 对齐 `docs/TEAM.md` §一 1.1 会话 / 1.2 成员 新编制：删旧 4 角色、增「审计督导」；代理人/承包商/助理/工匠/考官/真机执行/组织规划/策略顾问/分工与结构规划员 逐条对照 TEAM；新增 `tests/test_write_scopes.py`（≥3 例：JSON 合法、无旧名、关键角色+aliases 齐、paths 字段格式合法）。
- ② `tools/contract_check.py` `in_scope()` 支持 `{a,b}` 展开（多组；非法/空项回退字面匹配不崩）；`tests/test_contract_check.py` +2 例（花括号命中 / 不命中）。
- ③ `tools/contract_close.py` `draft_batch_note()` 尾句按 status 事实：有 push 记录 → 「已 push（origin/master=`<hash>`）；考官已复核」；无 → 「待考官『可发布』→ B push」；`tests/test_contract_close.py` +1 例（两分支）。
- ④ `tools/batch_facts.py`：新增追记行解析（`> 合同收尾追记…` 提取 accepted / 已 push 摘要），BATCHES 摘要优先显示追记、缺则回退末表行；`tests/test_batch_tools.py` +2 例。
- ⑤ 规范：`docs/TEAM.md` §三·十二 增「spawn 显式标职位（`description` 中文职位开头）+ status 时间戳 `YYYY-MM-DD HH:MM`」；`docs/contracts/CONTRACT-TEMPLATE.md` §11 注明时间格式，§8 注明「禁用 `{a,b}` 花括号，改显式路径或确认工具已支持」。
- ⑥ 台账：`BATCHES` 行（`合同:C6`）+ `test_results` 同步 + `FILES`/`METRICS` 重生成 + `HANDOFF` 收尾更新（必含下批建议：A\* 6 图功能批）。
## 7 验收
- **提交前（B 侧）**：`contract_check`（C6）+ `batch_facts` + `batch_close --dry-run` 全过；缺一不得提交。
### 7.1 机械项
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 tools/contract_check.py --contract docs/contracts/C6-governance-tools.md --status .pilot/C6/status.json` | exit 0 |
| M2 | `python3 run_tests.py` | exit 0，通过文件数 = `test_results.json`（≥36） |
| M3 | `python3 tools/gen_files_index.py --check` | exit 0 |
| M4 | `python3 -c "import json;r=json.load(open('tools/write_scopes.json'))['roles'];assert '统筹主持' not in r and '独立督导' not in r and '审计督导' in r"` | exit 0 |
| M5 | `python3 tools/contract_close.py C5 \| grep 合同收尾追记` | 含「已 push」，不含「待考官「可发布」→ B push」 |
| M6 | `python3 tools/batch_facts.py \| grep BATCHES` | 显示追记摘要（accepted/已 push），不再「待复核/⏳」 |
| M7 | `git diff --name-only <base>..HEAD` | 全部落 §8 |
### 7.2 判断项
- 花括号展开不破坏既有字面 / `/**` / glob 行为；追记解析对「无追记行」仓库回退兼容、不崩；`write_scopes` 与 TEAM §一 逐条对照一致（A 抽 1 条 M5 或 M6 复跑，只读回执+路径，不读 diff）。
### 7.3 真机项
- 无（纯 tools/tests/docs）。
### 7.4 成本判据（双判据）
- 每批增量 ≤ 基线×0.85 且 ≤30M/批；基线见 `.pilot/C6/cost-before.json`；`cost-after` 在 accepted 后由 B 取写 `.pilot/C6/cost.json`。
## 8 写入范围
- 允许：`docs/contracts/C6-governance-tools.md`、`tools/write_scopes.json`、`tools/contract_check.py`、`tools/contract_close.py`、`tools/batch_facts.py`、`tests/test_write_scopes.py`（新）、`tests/test_contract_check.py`、`tests/test_contract_close.py`、`tests/test_batch_tools.py`、`docs/TEAM.md`、`docs/contracts/CONTRACT-TEMPLATE.md`、`docs/BATCHES.md`、`docs/HANDOFF.md`、`docs/generated/FILES.md`、`docs/generated/METRICS.md`（经脚本）、`tools/test_results.json`
- 不允许：`native-emu/**`、`docs/audit/**`、`docs/roles/**`、`docs/history/**`、C1–C5 合同与 `PILOT.md`、keystore/签名；`.pilot/**` 不入库
## 9 禁止项
- 不改 C1–C5 样本合同与已推提交；不改 B 队台账正文；不手改生成物（FILES/METRICS 只跑脚本）；不伪造测试数字；不空提交、不 force push、不夹带范围外改动。
- 治理批 1 助理 + 1 考官（本环境 B 无 spawn 权时由 Lead 另起 fresh 考官）；无工匠、无真机项；spawn 子会话时显式标职位。
## 10 变更规则
- B 可改实现路径；不可改验收口径、写入范围、目标；范围外先停手扩合同。
- 不可行：1 轮内 `.pilot/C6/status.json` 置 `blocked` + 回执 ≤3 行原因，停手等 A 裁定。
- 2026-11-14 A 备注：本批起因 `{a,b}` 误判教训，合同 §8 一律写显式路径（花括号修复在 WBS ②，不靠合同写法绕过）。
## 11 回执
- 位置 `.pilot/C6/result.md`（≤10 行；首行 `session: <id> ｜ 状态: green|blocked`）；必含提交号 / 产物路径 / M1–M7 / 判断项依据 / 风险 / 待确认；accepted 后取 `cost-after` 写 `.pilot/C6/cost.json`。
