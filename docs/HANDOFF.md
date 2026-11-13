# 交接文档（HANDOFF）

> 2026-11-13 12:0x · 批次 3 收尾交接（F2 遗留收尾完成，Release `build-ff93b78…`）
> 给新会话（新统筹主持）：先读本文件 + `docs/TEAM.md`（§二 重建步骤）+ `docs/HANDOVER.md` + `docs/NATIVE_EMU_TODO.md`。
> **本文件是交接唯一真源，聊天记录不算。** 历史长文已迁出：上一版交接（F2/A–E 真机记录、T5 豁免对账）见 `git show 35b8fc7:docs/HANDOFF.md`。

## 交接（2026-11-13 12:0x）

- **事实快照**：`origin/master` 基线 = `9f35637`（B 队回执；此前 `ff93b78`＝`9f35637` 的父提交，为批次3 发布提交）。本收尾 docs 提交推送后：HEAD = 本收尾提交、`origin/master..HEAD` = 0（远端为真源）。批次 1（`95b861b`）/ 批次 2（`ab402fa`）/ 批次 3（`e22328f`→`ff93b78`）均已推送，考官均「可发布」。
- **当前目标**：批次 3（F2 遗留收尾）**已完成**（代码 + 文档 + 工具 + CI + 真机）。下一批建议：`MainActivity.kt` 拆分（710 行 > 500，先出方案）；代码侧迁移 M3/M4/M5 等 F 批发布后再动。
- **本批已完成**：
  - docs：`e22328f`（方案箱落地 + 台账/交接修正 + 授权闭环）＋本收尾条（来源＝组织规划 + 助理；本批 docs=2 ≤3）。
  - 代码：`97bb03c` F2 遗留结构债 + 取消轮询 + 单测 +13（Kotlin 95 条）。
  - tools：`8b38330` A-10 文档过期检查 + A-15 巡检兼容；`ff93b78` CI 证据（Kotlin 82→95，证据＝CI run `43321435153`）。
  - CI：验证分支 run `43321435153`（attempt1 **success**，build 步骤含单测 + assembleDebug，release skipped）；master run `43322690329`（**success**，**Release `build-ff93b780a517eebf4ea58b1d3210e110a7d4267d` 已发布**，APK `app-debug.apk` 11,575,075B＝11.04MB）。
  - **真机记录**（2026-11-13 06:55–06:58，`build-ff93b78` OTA）：加载 ROM / 继续冒险正常；2 场野生战；战斗页血条正确；「抓 / 叫声 / 火花」3 招点击施放成功、回合推进；招式菜单打开时切页未误按键 / 未卡键；第 4 格空（Lv7 仅 3 招）；「施放瞬间切页」未掐点触发，仍只有单测覆盖。
  - Kotlin 单测：**95/95**（CI `43321435153` + 本地独立复算双证；`tools/test_results.json` 已记 CI 证据）；Python 29/29。
  - B 队回执 `9f35637`：M1/M6 一次性授权**确认有效**（`AUDIT_LOG` 授权确认节）；A-7 交接登记；A-10/A-15 核销「已落地」；新增 A-16；元审查一条（不追改）。
- **剩余待办 / 转达**：
  - **A-5**（统筹主持 + 独立督导）：下轮 `REQUEST` 补「T4 结果」必填段，窗口起点先 `git cat-file` 验真（工具侧 `python3 tools/metrics.py --check --window <rev>` 已可用）。
  - **A-16**（助理）：工具链旧名 / 成本归因——`tools/metrics.py` 仍写「执行主管」、`tools/test_results.json` note 同；`tools/token_report.mjs` 的 roleFromLabel 不认「助理」「审查员 / 成本管理员」→ 4 个会话约 5055 万 token 落「未知职位」（约总量 9.5%）；下批随批修。
  - T4 仍红（复发 1 条，历史既有）——记录在案，不阻断；随下次审查复核。
- **规则（2026-11-13 用户拍板）**：docs 提交每批 **≤3 条**（同一会话 ≤1 条）；不同来源可同批提交、须标注来源；无写权限来源由助理代提交；占比 >50% 触发复盘，超 3 条只复盘、不阻断。
- **旧路径豁免清单**（grep 口径，B 队已确认）：(a) `docs/history/` 内正文 1 处（`INCIDENTS.md:66` 自指）；(b) `git show <旧提交>:<旧路径>` 历史引用；(c) `docs/org/PLAN-*` 等已定稿旧记录；(d) 历史台账正文不回改：`docs/audit/AUDIT_LOG.md` 3 处、`docs/audit/REPORT-20261112.md` 1 处。工作树**活体**文档/工具/脚本旧路径 = 0。

## 交接前置检查（HANDOVER §二，2026-11-13 12:0x 实测）

| # | 项 | 结果 |
|---|---|---|
| 1 | `git status` 干净 | ✅ 本收尾提交后为空 |
| 2 | 提交状态 | 本收尾 docs 提交推送后 `origin/master..HEAD` = 0（远端为真源） |
| 3 | CI 绿 | ✅ master run `43322690329` success；Release `build-ff93b78…` 已发布 |
| 4 | `python3 run_tests.py` | ✅ 29/29 通过（数字以 `tools/test_results.json` 为准） |
| 5 | TODO/CHANGELOG 与代码同步 | ✅ F2 遗留已收尾入 `NATIVE_EMU_TODO`；`CHANGELOG` 在 `history/`，历史不回改 |
| 6 | `gen_files_index.py` 重生成 + `--check` | ✅ 237 文件/0 未描述，`--check` exit 0 |
| 7 | 本文件更新（当前状态/阻塞/下一步/不要做什么） | ✅ 本提交 |
| 8 | 无未结束后台任务/子代理 | ✅ 无 |
| 9 | `precommit_check.sh --scope docs/ tools/` | ✅ 通过（见本提交前门禁输出） |
| 10 | `check_ui_state.py` | ✅ 考官批次3 已跑通过 |
| 11 | 机械闸门已装 + A-10 过期文案检查已入闸 | ✅ `.git/hooks/pre-commit`、`pre-push` 均在；A-10 已随批次3 落地 |

- **Kotlin 单测**：**95/95**（CI run `43321435153` attempt1 success，0 failure；本地独立复算一致）；此后无 Kotlin 改动则沿用，见 `tools/test_results.json`。
- **接手 5 分钟**（HANDOVER §五）：
  ```bash
  cd /root/workspace
  git status --short                                   # 期望空
  git log -1 --pretty='%h %s'                          # 期望本收尾 docs 提交
  git rev-list --count origin/master..HEAD             # 期望 0（推送后）
  python3 run_tests.py                                 # 期望 29/29
  python3 tools/gen_files_index.py --check             # 期望 0
  ```

## 构建 / 发布现状

- **最新构建 / 发布 = `build-ff93b780a517eebf4ea58b1d3210e110a7d4267d`**（master CI run `43322690329`，success，`publish release` success；APK `app-debug.apk` **11,575,075B / 11.04MB**）。
- 该构建为批次 3 F2 收尾版（Kotlin 95 单测通过）；已 OTA 真机验证（见上「真机记录」）；APK 在 GitHub Release 资产页。
- 判构建覆盖看 `docs/generated/METRICS.md` 的 tag→提交映射；CI 仅在推送含 `native-emu/**` 时构建（按推送 tip 打 tag）。

## 关键决策（为什么）

- **方案箱**：`docs/org/` 中文统一叫「方案箱」；组织规划只写不提交，由助理随批提交。
- **docs 提交限额**：每批 ≤3 条、同一会话 ≤1 条（防同一会话连续刷 docs）；不同来源可同批、须标注来源。
- **A-10 / A-15 机械化**：过期文档文案进 precommit 机械检查；巡检 `--all` 对无数据会话必须明示。豁免见上旧路径清单。
- **B 队授权已确认**：M1/M6 一次性授权（B 队文件仅活体路径引用同步）经 `9f35637` 确认有效；元审查一条不追改；后续跨队批各 owner 各改各的。
- **M6 审查件归并**：审查件归 `docs/audit/`，B 队文档单一目录；**M1 docs 分区**：`history/` 历史、`generated/` 生成物、活规范留顶层。
- **F2 最小范围**：仅招式菜单已展开（`TURN_FLAG==2` 且 `MAIN_CURSOR==0`）时可点；fail-closed + 失败即停；「施放瞬间切页」仍只有单测覆盖。
- **B 队文件 A 队只读**（`docs/audit/**`），跨队改动经统筹主持转达独立督导。

## 下一步建议（给新统筹主持）

1. 下一批：**`MainActivity.kt` 拆分**（710 行 > 500，先出拆分方案再动代码）；A-16（工具链旧名 / 成本归因）随批修。
2. A-5 并入下轮 `REQUEST`（督导执行）；T4 红随下次审查复核。
3. 代码侧迁移（M3 `tests/` 收拢、M4 数据目录并入、M5 根 `.py` → `platform/`）等 F 批发布后再动。
4. 新批必写一条 `docs/BATCHES.md` 记录（只追加）。

## 不要做什么（最值钱）

- **不要在本会话继续干活**（已交接结束，新会话重建后再做）。
- **不要改 `docs/history/**` 正文**（历史不回改）；生成物（`docs/generated/FILES.md`、`docs/generated/METRICS.md`）只重跑脚本，不手改。
- **不要手改 A-10 检查的豁免范围**（`docs/history/**`、`docs/org/PLAN-*`、B 队历史台账、git 历史）；新出现的过期文案应改源头文档。
- 不要重排已完成的**存档 3 槽 / 队伍详情 / 地图交互**（用户 11-12 决定：地图只修 bug、不加交互控件）。
- 不要用空提交触发构建；不要 amend / force push 已推送提交。
- 不要碰 keystore / token（签名固定，轮换会导致已装 App 无法覆盖升级；口令/密钥不进仓库、文档、聊天）。
- 不要把批次 A–E 旧包写成「已真机验证」（没有独立证据；真机记录只覆盖 `build-ff93b78`）。
- 不要改 `docs/audit/**` 的规则正文（A 队只读；需统筹主持转达独立督导）。
- 不要伪造门禁/测试数字：以 `tools/test_results.json`、`git`、CI run 为准。
- 不要在 `HANDOFF` 堆积历史长文：上一版见 `git show 35b8fc7:docs/HANDOFF.md`。
