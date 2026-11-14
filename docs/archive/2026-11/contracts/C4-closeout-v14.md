# C4 治理批 v1.4：收尾自动化 + 成本基线门禁 + 真机执行实战

> 归属：A 队 ｜ 生命周期：活（常设合同） ｜ 维护者：A（proxy）
> 类型：功能型（判断项 + 真机项）｜ 1 批（治理批，≤1 天）｜ 状态机 `open→claimed→green|blocked→accepted`（运行态 `.pilot/C4/`）

## 1–2 合同号 / 类型
C4 ｜ 功能型；本批 = 治理批 v1.4；验收按 §7 分列。

## 3 事实快照（2026-11-14 11:1x 实测）
- HEAD `d3baeab`；`git status --short` 空；`origin/master..HEAD` = 0；C1/C2/C3 accepted，无其它 open 合同。
- `ls tools | grep contract_close` → 空；`python3 tools/cost_snapshot.py --help` 无 `--before`；`tools/test_results.json` python 34。
- METRICS #9=2/2（开工前旧值）、#10=无数据（C3 已 accepted 且 `.pilot/C3/cost.json` 已落，待重生成计入）。

## 4 基线提交
- B 开工前 `git rev-parse HEAD` 写 `.pilot/C4/status.json` 的 `base`；改动判据 `<base>..HEAD`（不用 `HEAD~1`）。C4 自身成本基线已由 A 在 open 时落 `.pilot/C4/cost-before.json`（当日窗口 ÷ 窗口 5 批，工具化前的手动快照）。

## 5 背景与目标
C3 已闭环但留 3 个收尾缺口：开工前成本快照无机械强制（C3 只能重建近似）、验收后收尾不自动（BATCHES 末行 ⏳ / HANDOFF 停在 claimed / METRICS 滞后）、真机执行角色未实战。目标=补「cost_snapshot --before + contract_close + 真机执行演练 + 台账重生成」，C5 起成本基线有据、收尾一键可查、真机项有人跑。

## 6 任务清单（WBS）
- ① `tools/cost_snapshot.py` 增 `--before`：写 `.pilot/<id>/cost-before.json`（windowTotal/batches/baselinePerBatch/threshold）；`--contract` 仍产 cost.json；更新/新增 `tests/test_cost_snapshot.py`（≥3 例）。
- ② `tools/contract_check.py`：claimed 态缺 `.pilot/<id>/cost-before.json` 记警告，**C5 起**改阻断（TEAM 注明生效批次）；`tests/test_contract_check.py` 加 2 例。
- ③ 新 `tools/contract_close.py <id>`：accepted 后校验 accepted/contract_check，输出 BATCHES 追记行草稿 + HANDOFF 摘要行 + METRICS 重生成提示 + cost 摘要；只打印不改台账（同 batch_close）；`tests/test_contract_close.py` ≥3 例。
- ④ 真机执行演练：`realdevice` 跑真机项（`emu_probe --check-move 232 --expect-name 金属爪` + 手机截屏 `/sdcard/Download/DSH-Go/probe-232-*.jpg`），回执 ≤5 行 + 证据路径；`docs/roles/a/realdevice.md` 补执行口径；`docs/contracts/README.md` 更正 emu_probe 截图口径（工具不截屏、由执行者截）。
- ⑤ 规则：`docs/TEAM.md` §三·十二 补「A open 后落 cost-before」「B 收尾跑 contract_close」「真机项默认交 realdevice」「A open 后同步产出承包商启动提示词」；`docs/contracts/CONTRACT-TEMPLATE.md` 增 §12 启动提示词骨架（占位符 <编号>/<slug>/<成员>：角色卡+合同+TEAM→batch_facts→写 status→执行→回执）；`docs/contracts/README.md` 同步。
- ⑥ 台账：`BATCHES` 行（`合同:C4`）+ `test_results` 同步 + `FILES`/`METRICS` 重生成（C3 成本与 #9 计入）+ `HANDOFF` 收尾更新（必含**下一步计划：C5 旧方案归档**——停用旧主流程、旧职位引用清理、全局 `~/.dsh/AGENTS.md` 同步、审计/督导归属待用户拍板）。

## 7 验收
- **提交前（B 侧）**：`contract_check`（C4）+ `batch_facts` + `batch_close --dry-run` + `contract_close C4 --dry-run`（若已实现）全过；缺一不得提交。
### 7.1 机械项
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 tools/cost_snapshot.py --help` | exit 0，输出含 `--before` |
| M2 | `python3 tools/contract_close.py --help` | exit 0，有用法输出 |
| M3 | `python3 run_tests.py` | exit 0，通过数 = `test_results.json`（≥34+新增） |
| M4 | `python3 tools/gen_files_index.py --check` | exit 0 |
| M5 | `python3 tools/contract_check.py --contract docs/contracts/C4-closeout-v14.md --status .pilot/C4/status.json`；`grep -c '启动提示词' docs/contracts/CONTRACT-TEMPLATE.md` | exit 0；≥1 |
| M6 | `python3 tools/metrics.py --check` | exit 0，输出 #9=3/3（首轮通过）、#10 有数据（非「无数据」） |
| M7 | `git diff --name-only <base>..HEAD` | 全部落 §8 范围 |
### 7.2 判断项
- `cost_snapshot --before` 字段与 §7.4 口径一致（fixture 复算）；`contract_close` 输出风格与 `batch_close` 一致且不代写台账；`emu_probe` 截图口径更正后与实现一致。A 只读回执 + 证据路径，不读 diff。
### 7.3 真机项（realdevice 执行）
- 手机 NativeEmu 前台、第 4 招=232 的战斗，跑 `python3 tools/emu_probe.py --check-move 232 --expect-name 金属爪`，期望 `PASS 232 金属爪`，截屏存 `/sdcard/Download/DSH-Go/probe-232-*.jpg`，回 A 一行；若 realdevice 无手机工具，B 回执注明改由用户/A 执行，不阻断。
### 7.4 成本判据（双判据）
- 每批增量 ≤ 基线×0.85 且 ≤30M/批；基线见 `.pilot/C4/cost-before.json`（A 已落）；`cost-after` 在 accepted 后由 B 取写 `.pilot/C4/cost.json`。

## 8 写入范围
- 允许：`docs/contracts/C4-closeout-v14.md`、`docs/contracts/CONTRACT-TEMPLATE.md`、`docs/roles/a/realdevice.md`、`docs/TEAM.md`、`docs/contracts/README.md`、`tools/cost_snapshot.py`、`tools/contract_check.py`、`tools/contract_close.py`、`tests/test_cost_snapshot.py`、`tests/test_contract_check.py`、`tests/test_contract_close.py`、`tools/test_results.json`、`docs/generated/FILES.md`、`docs/generated/METRICS.md`（经脚本）、`docs/BATCHES.md`、`docs/HANDOFF.md`
- 不允许：`native-emu/**`、`docs/audit/**`、`docs/roles/b/**`、`docs/history/**`、keystore/签名；`.pilot/**` 不入库

## 9 禁止项
- 不改 C1/C2/C3 样本合同与已推提交；不手改生成物（FILES/METRICS 只跑脚本）；不伪造测试/成本数字；不空提交、不 force push；不夹带范围外改动；治理批 1 助理 + 1 考官 + 1 realdevice，不另开工匠。

## 10 变更规则
- B 可改实现路径；不可改验收口径、写入范围、目标；范围外先停手扩合同。
- 不可行：1 轮内 `.pilot/C4/status.json` 置 `blocked` + 回执 ≤3 行原因，停手等 A 裁定。

## 11 回执
- 位置 `.pilot/C4/result.md`（≤10 行；首行 `session: <id> ｜ 状态: green|blocked`）；必含提交号 / 产物路径 / M1–M7 / 判断项依据 / 真机结果 / 风险 / 待确认；accepted 后取 `cost-after` 写 `.pilot/C4/cost.json`。
