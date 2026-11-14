# C7 成本归因修复：token_report 职位映射对齐新编制
> 归属：A 队 ｜ 生命周期：活（常设合同） ｜ 维护者：A（proxy）
> 类型：机械型（无真机项）｜ 1 批（治理小批）｜ 状态机 `open→claimed→green|blocked→accepted`（运行态 `.pilot/C7/`）
## 1–2 合同号 / 类型
C7 ｜ 机械型；治理小批 v1.7；验收按 §7 分列（全部命令可判定）。
## 3 事实快照（2026-11-14 13:1x 实测）
- HEAD `a9604b8`；`git status --short` 空；`origin/master..HEAD`=0；C1–C6 accepted，无其它 open 合同。
- `node tools/token_report.mjs --json --since 2026-11-14`：windowTotal **181,758,052**；byRole＝主会话（未标注）78,096,324 / **未知职位 53,364,702（29.4%）** / 助理 39,011,531 / 考官 11,285,495。
- `tools/token_report.mjs:61` ROLE_PATTERNS 仍是旧 9 角色（统筹主持/助理/工匠/考官/独立督导/审查员/成本管理员/组织规划/策略顾问），缺 代理人/承包商/审计督导/真机执行/分工规划员/结构规划员；旧「执行主管」被并入助理。
- `tools/write_scopes.json` 已是 11 角色新编制（C6 对齐），两表不一致。
- tests 36 个 `test_*.py`；`gen_files_index --check`=0。
## 4 基线提交
- B 开工前 `git rev-parse HEAD` 写 `.pilot/C7/status.json` 的 `base`；判据 `<base>..HEAD`。成本基线 A open 时落 `.pilot/C7/cost-before.json`；claimed 缺该文件 `contract_check` 阻断。
## 5 背景与目标
C4 复盘 R3「未标注/未知职位占比高」主因＝ROLE_PATTERNS 旧表：C5/C6 的承包商、考官、真机执行会话被记「未知职位」（实测 53.4M/29.4%），成本无法按新角色归因。目标：映射与 `tools/write_scopes.json` / `docs/TEAM.md` §一 的 11 角色对齐、旧名兼容映射到新规范名；**只改分组、不改总量**。
## 6 任务清单（WBS）
- ① `tools/token_report.mjs`：`ROLE_PATTERNS` 改为 11 规范角色（与 `write_scopes.json` 同集：代理人/承包商/审计督导/组织规划/策略顾问/真机执行/助理/工匠/考官/分工规划员/结构规划员）；旧名兼容映射：统筹主持·执行主管→代理人、独立督导·审查员·成本管理员→审计督导、builder→工匠、steward→助理、verifier→考官；「取最靠左命中」与「无 descriptor→主会话（未标注职位）」规则**不变**。
- ② 可测性：新增 `--roles` 输出（JSON：规范角色→匹配词）；新增 `tests/test_token_roles.py`（≥4 例，纯离线：11 角色齐全、旧名映射正确、取最靠左规则、未知 label→未知职位）。
- ③ 文档：`docs/TEAM.md` §三·十二 增「成本归因唯一映射＝`token_report.mjs` ROLE_PATTERNS；改 TEAM §一 职位表须同批更新（与 `write_scopes` 同等）」。
- ④ 台账：跑 `node tools/token_report.mjs --json --since 2026-11-14` 记录改前/改后 byRole 对比（M5）；`BATCHES` 行（`合同:C7`）+ `test_results` 同步 + `FILES`/`METRICS` 重生成 + `HANDOFF` 收尾（R3：主因已修，观察项转下批验证）。
## 7 验收
- **提交前（B 侧）**：`contract_check`（C7）+ `batch_facts` + `batch_close --dry-run` 全过；缺一不得提交。
### 7.1 机械项
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 tools/contract_check.py --contract docs/contracts/C7-token-roles.md --status .pilot/C7/status.json` | exit 0 |
| M2 | `python3 run_tests.py` | exit 0，文件数 = `test_results.json`（≥37，含新 `test_token_roles.py`） |
| M3 | `python3 tools/gen_files_index.py --check` | exit 0 |
| M4 | `node tools/token_report.mjs --roles --json` | exit 0；JSON 含 6 个新角色（代理人/承包商/审计督导/真机执行/分工规划员/结构规划员）且共 11 个规范角色 |
| M5 | `node tools/token_report.mjs --json --since 2026-11-14` | 「未知职位」totalTokens 占比 **<15%**（改前 29.4%，改后实测 13.8%）；残留仅限 label 无任何职位词的会话（C1/C2 试点 2 个，回执须列明会话/token）；记录 windowTotal 差额（新增会话，不判红） |
| M6 | `python3 tools/metrics.py --check` | exit 0 |
| M7 | `git diff --name-only <base>..HEAD` | 全部落 §8 |
### 7.2 判断项
- 旧名映射有据（历史会话归属不丢、不凭空造角色）；「取最靠左命中」「无 descriptor→主会话」规则未变；「只改分组不改总量」由单测保证（同 fixture 映射前后 totals 相等）；M5 占比下降来自真实映射而非改口径（A 抽 1 条 M4 或 M5 复跑，只读回执+路径，不读 diff）。M5 残留不得靠改算法/造映射消除：2 个 C1/C2 试点会话 descriptor 无职位词（落盘合同制试点最小集 20,121,510 / 轻量复核试点落盘提交 5,942,544），如实记录即可。
### 7.3 真机项
- 无（纯 tools/tests/docs）。
### 7.4 成本判据（双判据）
- 每批增量 ≤ 基线×0.85 且 ≤30M/批；基线见 `.pilot/C7/cost-before.json`；`cost-after` 在 accepted 后由 B 取写 `.pilot/C7/cost.json`。
## 8 写入范围
- 允许：`docs/contracts/C7-token-roles.md`、`tools/token_report.mjs`、`tests/test_token_roles.py`（新）、`docs/TEAM.md`、`docs/BATCHES.md`、`docs/HANDOFF.md`、`docs/generated/FILES.md`、`docs/generated/METRICS.md`（经脚本）、`tools/test_results.json`
- 不允许：`native-emu/**`、`docs/audit/**`、`docs/roles/**`、`docs/history/**`、C1–C6 合同与 `PILOT.md`、`tools/write_scopes.json`（已对齐，不动）、keystore/签名；`.pilot/**` 不入库
## 9 禁止项
- 不改 C1–C6 样本合同与已推提交；不改 B 队台账正文；不手改生成物；不伪造测试/成本数字；不空提交、不 force push、不夹带范围外改动。
- 治理批 1 助理 + 1 考官（本环境 B 无 spawn 权时由 Lead 另起 fresh 考官）；无工匠、无真机项；spawn 子会话时显式标职位。
- 只改归因分组，不得改 windowTotal 统计口径、不得改 sessions 明细算法。
## 10 变更规则
- 2026-11-14 13:2x A 修订 M5：原「<10%」不可达——残留 26.06M 来自 2 个 label 无职位词的 C1/C2 试点会话，按 §7.2 不映射；改为 **<15%**（改前 29.4% / 改后 13.8%），并要求回执列明残留会话与 token。其余验收不变。
- B 可改实现路径；不可改验收口径、写入范围、目标；范围外先停手扩合同。
- 不可行：1 轮内 `.pilot/C7/status.json` 置 `blocked` + 回执 ≤3 行原因，停手等 A 裁定。
## 11 回执
- 位置 `.pilot/C7/result.md`（≤10 行；首行 `session: <id> ｜ 状态: green|blocked`）；必含提交号 / 产物路径 / M1–M7 / **改前→改后 byRole 对比** / 风险 / 待确认；accepted 后取 `cost-after` 写 `.pilot/C7/cost.json`。
