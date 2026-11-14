# C9 遗留收口小批：HANDOFF 文字更正 + 组织文档矛盾 + metrics 数据源行
> 归属：A 队 ｜ 生命周期：活（常设合同） ｜ 维护者：A（proxy）
> 类型：机械型（无真机项）｜ 1 批（治理小批 v1.9）｜ 状态机 `open→claimed→green|blocked→accepted`（运行态 `.pilot/C9/`）
## 1–2 合同号 / 类型
C9 ｜ 机械型；1 批；验收按 §7 分列。来源：C8 考官 2 条文字更正 + B 1 条候选 + 组织文档矛盾（A 检查发现）。
## 3 事实快照（2026-11-14 14:5x 实测）
- `origin/master`=HEAD=`5be668a`；工作树空；未推送 0；C1–C8 全 accepted，无其它 open 合同。
- `docs/HANDOFF.md:106` C7 复盘 R4 写「顺延（C8 无真机项）」——但 C7 复盘 R4 判据是「C8 执行过程无 blocked→resume」（`RETROSPECTIVE-20261114-C7-cost.md:38`），C8 为 14:36 claimed→14:45 green、无 blocked → 应记 **✓**。
- `docs/HANDOFF.md:117` 缓存注记写「14:11 缓存快照」，隐含 14:47 重生成仍走缓存；实测 C8 收尾 METRICS 14:47 生成已实时抓取（`ci_runs_cache.json` fetchedAt=14:48），14:11 缓存属 14:43 主提交那次 → 措辞需更正；`:203` 同步。
- `docs/roles/README.md:8-10` 把 助理/工匠/考官 标「A 队」，与 `docs/TEAM.md` §一 1.2「承包商（B 成员沿用）」矛盾。
- `tools/metrics.py` 内部有 `source`（"live" 或 "cache(…)"）但不固定输出「数据源」行；无 `tests/test_metrics.py`。
## 4 基线提交
- B claim 后第一件事：`python3 tools/cost_snapshot.py --before C9` 写 `.pilot/C9/cost-before.json` 并回四字段；base=开工前 `git rev-parse HEAD`（应=5be668a）；status 置 claimed（session/attempts=1），保留 A 写的 open 字段。
## 5 背景与目标
C8 关闭后遗留 4 项非阻断问题（2 条考官更正、1 条 B 候选、1 条组织文档矛盾）。目标：一次小批收口，避免文字失真与两表冲突；不动实现、不动已推台账正文。
## 6 任务清单（WBS）
- ① **HANDOFF 文字更正**（改 `docs/HANDOFF.md` 正文，不回改 BATCHES 历史追记）：
  - `:106` R4 改「✓（C8 无 blocked→resume：14:36 claimed→14:45 green）」；
  - `:117` 缓存注记改「C8 主提交（14:43）生成走 14:11 缓存；收尾重生成（14:47）已实时抓取（`ci_runs_cache.json` fetchedAt=14:48）；以该次为准」；
  - `:203` 同步措辞。
- ② **组织文档矛盾**：
  - `docs/roles/README.md` 表 助理/工匠/考官 行「A 队」→「B 成员（承包商 spawn）」；B 队停设三行保留；
  - `docs/TEAM.md` §一 1.1 增环境例外注：「本环境仅会话主持可 spawn；B 无 spawn 权时由代理人派发子会话并在 `description` 标中文职位（须用户/合同授权）」。
- ③ **metrics 数据源行**：`tools/metrics.py` 在 `--check` 与常规输出的 CI/#2/#3 相关段固定打印「数据源：live」或「数据源：cache(<fetchedAt>)」；**不改 `--json` 字段结构**；新增 `tests/test_metrics.py`（≥2 例纯离线：live 分支、cache 分支，用 fixture/假缓存文件，不联网）。
- ④ 台账：`BATCHES` 行（`合同:C9`）+ `test_results` 同步 + `FILES`/`METRICS` 重生成 + `HANDOFF` 收尾（本批摘要 + 下批候选）。
## 7 验收
### 7.1 机械项
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 tools/contract_check.py --contract docs/contracts/C9-hygiene.md --status .pilot/C9/status.json` | exit 0 |
| M2 | `python3 run_tests.py` | exit 0，38/38（新增 `test_metrics.py`） |
| M3 | `python3 tools/gen_files_index.py --check` | exit 0 |
| M4 | `grep -n "R4" docs/HANDOFF.md \| head -1` | 含「无 blocked→resume」且不含「顺延（C8 无真机项）」 |
| M5 | `grep -n "助理" docs/roles/README.md \| head -1`；`grep -c "会话主持可 spawn" docs/TEAM.md` | 行含「B 成员」，不含「A 队」；TEAM ≥1 |
| M6 | `grep -c "数据源：" tools/metrics.py`；`test -f tests/test_metrics.py` | ≥1；存在，且用例 ≥2 |
| M7 | `git diff --name-only <base>..HEAD` | 全部落 §8 |
### 7.2 判断项
- HANDOFF 更正后与 C7 复盘 R1–R5 定义、`ci_runs_cache.json` fetchedAt 一致（不编造时刻）；roles/README 与 TEAM 1.2 一致、B 队停设行保留；metrics 数据源行不改变现有文本/JSON 输出结构（`--json` 字段不变）。A 只读回执+路径，至多 2 条只读抽验。
### 7.3 真机项
- 无（纯 docs/tools 小改）。
### 7.4 成本判据（双判据）
- 每批增量 ≤ 基线×0.85 且 ≤30M/批；基线 `.pilot/C9/cost-before.json`（B claim 首步落）；`cost-after` 由 B 在 A 置 accepted 后取。
## 8 写入范围
- 允许：`docs/contracts/C9-hygiene.md`、`docs/HANDOFF.md`、`docs/roles/README.md`、`docs/TEAM.md`、`tools/metrics.py`、`tests/test_metrics.py`（新）、`docs/BATCHES.md`、`docs/generated/FILES.md`、`docs/generated/METRICS.md`（经脚本）、`tools/test_results.json`
- 不允许：C1–C8 合同与 `PILOT.md`、`docs/audit/**`、`docs/roles/a|b|org` 角色卡正文、`docs/history/**`、`native-emu/**`、`tools/` 其他文件、keystore；`.pilot/**` 不入库
## 9 禁止项
- 不回改 `BATCHES` 历史追记与 `docs/history/**` 正文（文字更正只改 HANDOFF 现状段）；不改 C1–C8 合同；不伪造缓存时刻/测试数字。
- 治理批 1 助理 + 1 考官（本环境 B 无 spawn 权时由 Lead 起考官）；无工匠、无真机项。
## 10 变更规则
- B 可改实现路径；不可改验收口径、写入范围、目标；范围外先停手扩合同。
- 不可行：1 轮内 `.pilot/C9/status.json` 置 `blocked` + 回执 ≤3 行原因，停手等 A 裁定。
## 11 回执
- 位置 `.pilot/C9/result.md`（≤10 行；首行 `session: <id> ｜ 状态: green|blocked`）；必含提交号 / 产物路径 / cost-before 四字段 / M1–M7（命令+输出摘要）/ 判断项依据 / 风险 / 待确认；accepted 后取 `cost-after` 写 `.pilot/C9/cost.json`。
