# 交接文档（HANDOFF）

> 2026-11-14 14:1x · **C7 成本归因修复（治理小批 v1.7）收尾**：**2 条提交**（主提交 `17248b5` 已 push 且 accepted；本**收尾提交**〔BATCHES 追记 + HANDOFF 收尾 + METRICS/FILES 重生成〕**待考官 examiner3 轻量复核后 push**）；不 amend、不 `--no-verify`。
> 给新会话（新代理人）：先读本文件 + `docs/TEAM.md`（§二 重建 + §三·十 合同制 + §三·十一/十二 现行流程）+ `docs/HANDOVER.md` + `docs/NATIVE_EMU_TODO.md`。
> **本文件是交接唯一真源，聊天记录不算。** 历史长文已迁出：更早的完整交接（F2/A–E 真机记录、T5 豁免对账）见 `git show 35b8fc7:docs/HANDOFF.md`，上一版见 `git show 2f258b0:docs/HANDOFF.md`；本文件只留最近 2–3 批摘要，不囤长文。

## 事实快照（2026-11-14 14:1x，C7 收尾提交前）

- **HEAD / 推送**：主提交 `17248b5` 已 push 且 accepted（`origin/master`=HEAD=主提交）；本批 C7 **收尾提交**（`git log -1` 可查）待考官 examiner3 轻量复核后 push；push 前 `origin/master..HEAD` = 1。
- **测试**：python **37/37**（`tools/test_results.json`；C7 实跑 **14:07:40–14:09:04** Asia/Shanghai，含新 `tests/test_token_roles.py` 6 例）；Kotlin 静态 **115**（CI 快照，本批无 Kotlin 改动）。
- **索引**：`python3 tools/gen_files_index.py --check` = 0；`docs/generated/FILES.md` / `METRICS.md` 收尾重生成（生成时 HEAD=`17248b5`，之后新增收尾提交属正常）。
- **审查**：最近完整审查 `docs/audit/REPORT-20261113.md` = **有条件通过**；冷却中（见「审查状态」）。本批治理批纯 tools/tests/docs，未命中审查触发。
- **合同制**：**C1–C7 全 accepted**——C1 `c7538bb`、C2 `f4e8bf9`、C3 `d3baeab`（15.0M ≤ 阈 21.3M）、C4 `36a28c1`（20.4M 记超，已复盘）、C5 `779dac6`（14.4M ≤ 阈 19.9M）、C6 `a0763bb`（13.1M ≤ 阈 19.6M）、**C7 `17248b5`（23.5M 记超，≤30M ✓；复盘待 C8）**。

## 当前目标

- 本批（C7 收尾）：收尾提交待考官 examiner3 轻量复核「可发布」→ push（**不 amend**）；复核要点：BATCHES 追记 / HANDOFF 收尾 / METRICS 重生成 / 百分比快照时刻标注。
- 本批之后：**C8**（A 职责边界同步：A 只派发与审核、不代跑工具/git；C7 成本复盘件落盘待用户批准）→ 跑 `HANDOVER` §二 11 项 → 交接（`TEAM` §二 重建）。
- 下一批建议：见「下一步建议」。

## 最近 3 批摘要

| 批次 | 提交 | 状态 |
|---|---|---|
| C5-旧方案归档 v1.5 | `779dac6` + 收尾 `2a4a551` | accepted；cost 14.4M ≤ 阈 19.9M、≤30M ✓（双判据 ✓）；均已 push |
| C6-治理工具批 v1.6 | `a0763bb` + 收尾 `a9604b8` | accepted；cost 13.1M ≤ 阈 19.6M、≤30M ✓（双判据 ✓）；均已 push |
| C7-成本归因 v1.7 | `17248b5` + 收尾提交（`git log -1` 可查） | accepted；cost **23.5M 记超**（> 阈 19.4M、≤30M ✓；复盘待 C8）；主提交已 push、收尾提交待考官后 push；M5 未知职位 29.4%→13.36%（A 裁定口径 <15%）；授权留痕见 `docs/BATCHES.md` |

## 已完成（累积；除本批外全部已在 origin/master）

- 重建 P0/P1 + 批次 1–5：`history/`+`generated/` 分区、审查件归并 `docs/audit/`、F2 遗留、MainActivity 拆分 710→311、A\* 跨图库——提交号/CI/Release/真机见 `docs/BATCHES.md` 与 `docs/history/CHANGELOG.md`。
- 规范批 A-19（`2e70a67`/`1702ae3`）：写入范围补表、度量定义、T4 新口径。
- 工具整改批（`da9962a`/`a88fa4d`）：A-23（A-10 只扫暂存 + 输出命中行）、A-24（A-18 门禁收窄 + `--scope=b-team`）、A-21（METRICS 8 项）。
- 合同制试点 + 转常设：见上表；规则真源 `TEAM` §三·十，操作手册 `docs/contracts/PILOT.md`。

## 未完成 / 待办（精简）

1. **A\* 6 图补采 + UI 入口**：缺 assets 的 6 张图补 `map_links.json` 条目；无高度层；`side` 语义待真机；当前**无 UI 入口**（仅库 + 单测/CI）。
2. **A\* 实机对照**：Kotlin 决策 vs Python 版行为一致（需 UI 入口后做）。
3. **M4/M5 迁移 + 结构债**：M4 数据目录并入、M5 根 `.py` → `platform/`；`EmuView`/`WalkControl` 等零散逻辑可继续迁出（M3 已由 C1 完成）。
5. **名表 354**：招式名表 P3 仍不完整（C2 只补 232 单条，现 56 条；完整 354 缺数据源）。
6. **自动化开关**（工具页，需决策层接入）；**联机**（GBA link cable，方案待调研）。
7. **tag 瑕疵**：`build-5bbe4f4` tag 实际指向 `e54b240`（target_commitish 默认；构建覆盖仍含 `5bbe4f4`）。
8. **A-5**：`REQUEST` 必填模板已落（`a88fa4d`），**待审计督导确认**归属。
8. **`tools/write_scopes.json` 镜像 TEAM §一 编制**：**C6 已对齐**（删旧 4 角色 / 增「审计督导」），本项闭环；`tests/test_write_scopes.py` 做离线一致性守护。

## 审查状态 / 豁免凭据

- **最近完整审查**：`docs/audit/REPORT-20261113.md`（窗口 `3decf36..ac26275`，45 提交）= **有条件通过**；3 条闭环前不得发下一版。整改现状：A-18/A-19/A-20/A-21/A-22/A-23/A-24 **已落地**（`3ba213d`/`2e70a67`/`da9962a` 等），A-5 **待审计督导确认**。
- **冷却**：两次完整审查间隔 ≥7 天 → **11-19 只做轻量复查**（按 REPORT §五 5 个复查点）、**下一次完整审查最早 2026-11-20**（用户 2026-11-13 13:46 拍板，`AUDIT_LOG`「11-19 复查安排与冷却重算」）。P0 / T6 / 新增复发可立即开审。
- **T5 交接前置审查**：须在冷却外审查或用户书面豁免；2026-11-13 已有 T5 豁免留痕（`AUDIT_LOG`）。11-19 前若交接，沿用豁免或结论标「降级采信」，**不得自行宣布豁免**。
- 本批（C6）未命中审查触发条件（治理批纯 tools/tests/docs；无 P0/T6/新增复发）。

## 审计留痕（C6 正式执行）

- 2026-11-14 前两次执行会话（contractor2 中断 / contractor3 自行提交 `afe4997`）经**用户判定「仅测试目的」**；A 按用户指示执行 `git reset --soft 2a4a551` 撤销该测试提交，工作内容 16 文件原样保留为暂存改动，随后由 contractor4 **正式执行**并单提交 `a0763bb`（before `2a4a551`）。
- `afe4997` **不在提交历史**（`git log` 查无）；仅 reflog / `.pilot/C6/status.json` history 可查，**不计入度量与审计样本**；本批验收只认 `a0763bb` 与收尾提交（前两次会话回执/提交不作验收依据）。

## 下一步建议

1. 先取**考官 examiner3 轻量复核**（三查：事实 / 引用一致性 / 越权范围 + 抽 1 条命令复跑）；结论写 `BATCHES` 追记 → 跑 `tools/precommit_check.sh --push`（带 `EXAMINER_OK`）→ push 收尾提交（**不 amend**）。
2. push 后跑 `HANDOVER` §二 11 项 → 交接（`TEAM` §二 重建；新会话＝代理人 + 合同制重建）；C7 `cost-after` 已取（23.5M，accepted 后）。
3. **C8（下一批）**：A 职责边界同步（A 只派发与审核、不代跑工具/git）+ **C7 成本复盘件落盘**（`docs/history/**` 属 C8，待用户批准后由 B 执行）+ 测试内 `OLD_PATTERNS` 同批维护提示。
4. **功能批（新会话第一批）**：合同制跑 A\* 6 图补采 + UI 入口（A 写合同 / B 执行；验收含真机步骤）；跨会话请求按 `REQUEST` §六 三字段填写（A-5）。
5. **治理建议收口状态（C5 考官 3 条 + A 补 3 项）**：
   ① `tools/write_scopes.json` 同步新编制 → **C6 已闭环**；
   ② `contract_close` 追记文案（「待考官→B push」与已 push 事实不符）→ **C6 已闭环**（尾句按 status push 事实）； 
   ③ `contract_check` 花括号 → **C6 已闭环**（支持 `{a,b}` 展开 + 3 用例；合同 §8 仍写显式路径）；
   ④ `status.json` 时间戳精确到分钟 → **C6 已规范**（`TEAM` §三·十二 + `CONTRACT-TEMPLATE` §11：`YYYY-MM-DD HH:MM`）；
   ⑤ R3 spawn 显式标职位 → **C6 已规范**（`TEAM` §三·十二：`description` 中文职位开头）；
   ⑥ `docs/audit/**` 正文归 A 队后的旧名清理 → 待 A 队（非本批）。
6. **剩余治理项（C6 收尾）**：docs 分组口径已修（16=docs 7+5+4，考官建议①）；status 时间戳已精确到分钟（A 侧 `openedAt` 12:42）；METRICS/FILES 已在收尾重生成（HEAD 含 `a0763bb`）。
7. **R3 收口（C7 byRole）**：主因已修——`tools/token_report.mjs` 的 `ROLE_PATTERNS` 由旧 9 岗位补为 **11 规范角色**（旧名兼容：统筹主持·执行主管→代理人 / 独立督导·审查员·成本管理员→审计督导 / builder→工匠 / steward→助理 / verifier→考官），「未知职位」53,364,702（29.4%）→ **26,064,054（13.6%）**；残留 26.06M **仅 2 个 label 无任何职位词的 C1/C2 试点会话**（`落盘合同制试点最小集` 20,121,510 + `轻量复核试点落盘提交` 5,942,544），按合同 §7.2 不造映射、如实记录；**避免措施：新会话 spawn 显式标职位**（`TEAM` §三·十二）。观察项转下批验证（windowTotal 差额仅记录，不判红）。
8. 功能候选：M4/M5 迁移、名表 354（先定数据源 + 去重口径）、自动化开关、联机。

## 不要做什么（最值钱）

- **不 amend / 不 force push 已推提交**；本批主提交 1 条待推，push 前必 `git fetch` 对齐——共享工作树曾被并发推送连带（`BATCHES` 批次5 追记）。
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
- **C3**：perBatch **15.0M** ≤ 阈 21.3M（双判据 ✓）。
- **C4**：perBatch **20.4M** > 阈 20.0M（记超，已复盘 `RETROSPECTIVE-20261114-C4-cost.md`）。
- **C5**：perBatch **14.4M**（delta 14,427,176 / batches 1）≤ baseline×0.85 = 阈 **19.9M**（72.6%）且 ≤30M → **未记超（R2 ✓）**；累计 C4 20.4M / C5 14.4M。
- **C6**：perBatch **13.1M**（delta 13,090,066 / batches 1）≤ baseline×0.85 = 阈 **19.6M**（为基线 56.8%）且 ≤30M → **未记超（双判据 ✓）**；累计 C4 20.4M / C5 14.4M / C6 13.1M，三批均值 ≈ **16.0M/批**。
- **C7**：perBatch **23.5M**（delta 23,534,117 / batches 1；`cost-after` 快照 14:09，窗口含本批会话）> 阈 **19.4M**（超 21.6%）且 ≤30M/批 → **记超（双判据未全过，须复盘）**；基线 22,770,908（cost-before windowTotal 182,167,266 / batches 8）。
- **#10 汇总（METRICS 重生成 2026-11-14 14:1x）**：accepted 合同 cost 均值 **17.3M/批；超阈值 2/5**（C4 20.4M、C7 23.5M 记超）；#9 合同一次通过率 **7/7 = 100%**。
- 新会话按 `docs/contracts/PILOT.md` §六 测量法重取；`cost-after` 必须在 accepted 后取。

## 复盘状态（C7 记超）

- C7 perBatch **23.5M** > 阈 19.4M（超 21.6%，≤30M ✓）→ **记超 + 复盘**（C4 先例）；**不阻断收尾**，accepted 保持有效。
- 复盘要点：① A 原写 M5「<10%」不可达（残留 26.06M 为 2 个无职位词的 C1/C2 试点会话）→ blocked 一轮往返；② 本批含「执行 + blocked→resume」多轮，B 会话成本计入；③ A 侧长文/取证推高主会话份额。
- 复盘件属 `docs/history/**`（C7 §8 禁改）→ **并入 C8，待用户批准后由 B 执行**；本批不落盘。

## 考官建议（C7 主提交复核）

1. **百分比快照口径**：M5/byRole 百分比须标快照时刻 → 本收尾已标注「快照 14:09 / 窗口含本批会话」。
2. **M2 实跑证据**：已补 `python3 run_tests.py` 实跑时间（14:07:40–14:09:04，37/37）。
3. **测试内 `OLD_PATTERNS` 副本**：`tests/test_token_roles.py` 内的旧表副本须与 `token_report.mjs` 映射同批维护 → 写进下批提示。

## 交接前置检查（`HANDOVER` §二 11 项现状）

| # | 项 | 现状 |
|---|---|---|
| 1 | `git status` 干净 | ✅ 本批提交后为空（`.pilot/` 已 gitignore） |
| 2 | 提交已推送 | ⏳ C7 **收尾提交**待考官 examiner3「可发布」后 push（push 后 `origin/master..HEAD` = 0）；主提交 `17248b5` 已 push 且 accepted |
| 3 | CI 绿 | ✅ 最近 master run `43458997942` success；Release `build-f4e8bf9`（本批纯 docs/tools/tests，不触发 CI） |
| 4 | `run_tests.py` | ✅ python **37/37**（`tools/test_results.json`；C7 实跑 14:07:40–14:09:04，新增 `test_token_roles` 6 例）；Kotlin 115（CI 覆盖） |
| 5 | TODO/CHANGELOG 与代码同步 | ⚠ 部分：TODO 名表条仍成立；C1/C2 无行为级 CHANGELOG 条目（C1 纯测试迁移、C2 数据补条），待审计督导定是否补记 |
| 6 | `gen_files_index.py` 重生成 + `--check` | ✅ 重生成后 `--check` = 0（本批执行） |
| 7 | 本文件更新 | ✅ 本批（C7 收尾：事实快照 / 摘要 / 成本口径 / 复盘状态 / 考官建议 / 下批清单） |
| 8 | 无未结束 job / 子代理；watcher | ✅ 本批无残留后台 job/子代理（执行会话 fresh 直执；收尾阶段 metrics/FILES 重生成已结束）；无 watcher 运行 |
| 9 | `precommit_check.sh --push` | ⏳ 收尾提交 push 时执行（考官「可发布」后带 `EXAMINER_OK`）；主提交 push 时已过（exit 0） |
| 10 | Kotlin UI 改动 → `check_ui_state.py` | ✅ 本批无 Kotlin 改动（历史 34 文件全配对） |
| 11 | 机械闸门已装 | ✅ `.git/hooks/pre-commit` + `pre-push` 都在 |

## 接手 5 分钟

```bash
cd /root/workspace
git status --short                         # 期望空（队友未提交文件除外，不要 add -A）
git log -3 --oneline                       # 期望含 C7 主提交 17248b5 + 收尾提交
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

- **合同**：`docs/contracts/C4-closeout-v14.md`（治理批；单提交 `36a28c1`；已 accepted 并 push origin/master；cost perBatch 20.4M 记超，复盘见 `docs/history/RETROSPECTIVE-20261114-C4-cost.md`）。
- **本批产物**：`tools/cost_snapshot.py --before`（开工前基线 `.pilot/<id>/cost-before.json`：windowTotal / batches / baselinePerBatch / threshold）；新 `tools/contract_close.py <id>`（accepted 后打印 BATCHES 追记 / HANDOFF 摘要 / METRICS 重生成提示 / cost 摘要，不写台账）；`contract_check` claimed 缺 cost-before 警告（C5 起阻断）；TEAM §三·十二 增 4 条规则；CONTRACT-TEMPLATE §12 启动提示词骨架。
- **真机（realdevice）**：`python3 tools/emu_probe.py --check-move 232 --expect-name 金属爪` → `PASS 232 金属爪`；截图 `/sdcard/Download/DSH-Go/probe-232-20261114-1130.jpg`（emu_probe 只读不截屏，由执行者截）。
- **门禁**：`contract_check` / `batch_facts` / `batch_close --dry-run` / `run_tests.py` / `gen_files_index.py --check` / `metrics.py --check` 全过（数字以 `tools/test_results.json` 为准，不写死）。
- **下一步计划**：C5 旧方案归档（已执行，见下节）；之后按「下一步建议」推进 A\* 6 图 + UI 入口。

## C5 治理批收尾（2026-11-14，旧方案归档 v1.5）

- **合同**：`docs/contracts/C5-legacy-archive.md`（治理批；本批 **2 条提交**：主批 `779dac6`（已 push）+ 收尾提交（合同 §8 显式路径修正 + BATCHES 追记 + HANDOFF/METRICS），待考官轻量复核后 push）。
- **合同 C5 摘要**：提交 `779dac6`；cost perBatch=14.4M；≤阈值 19.9M；≤30M/批（双判据 ✓，R2 通过）；contract_check exit 0；已 push（origin/master=779dac6）；METRICS 已重生成（#9/#10 计入 C5）。
- **§8 修正（A 侧）**：A 置 accepted 时 `contract_check` 报 5 个角色卡越权——根因 `§8` 用 `{assistant,artisan,examiner}` 花括号、`contract_check` 不展开 `{}`；实际授权无问题。A 已展开为显式路径并在 §10 留痕（合同 55 行），accepted 态复跑 exit 0；本收尾提交纳入。
- **C4 复盘验收（R1–R5）**：R1 ✓（C4 accepted 关闭未重开，追记已入 `BATCHES`）；**R2 ✓**（C5 perBatch 14.4M ≤ 阈 19.9M，未记超）；**R3 ✗ 观察**（`byRole` 未标注 / 未知职位 23.9% > 10%，窗口含 C3/C4 遗留会话，本批不可控 → 下批 spawn 显式标职位）；R4 顺延（本批无真机项）；R5 ✓（`metrics.py --check` exit 0，记超只记数不阻断）。
- **归零项（旧口径 → 合同制）**：
  - **旧主流程**：`TEAM` §三 12 步正文 → `docs/archive/TEAM-主流程-12步-20261112.md`（只移动、逐字未改）；§三 原位留 3 行指向 §三·十一 / §三·十二；§二 重建步骤改合同制口径。
  - **旧职位引用**：活体文档中「统筹主持 / 独立督导（B 队）」与旧执行岗口径清零（`M5` grep 空；`M4` literal 仅命中 §6 豁免区与合同 spec 自身引用）；保留助理 / 工匠 / 考官 / 真机执行（B 成员沿用）。
  - **审计 / 督导归属**：归 A 队——新增 `docs/roles/a/supervisor.md`（代理人按需 spawn、fresh、只读、≤5 行回执、按 `docs/audit/AUDIT.md` 触发）；`docs/roles/README.md` 与 `docs/roles/b/audit-lead.md` 标停设；`TEAM` §四 补归属句；`docs/audit/**` 正文未动。
  - **全局** `/root/.dsh/AGENTS.md`：先备份 `AGENTS.md.bak-20261114` → 删首行受管标记 → 只换「会话寿命与角色分工」段为合同制口径（不入库）。
- **已知偏差 / 待确认**：① 本环境 B 无 spawn 权，助理 / 考官由 Lead 另起 fresh 会话承担，本批执行与提交由 B 直执；② `M4` 原命令未排除 §6 豁免区，已按 §6 豁免口径执行；A 2026-11-14 12:3x 修订 M4 命令（合同 §10 变更行，限活体文件，实测空）；③ `tools/write_scopes.json` 镜像 TEAM §一 旧编制，本批 §8 不允许改，待下批。

## C6 治理工具批收尾（2026-11-14，v1.6）

- **合同**：`docs/contracts/C6-governance-tools.md`（机械型，1 批，无真机项；本批 **2 条提交**：主提交 `a0763bb`（已 push + accepted）+ 收尾提交（BATCHES 追记 + HANDOFF 收尾 + METRICS/FILES 重生成，待考官后 push））。
- **合同摘要**：提交 `a0763bb`；cost perBatch=13.1M；≤阈值 19.6M；≤30M/批（双判据 ✓）；contract_check exit 0；已 push（origin/master=a0763bb）；考官已复核（可发布，0 阻断）。
- **WBS ①–⑥**：① `tools/write_scopes.json` 对齐 `TEAM` §一新编制（删旧 4 角色 / 增「审计督导」）+ 新 `tests/test_write_scopes.py`（4 例）；② `contract_check.in_scope` 支持 `{a,b}` 展开（多组；非法/空项回退字面匹配）+ 测试 +3；③ `contract_close` 追记尾句按 status push 事实（有记录→已 push + 考官已复核；无→待考官→B push）+ 测试 +1；④ `batch_facts` 解析 `> 合同收尾追记…` 优先显示（无则回退末表行）+ 测试 +2；⑤ `TEAM` §三·十二 增 spawn 显式标职位 / status 时间格式，`CONTRACT-TEMPLATE` §8 禁 `{a,b}` / §11 时间格式；⑥ 台账（BATCHES `合同:C6` / test_results / FILES / METRICS / 本文件）。
- **门禁**：`contract_check`（C6）/ `batch_facts` / `batch_close --dry-run` / `run_tests.py` / `gen_files_index --check` / `metrics --check` 全过；M1–M7 全过（M7 改动全部落 §8）。
- **判断项**：花括号展开不破坏既有字面 / `/**` / glob（原 14 例 + 新 3 例全过）；追记解析无追记行回退末表行不崩；`write_scopes` 与 `TEAM` §一 逐条一致（测试守护）。
- **收尾修正**：考官建议① docs 分组 6→7（16=7+5+4，总数无误）；② status `openedAt` 由 A 改精确 12:42；③ METRICS/FILES 在收尾重生成（HEAD 已含 `a0763bb`）。
- **偏差 / 待确认**：本环境 B 无 spawn 权，助理 / 考官由 Lead 另起 fresh 会话承担，执行与提交由 B 直执；`cost-after` 已取（13.1M，accepted 后）；`afe4997` 测试提交已由 A `reset --soft` 撤销（见「审计留痕」）。

## C7 成本归因修复收尾（2026-11-14，治理小批 v1.7）

- **合同**：`docs/contracts/C7-token-roles.md`（机械型，1 批，无真机项；**2 条提交**：主提交 `17248b5`（已 push + accepted）+ 收尾提交（BATCHES 追记 + HANDOFF 收尾 + METRICS/FILES 重生成，待考官 examiner3 轻量复核后 push）；不 amend / 不 push 半成品）。
- **本批产物**：`tools/token_report.mjs` 的 `ROLE_PATTERNS` 改为 11 规范角色（与 `tools/write_scopes.json` 同集；旧名兼容映射；取最靠左 / 无 descriptor→主会话规则不变）+ `--roles` 机读输出 + 新 `tests/test_token_roles.py`（6 例纯离线，含同 fixture 映射前后 totals 相等）+ `TEAM` §三·十二「成本归因唯一映射」+ 台账。
- **M5（A 裁定口径 <15%，快照 14:09、窗口含本批会话）**：未知职位 53,364,702（29.4%）→ 26,064,054（13.36%）；残留仅 2 个 label 无职位词的 C1/C2 试点会话（`落盘合同制试点最小集` 20,121,510 / `轻量复核试点落盘提交` 5,942,544），如实记录、不造映射；windowTotal 差额仅记录（新增会话）。
- **成本**：perBatch **23.5M**（delta 23,534,117 / batches 1）> 阈 19.4M（超 21.6%）、≤30M/批 ✓ → **记超，须复盘**（不阻断收尾；复盘件并入 C8，`docs/history/**` 本批 §8 禁）。
- **门禁**：`contract_check`（C7）/ `batch_facts` / `batch_close --dry-run` / `run_tests.py` 37/37（实跑 14:07:40–14:09:04）/ `gen_files_index --check` / `metrics --check` 全过；M1–M7 全过（M7 改动全部落 §8；M5 按修订口径）；`contract_close C7` 仅 cost 项 FAIL（记超，非流程阻断）。
- **偏差 / 待确认**：① 本环境 B 无 spawn 权→无助理/考官，执行与提交由 B 直执、Lead 另起 fresh 考官复核；② M5 原 `<10%` 不可达，A 已修订为 `<15%` 并在合同 §10 留痕（2026-11-14 13:2x）；③ `cost-after` 已取（14:09，23.5M 记超）；④ 复盘件待 C8。
