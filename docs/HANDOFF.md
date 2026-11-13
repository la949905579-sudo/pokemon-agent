# 交接文档（HANDOFF）

> 2026-11-13 12:5x · 批次 4 收尾（MainActivity 拆分 + A-16；已合 master 并发布 `build-112817b`，docs#2 待推送复核）
> 给新会话（新统筹主持）：先读本文件 + `docs/TEAM.md`（§二 重建步骤）+ `docs/HANDOVER.md` + `docs/NATIVE_EMU_TODO.md`。
> **本文件是交接唯一真源，聊天记录不算。** 历史长文已迁出：上一版交接（F2/A–E 真机记录、T5 豁免对账）见 `git show 35b8fc7:docs/HANDOFF.md`。

## 交接（2026-11-13 12:5x）

- **事实快照**：`origin/master` = `112817b`（批次4 已合入 master 并发布 `build-112817b…`）。本收尾 docs#2 推送后 `origin/master..HEAD` = 0（远端为真源）。批次 1（`95b861b`）/ 批次 2（`ab402fa`）/ 批次 3（`e22328f`…`ff93b78`）/ 批次 4（`8b99815`+`6ec7350`+`8435b37`+`112817b`）均已推送并双审。
- **当前目标**：批次 4 **已完成**（code/tools/docs + CI + 考官 + 真机均过，已合 master 发布 `build-112817b…`）。本收尾 docs#2 待考官轻量复核 + 推送。规范 docs 批（策略顾问 `advisor` 角色卡 + `REQUEST` + `TEAM` + `roles/README`，组织规划写）待组织规划写完后由助理**显式路径**单独提交。下一批候选：A* 跨图、批次 A–E 真机补验。
- **本批已完成**：
  - code `6ec7350`：MainActivity 拆分（≈710→311 行）+ 4 个新 ui 文件（`EmuView` / `StatusParser` / `WalkControl` / `LocalStatus`）+ 1 个新测试（`StatusParserTest` 6 例）；`check_ui_state` 过（34 文件读写全配对）。
  - tools `8b99815`：A-16 工具链中文职位名补全 / 成本归因修复——`token_report.mjs` roleFromLabel 补全 9 个中文职位名（旧名兼容、最左命中）、`metrics.py` / `test_results.json` 旧名同步、`token_baseline.json` 用脚本 `--write` 重生成。
  - docs#1 `8435b37`：`FILES` 重生成（**242 文件/0 未描述**，收录 4 个新 ui 文件 + 测试）；`METRICS` 重生成；`BATCHES` 批次4 行；本文件更新。
  - 合入与发布：master `401ebfa..112817b` 快进合并；master CI run `43366232788` **success**（`build`/`upload-artifact`/`publish release` 全 success），Release `build-112817b27fcc599e49248a5f11380aab3c2a1e1f`，APK `app-debug.apk` **11,575,075B / 11.04MB**。
  - **真机记录**（2026-11-13 12:49–12:53，`build-112817b` OTA）：版本/构建更新成功、游戏继续；Tab 队伍/背包/名字/图鉴/存档/设置均可切（存档 Tab 双击回地图页）、地图页渲染（「点格子预览路线」提示在）；按键行走正常；2 场野生战正常；战斗页双方等级/HP/招式正确；火花 16→0、抓 14→5 施放成功、回合推进；招式菜单打开时切页→不误按键/不卡键、返回后仍可施放。**未覆盖**：「施放瞬间切页」施放太快未掐到（单测覆盖）；地图点格子预览因截图/帧比对无法自动化（页面渲染已确认）。
  - docs#2（本收尾条）：`BATCHES`/`HANDOFF` 收尾 + `METRICS` 重生成（批次4 CI/Release 入表、三处 nit 校正）。
- **A-16 归因变化（供记录）**：未知职位 **实测快照 12:16：4 会话 / 59,666,019 token（7.6%）→ 0**；考官同口径复算 74,297,991（9.1%），差异＝助理会话 cacheRead 增长 / 快照时刻，**非归因错误**。执行主管（3 / 92,709,036）→ 助理、督导 → 独立督导、组织架构师 → 组织规划、B 队审查员 / 成本管理员归位；22 会话全部有归属（含 6 个主会话未标注）。
- **剩余待办 / 转达**：
  - **批次4 收尾 docs#2**：本收尾条待考官轻量复核 + 推送（不 push，等统筹主持拍板）。
  - **规范 docs 批**（另算 1 条）：组织规划正在写 `docs/org/REQUEST.md`、`docs/roles/org/advisor.md`、`docs/TEAM.md`、`docs/roles/README.md`（只写不提交）；助理只能**显式路径**提交，严禁 `git add -A`。
  - **A-5**（统筹主持 + 独立督导）：下轮 `REQUEST` 补「T4 结果」必填段，窗口起点先 `git cat-file` 验真（工具侧 `python3 tools/metrics.py --check --window <rev>` 已可用）。
  - T4 仍红（复发 1 条，历史既有）——记录在案，不阻断；随下次审查复核。
- **规则（2026-11-13 用户拍板）**：docs 提交每批 **≤3 条**（同一会话 ≤1 条）；不同来源可同批提交、须标注来源；无写权限来源由助理代提交；占比 >50% 触发复盘，超 3 条只复盘、不阻断。
- **旧路径豁免清单**（grep 口径，B 队已确认）：(a) `docs/history/` 内正文 1 处；(b) `git show <旧提交>:<旧路径>` 历史引用；(c) `docs/org/PLAN-*` 等已定稿旧记录；(d) 历史台账正文不回改：`docs/audit/AUDIT_LOG.md` 3 处、`docs/audit/REPORT-20261112.md` 1 处。工作树**活体**文档/工具/脚本旧路径 = 0。

## 交接前置检查（HANDOVER §二，2026-11-13 12:2x 实测）

| # | 项 | 结果 |
|---|---|---|
| 1 | `git status` 干净 | ⏳ 本 docs#2 提交后干净；组织规划的规范批文件仍在其工作区（未提交，助理不得卷入） |
| 2 | 提交状态 | 批次4 主体 4 条已在 master；本 docs#2 待推送，推送后 `origin/master..HEAD` = 0 |
| 3 | CI 绿 | ✅ 批次4 master CI run `43366232788` success；Release `build-112817b…` 已发布 |
| 4 | `python3 run_tests.py` | ✅ 29/29 通过（数字以 `tools/test_results.json` 为准） |
| 5 | TODO/CHANGELOG 与代码同步 | ✅ 本批改动记入 `NATIVE_EMU_TODO`；`CHANGELOG` 在 `history/`，历史不回改 |
| 6 | `gen_files_index.py` 重生成 + `--check` | ✅ **242 文件/0 未描述**，`--check` exit 0 |
| 7 | 本文件更新（当前状态/阻塞/下一步/不要做什么） | ✅ 本提交 |
| 8 | 无未结束后台任务/子代理 | ✅ 无 |
| 9 | `precommit_check.sh --scope docs/ tools/ native-emu/` | ✅ 通过（见本提交前门禁输出） |
| 10 | `check_ui_state.py` | ✅ 本批通过（34 个 Kotlin 文件，26 个 mutableStateOf 读写全配对） |
| 11 | 机械闸门已装 + A-10 过期文案检查 | ✅ `.git/hooks/pre-commit`、`pre-push` 均在 |

- **Kotlin 单测**：**101/101**（CI run `43365120600` 分支 attempt1 success、0 failure；master run `43366232788` build 步骤 success 再次确认）；`tools/test_results.json` 已记 101。
- **接手 5 分钟**（HANDOVER §五）：
  ```bash
  cd /root/workspace
  git status --short                                   # 期望空（队友未提交文件除外，不要 add -A）
  git log -3 --oneline                                 # 期望含批次4 tools/code/docs
  git rev-list --count origin/master..HEAD             # 统一推送后期望 0
  python3 run_tests.py                                 # 期望 29/29
  python3 tools/gen_files_index.py --check             # 期望 0
  ```

## 构建 / 发布现状

- **最新构建 / 发布 = `build-112817b27fcc599e49248a5f11380aab3c2a1e1f`**（批次4；master CI run `43366232788`，success，`publish release` success；APK `app-debug.apk` **11,575,075B / 11.04MB**）。
- 该构建已 OTA 真机验证（版本 `0.2 (112817b) / 构建 12:34`；主屏拆分后 Tab / 地图 / 行走 / 战斗 T2 均回归通过，见上「真机记录」）。
- 上一版 `build-ff93b78…`（批次3）保留为上一 Release；判构建覆盖看 METRICS 的 tag→提交映射。
- 判构建覆盖看 `docs/generated/METRICS.md` 的 tag→提交映射；CI 仅在推送含 `native-emu/**` 时构建（按推送 tip 打 tag）。

## 关键决策（为什么）

- **方案箱**：`docs/org/` 中文统一叫「方案箱」；组织规划只写不提交，由助理随批提交（显式路径，防卷入）。
- **docs 提交限额**：每批 ≤3 条、同一会话 ≤1 条；不同来源可同批、须标注来源。
- **A-16 修复**：职位名以新中文名为准、旧名兼容；生成物（`token_baseline.json`）只经脚本重生成。
- **A-10 / A-15 机械化**：过期文档文案进 precommit 机械检查；巡检 `--all` 对无数据会话必须明示。豁免见上旧路径清单。
- **MainActivity 拆分**：先出拆分方案再动代码；拆出 `EmuView` / `StatusParser` / `WalkControl` / `LocalStatus` 四个职责单文件，`StatusParser` 保持纯函数可离线单测。
- **B 队授权已确认**：M1/M6 一次性授权经 `9f35637` 确认有效；后续跨队批各 owner 各改各的。
- **B 队文件 A 队只读**（`docs/audit/**`），跨队改动经统筹主持转达独立督导。

## 下一步建议（给新统筹主持）

1. 先推本收尾 docs#2 → 考官轻量复核；批次4 主体（code/tools）已在 master 并发布 `build-112817b…`，真机回归已过。
2. 规范 docs 批：等组织规划写完（`REQUEST` / `advisor` 卡 / `TEAM` / `roles/README`）后由助理**显式路径**单独提交 1 条。
3. 下一批候选：A* 跨图、批次 A–E 真机补验；A-5 并入下轮 `REQUEST`。
4. 代码侧迁移（M3 `tests/` 收拢、M4 数据目录并入、M5 根 `.py` → `platform/`）等 F 批发布后再动；新批必写一条 `docs/BATCHES.md`。

## 不要做什么（最值钱）

- **不要 `git add -A`**：批次4 起 docs 收尾用显式路径；队友并行未提交文件（规范 docs 批 / native-emu）不得卷入。
- **不要在本会话继续干活**（已交接结束，新会话重建后再做）。
- **不要改 `docs/history/**` 正文**（历史不回改）；生成物（`docs/generated/FILES.md`、`docs/generated/METRICS.md`）只重跑脚本，不手改。
- **不要手改 A-10 检查的豁免范围**（`docs/history/**`、`docs/org/PLAN-*`、B 队历史台账、git 历史）；新出现的过期文案应改源头文档。
- 不要重排已完成的**存档 3 槽 / 队伍详情 / 地图交互**（用户 11-12 决定：地图只修 bug、不加交互控件）。
- 不要用空提交触发构建；不要 amend / force push 已推送提交。
- 不要碰 keystore / token（签名固定，轮换会导致已装 App 无法覆盖升级；口令/密钥不进仓库、文档、聊天）。
- 不要把批次 A–E 旧包写成「已真机验证」（真机记录只覆盖 `build-ff93b78`）。
- 不要改 `docs/audit/**` 的规则正文（A 队只读；需统筹主持转达独立督导）。
- 不要伪造门禁/测试数字：以 `tools/test_results.json`、`git`、CI run 为准。
- 不要在 `HANDOFF` 堆积历史长文：上一版见 `git show 35b8fc7:docs/HANDOFF.md`。
