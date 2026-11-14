# C3 流程优化 v1.3：真机执行 + 成本归因 + 等待/证据规范

> 归属：A 队 ｜ 生命周期：活（常设合同） ｜ 维护者：A（proxy）
> 类型：功能型（判断项 + 真机项）｜ 1 批（治理批，≤1 天）｜ 状态机 `open→claimed→green|blocked→accepted`（运行态 `.pilot/C3/`）

## 1–2 合同号 / 类型
C3 ｜ 功能型；本批 = 治理批 v1.3；验收按 §7 分列。

## 3 事实快照（2026-11-14 08:4x 实测）
- HEAD `916fb2d`；`git status --short` 空；`origin/master..HEAD` = 0；无 open 合同（C1/C2 accepted）。
- `ls tools | grep -E 'emu_probe|cost_snapshot'` → 空；`docs/roles/a/realdevice.md` 不存在；`grep -c '三·十二' docs/TEAM.md` → 0。
- `tools/test_results.json`：python 32 / kotlin 115（CI）；METRICS #10「每合同成本」= 无数据（`.pilot/*/cost.json` 不存在）。

## 4 基线提交
- B 开工前 `git rev-parse HEAD` 写 `.pilot/C3/status.json` 的 `base`；改动判据 `<base>..HEAD`，不用 `HEAD~1`。

## 5 背景与目标
试点实测：A 裁决 10.5M/5 turn、试点 7 会话 27.6M、cacheRead 占 98%；v1.2 已降台账/协调成本，但真机取证、成本归因、等待与证据仍靠人工摸索。目标=固化「真机执行角色 + emu_probe + cost_snapshot + token 预算规则」，使下一批 A ≤5M/批、真机 ≤2 turn/≤5 行回执、每合同成本有数。

## 6 任务清单（WBS）
- ① 新职位「真机执行」（实例 `device`）：新增 `docs/roles/a/realdevice.md`（≤30 行；fresh 会话、只跑 `tools/emu_probe.py`、回执 ≤5 行 + ≤2 证据路径）；`docs/TEAM.md` §一 职位行 + §三·十二 引用；`docs/roles/README.md` 索引；`tools/write_scopes.json` 同步。
- ② `tools/emu_probe.py`：`--check-move <id> [--expect-name <名>]` 走 TCP:55401 读 `MY_BATTLE+0x0C`，对照 `bdata.MOVES` 输出一行 `PASS/FAIL <id> <name>`；截图约定 `/sdcard/Download/DSH-Go/probe-<id>-<ts>.jpg`；离线 mock 可测 + `tests/test_emu_probe.py` ≥4 例。
- ③ `tools/cost_snapshot.py`：`--contract <id>` 读 `token_report.mjs --json` 生成 `.pilot/<id>/cost.json`（windowTotal/baselinePerBatch/delta/perBatch/threshold + `byRole`）；`tests/test_cost_snapshot.py` ≥3 例（fixture）。
- ④ 规则：`docs/TEAM.md` 新增 §三·十二「v1.3 token 预算」：裁决会话 0 截图/0 长文、零轮询（单次等待 ≤20min）、证据只给路径、A ≤5M/批目标、真机交「真机执行」、每合同 cost.json；`docs/contracts/README.md` 补口径。
- ⑤ 台账（B 侧助理）：`BATCHES` 一行（备注 `合同:C3`）+ `test_results` 同步 + `FILES` 重生成。
- ⑥ `docs/HANDOFF.md` 补 3–5 行事实快照（HEAD 916fb2d / python 32/32（测试快照） / C1·C2 accepted + C3 open / 下一步=C3）；只补快照，不囤长文。

## 7 验收
- **提交前（B 侧）**：`python3 tools/contract_check.py --contract docs/contracts/C3-token-optimization.md --status .pilot/C3/status.json` 通过；`python3 tools/batch_facts.py` 与 `python3 tools/batch_close.py --batch "C3 流程优化v1.3" --dry-run` 通过；缺一不得提交。
### 7.1 机械项
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 tools/emu_probe.py --help` | exit 0，输出含 `--check-move` |
| M2 | `python3 run_tests.py` | exit 0，通过数 = `test_results.json`（≥32+新增） |
| M3 | `python3 tools/contract_check.py --contract docs/contracts/C3-token-optimization.md --status .pilot/C3/status.json` | exit 0 |
| M4 | `python3 tools/gen_files_index.py --check` | exit 0 |
| M5 | `grep -c '三·十二' docs/TEAM.md`；`grep -c '真机执行' docs/TEAM.md docs/roles/a/realdevice.md`；`grep -c 'C3' docs/HANDOFF.md` | 三·十二 ≥1；真机执行两文件均 ≥1；HANDOFF 含 C3 |
| M6 | `git diff --name-only <base>..HEAD` | 全部落 §8 范围 |
### 7.2 判断项
- `cost_snapshot.py` 输出字段与 §三·十 / README 口径一致（5 字段 + byRole），fixture 可离线复算；`emu_probe` mock 测试证明无真机也可判定；A 只看回执 + 证据路径，不读 diff。
### 7.3 真机项（用户/A 执行，不改存档）
- 手机 NativeEmu 前台、内存第 4 招 = `232` 的战斗状态，跑 `python3 tools/emu_probe.py --check-move 232 --expect-name 金属爪`，期望 exit 0、输出 `PASS 232 金属爪`、截图 `/sdcard/Download/DSH-Go/probe-232-*.jpg`；回 A 一行。
### 7.4 成本判据（双判据）
- 每批增量 ≤ 基线×0.85 且 ≤30M/批；`cost-after` 在 accepted 后取；快照 `.pilot/C3/cost.json`（5 字段）。

## 8 写入范围
- 允许：`docs/contracts/C3-token-optimization.md`、`docs/roles/a/realdevice.md`、`docs/roles/a/contractor.md`、`docs/roles/README.md`、`docs/TEAM.md`、`docs/contracts/README.md`、`tools/emu_probe.py`、`tools/cost_snapshot.py`、`tools/write_scopes.json`、`tests/test_emu_probe.py`、`tests/test_cost_snapshot.py`、`tools/test_results.json`、`docs/generated/FILES.md`、`docs/generated/METRICS.md`（经脚本）、`docs/BATCHES.md`、`docs/HANDOFF.md`
- 不允许：`native-emu/**`、`docs/audit/**`、`docs/roles/b/**`、`docs/history/**`、keystore/签名；`.pilot/**` 不入库

## 9 禁止项
- 不改 C1/C2 样本合同；不手改生成物（FILES/METRICS 只跑脚本）；不伪造测试/成本数字；不空提交、不 force push；不夹带范围外改动；不 spawn 工匠/多助理（治理批：1 助理 + 1 考官；tools/tests 由助理代做并在 BATCHES 留痕授权）。

## 10 变更规则
- B 可改实现路径；不可改验收口径、写入范围、目标；范围外先停手扩合同。
- 不可行：1 轮内 `.pilot/C3/status.json` 置 `blocked` + 回执 ≤3 行原因，停手等 A 裁定。

## 11 回执
- 位置 `.pilot/C3/result.md`（≤10 行；首行 `session: <id> ｜ 状态: green|blocked`）；必含提交号 / 产物路径 / M1–M6 / 判断项依据 / 真机结果 / 风险 / 待确认；accepted 后取 `cost-after` 写 `.pilot/C3/cost.json`。
