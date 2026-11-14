# 交接文档（HANDOFF）

> 2026-11-14 07:3x · **收尾批**（纯 docs：HANDOFF / METRICS / ACTIONS / org 索引 / TEAM 小补；**1 条提交，已 push origin/master**）。
> 给新会话（新统筹主持）：先读本文件 + `docs/TEAM.md`（§二 重建 + §三·十 合同制）+ `docs/HANDOVER.md` + `docs/NATIVE_EMU_TODO.md`。
> **本文件是交接唯一真源，聊天记录不算。** 历史长文已迁出：更早的完整交接（F2/A–E 真机记录、T5 豁免对账）见 `git show 35b8fc7:docs/HANDOFF.md`，上一版见 `git show 2f258b0:docs/HANDOFF.md`；本文件只留最近 2–3 批摘要，不囤长文。

## 事实快照（2026-11-14 07:3x 实测）

- **HEAD / 推送**：本次**收尾 docs 提交**（`git log -1` 可查，避免自引用哈希）；**已 push origin/master**（2026-11-14 考官「可推送」后）→ `origin/master` = HEAD = 该提交、`origin/master..HEAD` = **0**；推送前 `origin/master` = `2f258b0`（前序 tools 合同制）。
- **工作树**：干净（本批提交后空）。
- **测试**：python **31/31**（考官复核实跑通过；`tools/test_results.json` 为 06:08 快照）；Kotlin 静态 **115**（`tools/test_results.json`；CI run `43458997942` 的构建步骤覆盖 `:app:testDebugUnitTest`）。
- **CI / 发布**：最近 master run `43458997942` = **success**（head `f4e8bf9`）；Release `build-f4e8bf947eec…`（C2 批次）已发。
- **审查**：最近完整审查 `docs/audit/REPORT-20261113.md` = **有条件通过**；冷却中（见「审查状态」）。
- **合同制**：C1 `c7538bb`、C2 `f4e8bf9` 均 **accepted**；2026-11-14 转常设（`docs/TEAM.md` §三·十）。

### C3 开工快照（2026-11-14 08:5x，B 实测）

- **HEAD / 推送**：HEAD `916fb2d`；`origin/master..HEAD` = 0；`git status --short` 仅未提交的合同 `docs/contracts/C3-token-optimization.md`（本批入库）。
- **测试 / 索引**：python 32/32（`python3 run_tests.py`，`tools/test_results.json` 同步）；kotlin 115（CI 快照）；`python3 tools/gen_files_index.py --check` = 0。
- **合同制**：C1、C2 已 accepted；C3 = 治理批 v1.3，state `claimed`（真机执行 + `emu_probe` + `cost_snapshot` + token 预算规则）。
- **下一步**：C3 执行（1 助理 + 1 考官，无工匠；tools/tests 由助理代做）；真机项 §7.3 由用户/A 执行；accepted 由 A 置。

## 当前目标

- 本批（收尾）：纯 docs 收口——重写 HANDOFF、重生成 METRICS、回填 ACTIONS 状态、org 索引、TEAM 三处小补、合同模板/PILOT 自检行、FILES 重生成、BATCHES 追加。**考官 2026-11-14 复核「可推送」（0 阻断），已 push origin/master**。
- 本批之后：已 push → **交接前置检查** → 交接（`TEAM` §二 + `HANDOVER` §二）；T5 前提见「审查状态」。
- 下一功能批建议：**合同制跑 A\* 6 图补采 + UI 入口**（见「下一步」）。

## 最近 3 批摘要

| 批次 | 提交 | 状态 |
|---|---|---|
| 合同制试点（C1/C2） | 试点落盘 `585918c`；C1 `c7538bb`；C2 `f4e8bf9` | 两合同 **accepted**；C1 离线测试 29/29；C2 三源一致 + CI `43458997942` + 真机证据；成本见「成本口径」 |
| 补账 + 合同制转常设 | `a17a1de`（补账 docs）、`809edfc`（转常设 docs）、`2f258b0`（tools） | 考官复核通过、已在 origin/master（`2f258b0`）；`BATCHES`/测试台账/FILES 已同步；`contract_check.py` + 9 例离线测试 |
| 本批（收尾 docs） | 本条（`git log -1` 可查） | 可推送（2026-11-14 复核，0 阻断）；本批 docs=1；授权留痕见 `docs/BATCHES.md` |

## 已完成（累积；除本批外全部已在 origin/master）

- 重建 P0/P1 + 批次 1–5：`history/`+`generated/` 分区、审查件归并 `docs/audit/`、F2 遗留、MainActivity 拆分 710→311、A\* 跨图库——提交号/CI/Release/真机见 `docs/BATCHES.md` 与 `docs/history/CHANGELOG.md`。
- 规范批 A-19（`2e70a67`/`1702ae3`）：写入范围补表、度量定义、T4 新口径。
- 工具整改批（`da9962a`/`a88fa4d`）：A-23（A-10 只扫暂存 + 输出命中行）、A-24（A-18 门禁收窄 + `--scope=b-team`）、A-21（METRICS 8 项）。
- 合同制试点 + 转常设：见上表；规则真源 `TEAM` §三·十，操作手册 `docs/contracts/PILOT.md`。

## 未完成 / 待办（精简）

1. **A\* 6 图补采 + UI 入口**：缺 assets 的 6 张图补 `map_links.json` 条目；无高度层；`side` 语义待真机；当前**无 UI 入口**（仅库 + 单测/CI）。
2. **A\* 实机对照**：Kotlin 决策 vs Python 版行为一致（需 UI 入口后做）。
3. **M4/M5 迁移 + 结构债**：M4 数据目录并入、M5 根 `.py` → `platform/`；`EmuView`/`WalkControl` 等零散逻辑可继续迁出（M3 已由 C1 完成）。
4. **名表 354**：招式名表 P3 仍不完整（C2 只补 232 单条，现 56 条；完整 354 缺数据源）。
5. **自动化开关**（工具页，需决策层接入）；**联机**（GBA link cable，方案待调研）。
6. **tag 瑕疵**：`build-5bbe4f4` tag 实际指向 `e54b240`（target_commitish 默认；构建覆盖仍含 `5bbe4f4`）。
7. **A-5**：`REQUEST` 必填模板已落（`a88fa4d`），**待独立督导确认**归属。

## 审查状态 / 豁免凭据

- **最近完整审查**：`docs/audit/REPORT-20261113.md`（窗口 `3decf36..ac26275`，45 提交）= **有条件通过**；3 条闭环前不得发下一版。整改现状：A-18/A-19/A-20/A-21/A-22/A-23/A-24 **已落地**（`3ba213d`/`2e70a67`/`da9962a` 等），A-5 **待独立督导确认**。
- **冷却**：两次完整审查间隔 ≥7 天 → **11-19 只做轻量复查**（按 REPORT §五 5 个复查点）、**下一次完整审查最早 2026-11-20**（用户 2026-11-13 13:46 拍板，`AUDIT_LOG`「11-19 复查安排与冷却重算」）。P0 / T6 / 新增复发可立即开审。
- **T5 交接前置审查**：须在冷却外审查或用户书面豁免；2026-11-13 已有 T5 豁免留痕（`AUDIT_LOG`）。11-19 前若交接，沿用豁免或结论标「降级采信」，**不得自行宣布豁免**。
- 本批未命中审查触发条件（纯 docs/台账；无 P0/T6/新增复发）。

## 下一步建议

1. 先取**考官轻量复核**（≤5 行：引用 / 一致性 / 索引）；结论写 `BATCHES` 末行 → 跑 `tools/precommit_check.sh --push` → push（**不 amend**）。
2. push 后跑 `HANDOVER` §二 11 项 → 交接（`TEAM` §二 重建新会话）。
3. 新会话第一批：**合同制**跑 A\* 6 图补采 + UI 入口（A 写合同 / B 执行；验收含真机步骤）；跨会话请求按 `REQUEST` §六 三字段填写（A-5）。
4. 功能候选：M4/M5 迁移、名表 354（先定数据源 + 去重口径）、自动化开关、联机。

## 不要做什么（最值钱）

- **不 amend / 不 force push 已推提交**；本批 1 条待推，push 前必 `git fetch` 对齐——共享工作树曾被并发推送连带（`BATCHES` 批次5 追记）。
- **不碰 keystore / 签名 / token**（轮换会导致已装 App 无法覆盖升级）；不碰 `docs/roles/b/**`。
- **不改 `docs/audit/**` 规则正文**（B 队所有；本批 ACTIONS 状态列属用户一次性授权回填）。
- **不改 `docs/history/` 旧文正文**；生成物（`FILES`/`METRICS`）只重跑脚本，**不手改**。
- **watcher 规则**：合同制 watcher 属 `HANDOVER` §二.8 豁免项，交接前 kill 并写「watcher 已 kill / 接管命令」；watcher 不可用时用**口令兜底**（重发转达句），不重复轮询。
- **HANDOFF 不囤长文**：只留最近 2–3 批摘要；历史见 `git show 35b8fc7:docs/HANDOFF.md`。
- **不伪造门禁/测试数字**（以 `tools/test_results.json`、`git`、CI run 为准）；不用空提交触发构建。
- **A-22 口径**：T4 看「窗口内新增复发」，不要用累计复发判红。
- 同会话 docs 常规 ≤1 条；只有用户明确「一次授权合批」才允许 2 条，且须 `BATCHES` 留痕。

## 成本口径

- 试点（C1/C2，2 批）：`cost-after`（06:07，accepted 后）− 基线 607,266,686 = **39,870,262**，÷2 ≈ **19.9M/批**；基线 **67,474,076/批**（≈67.5M），阈值 57.35M → **OK**。
- **`cost-after` 必须在 A 置 accepted 后取**（C2 教训：green 时快照作废）；基线按开工前当日窗口实测 ÷ 窗口批次数（不含本批），不写死。
- 本收尾批未单独核算；新会话按 `docs/contracts/PILOT.md` §六 测量法重取。

## 交接前置检查（`HANDOVER` §二 11 项现状）

| # | 项 | 现状 |
|---|---|---|
| 1 | `git status` 干净 | ✅ 本批提交后为空 |
| 2 | 提交已推送 | ✅ 本批 1 条已 push origin/master（2026-11-14 考官「可推送」后）；推送前 `origin/master` = `2f258b0` |
| 3 | CI 绿 | ✅ 最近 master run `43458997942` success；Release `build-f4e8bf9` |
| 4 | `run_tests.py` | ✅ python 35/35（C4 实跑）；Kotlin 115（`tools/test_results.json`，CI 覆盖） |
| 5 | TODO/CHANGELOG 与代码同步 | ⚠ 部分：TODO 名表条仍成立；C1/C2 无行为级 CHANGELOG 条目（C1 纯测试迁移、C2 数据补条），待督导定是否补记 |
| 6 | `gen_files_index.py` 重生成 + `--check` | ✅ 重生成后 `--check` = 0（本批执行） |
| 7 | 本文件更新 | ✅ 本批（按 `HANDOVER` §三 模板重写） |
| 8 | 无未结束 job / 子代理；watcher | ✅ 本批无后台 job/子代理；无 watcher 运行 |
| 9 | `precommit_check.sh --push` | ✅ push 前已跑（exit 0，带 `EXAMINER_OK`） |
| 10 | Kotlin UI 改动 → `check_ui_state.py` | ✅ 本批无 Kotlin 改动（历史 34 文件全配对） |
| 11 | 机械闸门已装 | ✅ `.git/hooks/pre-commit` + `pre-push` 都在 |

## 接手 5 分钟

```bash
cd /root/workspace
git status --short                         # 期望空（队友未提交文件除外，不要 add -A）
git log -3 --oneline                       # 期望含本收尾 docs 条
git rev-list --count origin/master..HEAD   # 等考官期间 = 1；push 后 = 0
python3 run_tests.py                       # 数量以 tools/test_results.json 为准
python3 tools/gen_files_index.py --check   # 期望 0
```

## 构建 / 发布现状

- 最新发布：`build-f4e8bf947eec…`（C2；CI `43458997942` success）；上一版 `build-5bbe4f4…`（批次5）、`build-112817b…`（批次4）保留。
- tag→提交映射与构建覆盖看 `docs/generated/METRICS.md`；CI 仅在推送含 `native-emu/**` 时构建（按推送 tip 打 tag；`build-5bbe4f4` 指向 `e54b240` 属已知瑕疵）。

## 旧路径豁免清单（grep 口径，B 队已确认）

(a) `docs/history/` 内正文；(b) `git show <旧提交>:<旧路径>` 历史引用；(c) `docs/org/PLAN-*` 等已定稿旧记录；(d) 历史台账正文不回改（`AUDIT_LOG` 3 处、`REPORT-20261112` 1 处）。工作树**活体**文档/工具/脚本旧路径 = 0。

## C4 治理批收尾（2026-11-14，v1.4）

- **合同**：`docs/contracts/C4-closeout-v14.md`（治理批；单提交，提交号见 `git log -1`；未 push，等考官「可发布」后由 B push）。
- **本批产物**：`tools/cost_snapshot.py --before`（开工前基线 `.pilot/<id>/cost-before.json`：windowTotal / batches / baselinePerBatch / threshold）；新 `tools/contract_close.py <id>`（accepted 后打印 BATCHES 追记 / HANDOFF 摘要 / METRICS 重生成提示 / cost 摘要，不写台账）；`contract_check` claimed 缺 cost-before 警告（C5 起阻断）；TEAM §三·十二 增 4 条规则；CONTRACT-TEMPLATE §12 启动提示词骨架。
- **真机（realdevice）**：`python3 tools/emu_probe.py --check-move 232 --expect-name 金属爪` → `PASS 232 金属爪`；截图 `/sdcard/Download/DSH-Go/probe-232-20261114-1130.jpg`（emu_probe 只读不截屏，由执行者截）。
- **门禁**：`contract_check` / `batch_facts` / `batch_close --dry-run` / `run_tests.py` / `gen_files_index.py --check` / `metrics.py --check` 全过（数字以 `tools/test_results.json` 为准，不写死）。
- **下一步计划：C5 旧方案归档**——停用旧主流程、旧职位引用清理、全局 `~/.dsh/AGENTS.md` 同步、审计/督导归属待用户拍板。
