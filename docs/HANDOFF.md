# 交接文档（HANDOFF）

> 2026-11-13 06:4x · 批次 3（F2 遗留收尾）进行中——非代码部分（docs/tools）已提交，代码部分由工匠执行
> 给新会话（新统筹主持）：先读本文件 + `docs/TEAM.md`（§二 重建步骤）+ `docs/HANDOVER.md` + `docs/NATIVE_EMU_TODO.md`。
> **本文件是交接唯一真源，聊天记录不算。** 历史长文已迁出：上一版交接（F2/A–E 真机记录、T5 豁免对账）见 `git show 35b8fc7:docs/HANDOFF.md`。

## 交接（2026-11-13 06:4x）

- **事实快照**：`origin/master` = `c599b72`（远端真源）；本批 docs + tools 2 条提交待**统一推送**，推送后 `origin/master..HEAD` = 0。批次 1（`95b861b`）、批次 2（`ab402fa`）均已推送，考官均「可发布（0 阻断）」。
- **当前目标**：批次 3（F2 遗留收尾）双线——非代码部分（本助理）已完成；代码部分（工匠：`BattleMoveAction.kt` 结构债、单测缺口、轮询 cancelled、注释）进行中。两线完成 → 合并双审 + 统一推送。
- **已完成**（带提交号，远端 `origin/master` 即真源）：
  - 本批 docs `docs(批次3): 方案箱落地 + 台账/交接修正 + 授权闭环`：组织规划 5 文件**原样**提交（PLAN-4 §九 / `org/README`「方案箱」/ TEAM 三·八 / docs/README §二 / roles/org/architect）；`BATCHES` 只追加（批次3 行 + 批次1/2「已推送 + 考官可发布」追记）；本文件校正；A-10 顺带修 `TOOLS.md` 过期测试数（28→29）。
  - 本批 tools `chore(tools): A-10 文档过期检查 + A-15 巡检兼容`：A-10 precommit 新增「过期文档文案」机械检查（旧文件数 / 旧测试数 / 退役实例名等过期文案，命中即红）+ `metrics.py --check` 窗口 `git cat-file` 验真（起点不可解析即红、报实际提交数）；A-15 `session_health.mjs --all` 兼容无会话数据目录，输出「无数据」而非默认「未超线」。
  - `c599b72` B 队 ACTIONS 状态回填（A-1~A-4/A-9/A-11~A-14 已落地，余 A-5/A-10/A-15）+ M6 实况与越界观察。
  - `ab402fa` 批次 2 M6（审查件归并 `docs/audit/`；已推送；考官可发布 0 阻断）。
  - `95b861b` 批次 1 M1（docs 分区迁移 history/ + generated/；已推送；考官可发布 0 阻断）。
  - `6841960` B 队三卡迁入 `docs/roles/b/` + M6 归并同意；`598cee1` HANDOFF 交接 + BATCHES 回填；`4378149` 项目重建 P0。
- **授权闭环**（M1/M6 §五.4）：B 队 `c599b72` 回执——内容验收无误、**不追改**；流程上「M6 由 A 队执行、连带改 B 队文件」记**元审查一条**；后续跨队批**各 owner 各改各的**。M1/M6 授权记录据此闭环，最终确认并入下方转达清单第 1 项。
- **转达清单（PLAN-4 §9.2 待督导，由统筹主持转达，4 项）**：
  1. 确认 M1/M6 一次性授权（范围＝B 队文件仅**活体**路径引用同步；未改职责/规则正文；历史台账正文不回改）。
  2. A-7 交接记录：旧统筹主持会话 142 轮已完成交接；按 T5 在 `AUDIT_LOG` 记录审查状态，或按用户豁免留痕（冷却至 2026-11-19）。
  3. A-5：下轮 `REQUEST` 补「T4 结果」必填段，窗口起点先 `git cat-file` 验真。
  4. A-15 巡检口径：无数据的会话目录必须注明「无数据」，不得默认「未超线」（工具已在批次 3 落地）。
- **未完成 / 卡住**：
  - 批次 3 代码部分（工匠）：`BattleMoveAction.kt` 结构债、单测缺口、轮询未查 cancelled、注释；完成后与 docs/tools 两提交合并双审、统一推送。细节见 `docs/NATIVE_EMU_TODO.md`「批次 F2 遗留」。
  - 旧 B 队整改 A-5 仍待办（下轮 `REQUEST`）；A-10/A-15 已在本批落地。
  - 批次 A–E 旧包无独立真机证据（历史日志早于批次 C、OTA 下载失败）；只有 `build-9c2fc63` 上的 A–E 功能点抽查（旧 HANDOFF §二·七，见 `git show 35b8fc7:docs/HANDOFF.md`）。
- **旧路径豁免清单**（grep 口径，均待督导确认）：(a) `docs/history/` 内正文 1 处（`INCIDENTS.md:66` 自指）；(b) `git show <旧提交>:<旧路径>` 历史引用；(c) `docs/org/PLAN-*` 等已定稿旧记录（AUDIT/AUDIT_LOG 18 + M1 路径 16）；(d) **历史台账正文不回改**：`docs/audit/AUDIT_LOG.md` 3 处、`docs/audit/REPORT-20261112.md` 1 处。工作树**活体**文档/工具/脚本旧路径 = 0。

## 交接前置检查（HANDOVER §二，2026-11-13 06:4x 实测）

| # | 项 | 结果 |
|---|---|---|
| 1 | `git status` 干净 | ✅ 本批提交后为空 |
| 2 | 提交状态 | 本批 2 条待**统一推送**；推送后 `origin/master..HEAD` = 0（远端为真源） |
| 3 | CI 绿 | ✅ 本批 docs + tools，不触发 CI 构建（无 `native-emu/**`） |
| 4 | `python3 run_tests.py` | ✅ 29/29 通过（数字以 `tools/test_results.json` 为准） |
| 5 | TODO/CHANGELOG 与代码同步 | ✅ F2 遗留已入 `NATIVE_EMU_TODO`；`CHANGELOG` 已入 `history/`，历史不回改 |
| 6 | `gen_files_index.py` 重生成 + `--check` | ✅ 233 文件/0 未描述，`--check` exit 0 |
| 7 | 本文件更新（当前状态/阻塞/下一步/不要做什么） | ✅ 本提交 |
| 8 | 无未结束后台任务/子代理 | ✅ 无 |
| 9 | `precommit_check.sh --scope` | ✅ 批次A `--scope docs/`、批次B `--scope docs/ tools/` 均通过 |
| 10 | `check_ui_state.py`（有 Kotlin UI 改动才跑） | — 本批非代码部分不适用；代码部分工匠按需 |
| 11 | 机械闸门已装 + A-10 过期文案检查已入闸 | ✅ `.git/hooks/pre-commit`、`pre-push` 均在；A-10 检查已随批次B 提交 |

- **Kotlin 单测**：最近实跑 82/82（`9c2fc63`，MoveCasterTest 11/11）；本批代码改动后由工匠更新 `tools/test_results.json`（数字以它为准）。
- **接手 5 分钟**（HANDOVER §五）：
  ```bash
  cd /root/workspace
  git status --short                                   # 期望空
  git log -3 --oneline                                 # 期望含本批 docs + tools 提交
  git rev-list --count origin/master..HEAD             # 期望 2（统一推送后为 0）
  python3 run_tests.py                                 # 期望 29/29
  python3 tools/gen_files_index.py --check             # 期望 0
  ```

## 构建 / 发布现状

- **最新构建 = `build-9c2fc63`**（CI run `43266619857`，success，唯一 1 次构建；Release 自动发布，APK 11,575,075B）。
- 该构建已装到手机并完成 F2 真机验证（版本 `0.2 (9c2fc63) / 构建 11-13 01:11`）；APK 也在 `/sdcard/Download/DSH-Go/native-emu-9c2fc63.apk`。
- 判构建覆盖看 `docs/generated/METRICS.md` 的 tag→提交映射；CI 仅在推送含 `native-emu/**` 时构建（按推送 tip 打 tag）。

## 关键决策（为什么）

- **方案箱**：`docs/org/` 中文统一叫「方案箱」；组织规划**只写不提交**，由助理随批提交（路径不变，命名规则不变）。
- **A-10 / A-15 机械化**：「过期文档文案」进 precommit 机械检查（老数字/退役实例名不再靠人记）；巡检 `--all` 对无数据会话必须明示，不默认健康。豁免：`docs/history/**`、`docs/org/PLAN-*`、B 队历史台账、git 历史。
- **授权闭环**：B 队 `c599b72` 回执——不追改、流程记元审查一条、后续跨队批各 owner 各改各的；M1/M6 授权据此闭环。
- **M6 审查件归并**：审查件是 B 队文件，归并后 B 队文档单一目录（`docs/audit/`）；依据 `6841960` 督导同意、单开批、同批改完引用。
- **M1 docs 分区**：`history/` 只放历史记录（只移动、不改正文）、`generated/` 只放生成物（只经脚本重跑），活规范留顶层。
- **规则文档重写 + 角色卡按队拆**：落实「单会话单身份」；助理每批新开，保护统筹主持寿命；退役实例名永久禁用（历史文档不回改）。
- **F2 最小范围**：仅招式菜单已展开（`TURN_FLAG==2` 且 `MAIN_CURSOR==0`）时可点；不做主菜单自动打开；fail-closed + 失败即停，避免误操作。
- **docs 提交每批 ≤1 个**、`BATCHES` 只追加：控制文档反客为主。
- **B 队文件 A 队只读**（`docs/audit/**`，含 `AUDIT.md`/`AUDIT_LOG.md`），跨队改动经统筹主持转达独立督导。

## 下一步建议（给新统筹主持）

1. 等工匠代码部分完成 → **合并双审**（考官 doc 轻量 + 代码复核）→ **统一推送**批次 3（docs + tools + 代码提交），然后核对 `origin/master..HEAD`=0。
2. A-5 并入下轮 `REQUEST`（督导执行）；转达清单 4 项由统筹主持转达。
3. 代码侧迁移（M3 `tests/` 收拢、M4 数据目录并入、M5 根 `.py` → `platform/`）等 F 批发布后再动。
4. 新批必写一条 `docs/BATCHES.md` 记录（只追加）。

## 不要做什么（最值钱）

- **不要在本会话继续干活**（已交接结束，新会话重建后再做）。
- **不要改 `docs/history/**` 正文**（历史不回改）；生成物（`docs/generated/FILES.md`、`docs/generated/METRICS.md`）只重跑脚本，不手改。
- **不要手改 A-10 检查的豁免范围**（`docs/history/**`、`docs/org/PLAN-*`、B 队历史台账、git 历史）；新出现的过期文案应改源头文档。
- 不要重排已完成的**存档 3 槽 / 队伍详情 / 地图交互**（用户 11-12 决定：地图只修 bug、不加交互控件）。
- 不要用空提交触发构建；不要 amend / force push 已推送提交。
- 不要碰 keystore / token（签名固定，轮换会导致已装 App 无法覆盖升级；口令/密钥不进仓库、文档、聊天）。
- 不要把批次 A–E 旧包写成「已真机验证」（没有独立证据；只有当前包 `build-9c2fc63` 的功能点抽查）。
- 不要改 `docs/audit/**`（含 `AUDIT.md`/`AUDIT_LOG.md`）的规则正文（A 队只读；需统筹主持转达独立督导）。
- 不要伪造门禁/测试数字：以 `tools/test_results.json`、`git`、CI run 为准。
- 不要在 `HANDOFF` 堆积历史长文：上一版见 `git show 35b8fc7:docs/HANDOFF.md`。
