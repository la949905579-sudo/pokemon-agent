# 交接文档（HANDOFF）

> 2026-11-13 14:0x · 批次 5 收尾（含跨会话并发事实；docs 收尾待推送）
> 给新会话（新统筹主持）：先读本文件 + `docs/TEAM.md`（§二 重建步骤）+ `docs/HANDOVER.md` + `docs/NATIVE_EMU_TODO.md`。
> **本文件是交接唯一真源，聊天记录不算。** 历史长文已迁出：上一版交接（F2/A–E 真机记录、T5 豁免对账）见 `git show 35b8fc7:docs/HANDOFF.md`。

## 交接（2026-11-13 14:0x）

- **事实快照（含跨会话并发）**：`origin/master` = `e54b240`；其上另有 B 队 `5bbe4f4`（A-22：T4 判据改「窗口内新增复发>0」+ 口径）与 `e54b240`（A-23：门禁误报）。**B 队推 `5bbe4f4` 时连带把我们的 `3ba213d`（tools）+ `067a230`（code）一并推上 master** → 本批 code/tools 在考官结论前已进 master（跨会话并发，不追回不回滚，靠 CI/考官/真机补验）。master CI run `43375557906`（head `5bbe4f4`）**success**，已发 Release `build-5bbe4f4…`（18 个 build tag）。本 docs 收尾条 ahead=1，推送后 `origin/master..HEAD`=0。
- **当前目标**：批次 5 进行中——tools/code 已随 `5bbe4f4` 上 master 并出 Release；① 本 docs 收尾条待推送；② **A-23（A-10 误报）下一条 tools 提交修复**；③ 待考官复核 + 真机 OTA（A* 跨图）。下一批候选：批次 A–E 真机补验；A-5（下轮 REQUEST）。
- **审查状态/豁免凭据**：2026-11-13 提前审（B 队 `docs/audit/REPORT-20261113.md`，窗口 `3decf36..ac26275`）＝**有条件通过**；五项整改状态——① **A-18 已落地**（本条 tools：`--push` 考官门禁）；② **A-2/A-3/A-10 部分修复**（A-10 模式已扩 + `WORKPLAN` 修，A-2/A-3 本收尾改引用）；③ **A-19 归组织规划**；④ **A-20/A-21 本条落地**（HANDOVER 模板审查状态行 + 新增复盘）；⑤ **A-22 已拍板**（B 队 `5bbe4f4` 已把 T4 判据改为「窗口内新增复发>0」）。T5 交接豁免见 `docs/audit/AUDIT_LOG.md`。**并发事实**：本批 code/tools 在考官结论前已随 B 队 push 上 master（A-18 门禁被并发绕过），已登记、不追回；**A-23** 记录 A-10 误拦 B 队合法提交（其被迫 `--no-verify`）→ 下一提交修。
- **本批已完成**：
  - tools `3ba213d`（已被 `5bbe4f4` 连带推送）：A-10 过期文案模式扩 `\d+ 项` / `\d+/\d+`（上下文防误报，文件级豁免 history/audit/generated/org-PLAN/roles-b/HANDOVER；`WORKPLAN` 写死数字同批修复）；A-17 写入范围检查（新增 `tools/write_scopes.json` 镜像 TEAM §一；`SCOPE_ROLE`/`--role`，默认警告、`--strict` 拒绝）；A-18 推送门禁（`BATCHES` 末行待复核 → 拒绝 push，除非 `--examiner-ok`/`EXAMINER_OK`）。
  - code `067a230`（已被 `5bbe4f4` 连带推送）：A* 跨图寻路移植（`MapLinks` / `CrossMapPathfinder` / `CrossMapWalker` + `assets/maps/map_links.json`；+12 测试，工匠本地 19/19 过）。**限制**：6 图缺 assets → 当前 5 图连通域可用；**无高度层**；`side` 语义待真机确认。
  - docs（本条）：`BATCHES` 只追加批次5 行；`HANDOVER` §三 交接模板增「审查状态/豁免凭据」必填行（A-20）；新建 `docs/history/RETROSPECTIVE-20261113.md`（docs 占比复盘，A-21）；`FILES`/`METRICS` 重生成；本文件更新。
- **A-2/A-3 口径（已改引用）**：测试数一律以 `tools/test_results.json` 为准（当前 python 29 / kotlin 101；批次5 新增 12 条待 CI 复跑后更新）；不再在 HANDOFF/HANDOVER 写死总数。
- **A-21 复盘（docs 占比）**：审查窗口 docs 占比 57%>50%、4 个纯 docs 批 100%；当日 44 提交中 docs 类 33（75%）。原因＝重建收尾集中 + 迁移类本身是 docs + 台账固定成本；对策＝后续批优先功能、docs ≤3/来源标注、A-17/A-18 机械门禁、HANDOFF 压缩；**复查点 2026-11-19**。详见 `docs/history/RETROSPECTIVE-20261113.md`。
- **剩余待办 / 转达**：
  - **A-23**（助理）：A-10 两处缺陷——扫描范围含未提交工作区（应只扫 staged）、`\d+ 项` 误报、引用旧值被当违规；**本条后紧接 1 条 tools 提交修复**（`chore(tools): 修 A-23 门禁误报`，不 push）。
  - **A-5**（统筹主持 + 独立督导）：下轮 `REQUEST` 补「T4 结果」必填段，窗口起点先 `git cat-file` 验真。
  - **A-22**（用户拍板）：T4「复发率>0」永久红 → 是否改「窗口内新增复发>0」。
  - **规范 docs 后续**：组织规划若再写（只写不提交），仍由助理**显式路径**提交，严禁 `git add -A`；来源须在提交信息标注。当前工作区另有组织规划未提交文件（`docs/TEAM.md`、`docs/org/PLAN-20261113-5.md`），**不要卷入本批**。
  - T4 仍红（复发 1 条，历史既有）——记录在案，不阻断。
- **规则（2026-11-13 用户拍板）**：docs 提交每批 **≤3 条**（同一会话 ≤1 条）；不同来源可同批提交、须标注来源；无写权限来源由助理代提交；占比 >50% 触发复盘，超 3 条只复盘、不阻断。
- **旧路径豁免清单**（grep 口径，B 队已确认）：(a) `docs/history/` 内正文；(b) `git show <旧提交>:<旧路径>` 历史引用；(c) `docs/org/PLAN-*` 等已定稿旧记录；(d) 历史台账正文不回改：`docs/audit/AUDIT_LOG.md` 3 处、`docs/audit/REPORT-20261112.md` 1 处。工作树**活体**文档/工具/脚本旧路径 = 0。

## 交接前置检查（HANDOVER §二，2026-11-13 13:5x 实测）

| # | 项 | 结果 |
|---|---|---|
| 1 | `git status` 干净 | ⏳ 本收尾条提交后干净；组织规划的 `docs/TEAM.md`/`docs/org/PLAN-20261113-5.md` 未提交（属其批次，助理未卷入） |
| 2 | 提交状态 | 本批 code/tools 已随 B 队 `5bbe4f4` 上 master（并发事实）；本 docs 收尾条 ahead=1，推送后 `origin/master..HEAD` = 0 |
| 3 | CI 绿 | ✅ master run `43375557906`（head `5bbe4f4`，含 native-emu）**success**；Release `build-5bbe4f4…` 已发布；待考官复核 + 真机 A* |
| 4 | `python3 run_tests.py` | ✅ 通过（数量以 `tools/test_results.json` 为准：python 29） |
| 5 | TODO/CHANGELOG 与代码同步 | ✅ 本批改动记入 `NATIVE_EMU_TODO`；`CHANGELOG` 在 `history/`，历史不回改 |
| 6 | `gen_files_index.py` 重生成 + `--check` | ✅ 重生成后 `--check` exit 0（见本提交） |
| 7 | 本文件更新（当前状态/阻塞/下一步/不要做什么） | ✅ 本提交 |
| 8 | 无未结束后台任务/子代理 | ✅ 无 |
| 9 | `precommit_check.sh --scope docs/ tools/`（`SCOPE_ROLE=assistant`） | ✅ 通过（A-17 对本批 docs 收尾文件仅告警） |
| 10 | `check_ui_state.py` | ✅ 本批通过（34 个 Kotlin 文件读写全配对） |
| 11 | 机械闸门已装 + A-10/A-17/A-18 | ✅ `.git/hooks/*` 在；A-18 生效后 push 须带考官回执 |

- **Kotlin 单测**：以 `tools/test_results.json` 为准（当前 kotlin 101，批次5 新增 12 条待 CI 复跑后更新）。
- **接手 5 分钟**（HANDOVER §五）：
  ```bash
  cd /root/workspace
  git status --short                                   # 期望空（队友未提交文件除外，不要 add -A）
  git log -3 --oneline                                 # 期望含批次5 tools/code/docs
  git rev-list --count origin/master..HEAD             # 统一推送后期望 0
  python3 run_tests.py                                 # 以 tools/test_results.json 为准
  python3 tools/gen_files_index.py --check             # 期望 0
  ```

## 构建 / 发布现状

- **最新构建 / 发布 = `build-5bbe4f4…`**（批次5；master CI run `43375557906` success，`publish release` success；含 A* 跨图 code `067a230`，**在考官结论前已发**——属并发事实，待考官/真机补验）。
- 上一版 `build-112817b27fcc599e49248a5f11380aab3c2a1e1f`（批次4；APK 11,575,075B / 11.04MB）保留为上一 Release。
- 该构建已 OTA 真机验证（版本 `0.2 (112817b) / 构建 12:34`；主屏拆分后 Tab / 地图 / 行走 / 战斗 T2 均回归通过）。
- 批次 5 的 code `067a230` **尚未构建**；待推验证分支跑 CI（非 master 不发 Release），绿后再合 master 发 `build-<sha>`；A* 跨图需真机验证（5 图连通域 / 无高度层 / side 语义）。
- 上一版 `build-ff93b78…`（批次3）保留；判构建覆盖看 `docs/generated/METRICS.md` 的 tag→提交映射；CI 仅在推送含 `native-emu/**` 时构建（按推送 tip 打 tag）。

## 关键决策（为什么）

- **方案箱**：`docs/org/` 中文统一叫「方案箱」；组织规划只写不提交，由助理随批提交（显式路径，防卷入）。
- **docs 提交限额**：每批 ≤3 条、同一会话 ≤1 条；不同来源可同批、须标注来源；>50% 触发复盘（A-21 复盘见 `history/RETROSPECTIVE-20261113.md`）。
- **A-10 扩展防误报**：只对新模式加「上下文白名单」，已知过期值（旧文件数 / 旧测试数 / 退役实例名）仍无条件拦截；文件级豁免 history/audit/generated/org-PLAN/roles-b/HANDOVER。
- **A-17 写入范围**：范围表镜像 `docs/TEAM.md` §一（唯一真源）；默认警告防误伤、`--strict` 才拒绝；`tools/write_scopes.json` 改表须与 TEAM 同批。
- **A-18 推送门禁**：`BATCHES` 末行待复核/待考官 → 拒绝 push；考官回执经 `--examiner-ok`/`EXAMINER_OK` 留痕，避免「先推再审」。
- **A* 跨图限制**：优先可验证的小步（5 图连通域），缺 assets / 无高度层 / side 语义留给真机与后续批，不假装完整。
- **B 队授权已确认**：M1/M6 一次性授权经 `9f35637` 确认有效；后续跨队批各 owner 各改各的。
- **B 队文件 A 队只读**（`docs/audit/**`），跨队改动经统筹主持转达独立督导。

## 下一步建议（给新统筹主持）

1. 先推本 docs 收尾条 + A-23 修复提交；考官复核（含并发事实登记）→ 真机 OTA 回归 A* 跨图（5 图连通域 / 无高度层 / side 语义）。
2. 组织规划的 `TEAM.md`/`PLAN-20261113-5.md`（A-19）写完后，由助理**显式路径**单独提交（另一条 docs，来源标注）。
3. 下一批候选：批次 A–E 真机补验；A-5 并入下轮 `REQUEST`。
4. 代码侧迁移（M3 `tests/` 收拢、M4 数据目录并入、M5 根 `.py` → `platform/`）等 F 批发布后再动；新批必写一条 `docs/BATCHES.md`。

## 不要做什么（最值钱）

- **不要 `git add -A`**：docs 收尾用显式路径；队友并行未提交文件（组织规划 TEAM/PLAN-5、native-emu）不得卷入。
- **不要在本会话继续干活**（已交接结束，新会话重建后再做）。
- **不要改 `docs/history/**` 旧文正文**（历史不回改；新复盘按日期单开）；生成物（`docs/generated/FILES.md`、`docs/generated/METRICS.md`）只重跑脚本。
- **不要手改 A-10 检查的豁免范围**；新出现的过期文案应改源头文档。
- **不要在未取考官结论时 push**：A-18 会拦；带 `--examiner-ok`/`EXAMINER_OK` 并在输出留痕。
- 不要重排已完成的**存档 3 槽 / 队伍详情 / 地图交互**（用户 11-12 决定：地图只修 bug、不加交互控件）。
- 不要用空提交触发构建；不要 amend / force push 已推送提交。
- 不要碰 keystore / token（签名固定，轮换会导致已装 App 无法覆盖升级；口令/密钥不进仓库、文档、聊天）。
- 不要把批次 A–E 旧包或 A* 跨图写成「已真机验证」（真机目前只覆盖 `build-112817b` 的批次4 回归）。
- 不要改 `docs/audit/**` 的规则正文（A 队只读；需统筹主持转达独立督导）。
- 不要伪造门禁/测试数字：以 `tools/test_results.json`、`git`、CI run 为准。
- 不要在 `HANDOFF` 堆积历史长文：上一版见 `git show 35b8fc7:docs/HANDOFF.md`。
