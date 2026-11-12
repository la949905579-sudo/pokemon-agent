# 交接文档（HANDOFF）

> 2026-11-13 05:5x · 批次 1（docs 分区迁移 M1）提交后交接
> 给新会话（新统筹主持）：先读本文件 + `docs/TEAM.md`（§二 重建步骤）+ `docs/HANDOVER.md` + `docs/NATIVE_EMU_TODO.md`。
> **本文件是交接唯一真源，聊天记录不算。** 历史长文已迁出：上一版交接（F2/A–E 真机记录、T5 豁免对账）见 `git show 35b8fc7:docs/HANDOFF.md`。

## 交接（2026-11-13 05:5x）

- **当前目标**：批次 1（docs 分区迁移 M1）已提交、**未推送**（等统筹主持拍板 + 考官轻量复核）。下一批候选：**M6** 审查件归并 `docs/audit/`（已获督导同意，单开一批）。
- **已完成**（带提交号，远端 `origin/master` 即真源）：
  - 本批 `docs(M1): docs 分区迁移（history/ + generated/）`（HEAD，`git log --oneline -1` 可查）：7 文件 `git mv`（`FILES`/`METRICS` → `generated/`；`CHANGELOG`/`INCIDENTS`/`RETROSPECTIVE`/`NOTES`/`ARCHITECTURE` → `history/`，正文不改）；`tools/gen_files_index.py`（输出路径 + OVERRIDES）、`tools/metrics.py`（OUT + 事故路径文案）、`tools/precommit_check.sh` 同步；活文档路径同步（`README` §二/§七、`STRUCTURE`、`TOOLS`、`WORKPLAN`、`HANDOVER`、`TEAM`、`PROJECT_PLAN`、`archive/README`、`roles/a/assistant`、`roles/b/*`）；根 `README.md`（2 行）、`AGENTS.md`（1 行）旧路径同步；索引重生成（233 文件/0 未描述）；`METRICS` 用脚本重生成（无旧路径回流）。
  - `6841960` B 队三卡迁入 `docs/roles/b/` + 引用更新 + 助理改名 + 六节报告/每日巡检规则；**M6 归并获督导同意（单开批）**。
  - `598cee1` HANDOFF 交接（2026-11-13 会话结束）+ BATCHES 台账回填。
  - `4378149` 项目重建 P0（规则文档重写 + 角色卡按队拆 + 批次台账 + `FILES` 重生成）。
- **未完成 / 卡住**：
  - **M6** 审查件归并 `docs/audit/`：已获督导同意，待单开一批（搬 `AUDIT.md`/`AUDIT_LOG.md` + B 队写范围，需督导配合）。
  - **待督导跟进**：B 队只读文件内的旧路径（`docs/AUDIT.md`、`docs/AUDIT_LOG.md`、`docs/audit/**`）本批按「A 队只读」未改，属口径豁免；`docs/roles/b/*` 的路径已随本批同步，改动经 `git show` 核对为**纯路径**（3 文件 4 行，无正文/职责改动），**§五.4 一次性授权待督导确认**。
  - F2 遗留：拒绝路径（未开菜单/回读不一致）与切页·收面板中断**仅单测覆盖、未真机触发**；`ui/BattleMoveAction.kt` 直接读内存的结构债；`MainActivity.kt` 710 行 > 500 上限；A 后轮询未查 cancelled；P3 名表 `id=232` 缺口（界面显示 `#232`）。均记于 `docs/NATIVE_EMU_TODO.md`「批次 F2 遗留」。
  - 批次 A–E 旧包无独立真机证据（历史日志早于批次 C、OTA 下载失败）；只有 `build-9c2fc63` 上的 A–E 功能点抽查（旧 HANDOFF §二·七，见 `git show 35b8fc7:docs/HANDOFF.md`）。
  - 旧 B 队整改 A-10～A-13 是否仍适用，需按新流程复核（新规则：整改并入下一功能批，只有 P0 单开）。
- **本批旧路径豁免清单**（grep 口径）：(a) `docs/history/` 内正文；(b) `git show <旧提交>:<旧路径>` 历史引用；(c) B 队只读文件（见上，待督导跟进）；(d) `docs/org/PLAN-*` 等已定稿旧记录。工作树活文档/活工具/脚本中的旧路径 = 0。

## 交接前置检查（HANDOVER §二，2026-11-13 05:5x 实测）

| # | 项 | 结果 |
|---|---|---|
| 1 | `git status` 干净 | ✅ 提交后为空 |
| 2 | 提交状态 | ⏳ 本批按要求**不 push**：`origin/master..HEAD` = 1，等统筹主持拍板 |
| 3 | CI 绿 | ✅ 本批 docs-only，pre-push 判定不触发构建（无 `native-emu/**`） |
| 4 | `python3 run_tests.py` | ✅ 29/29 通过（数字以 `tools/test_results.json` 为准） |
| 5 | TODO/CHANGELOG 与代码同步 | ✅ 本批无代码变更；`CHANGELOG` 已入 `history/`，历史不回改 |
| 6 | `gen_files_index.py` 重生成 + `--check` | ✅ 233 文件/0 未描述，`--check` exit 0 |
| 7 | 本文件更新（当前状态/阻塞/下一步/不要做什么） | ✅ 本提交 |
| 8 | 无未结束后台任务/子代理 | ✅ 无 |
| 9 | `precommit_check.sh --scope docs/ tools/ README.md AGENTS.md` | ✅ 通过（见本提交前门禁输出） |
| 10 | `check_ui_state.py`（有 Kotlin UI 改动才跑） | — 本批无 Kotlin 改动，不适用 |
| 11 | 机械闸门已装 | ✅ `.git/hooks/pre-commit`、`pre-push` 均在 |

- **Kotlin 单测**：最近实跑 82/82（`9c2fc63`，MoveCasterTest 11/11）；此后无 Kotlin 改动，见 `tools/test_results.json`。
- **接手 5 分钟**（HANDOVER §五）：
  ```bash
  cd /root/workspace
  git status --short                                   # 期望空
  git log -1 --pretty='%h %s'                          # 期望本批 M1 提交
  git rev-list --count origin/master..HEAD             # 期望 1（未推送，等拍板）
  python3 run_tests.py                                 # 期望 29/29
  python3 tools/gen_files_index.py --check             # 期望 0
  ```

## 构建 / 发布现状

- **最新构建 = `build-9c2fc63`**（CI run `43266619857`，success，唯一 1 次构建；Release 自动发布，APK 11,575,075B）。
- 该构建已装到手机并完成 F2 真机验证（版本 `0.2 (9c2fc63) / 构建 11-13 01:11`）；APK 也在 `/sdcard/Download/DSH-Go/native-emu-9c2fc63.apk`。
- 判构建覆盖看 `docs/generated/METRICS.md` 的 tag→提交映射；CI 仅在推送含 `native-emu/**` 时构建（按推送 tip 打 tag）。

## 关键决策（为什么）

- **M1 docs 分区**：`history/` 只放历史记录（只移动、不改正文）、`generated/` 只放生成物（只经脚本重跑），活规范留顶层；迁移同批完成，不留半搬半留。
- **规则文档重写 + 角色卡按队拆**：落实「单会话单身份」；助理每批新开，保护统筹主持寿命；旧名 `builder`/`verifier`/`steward` 永久禁用。
- **F2 最小范围**：仅招式菜单已展开（`TURN_FLAG==2` 且 `MAIN_CURSOR==0`）时可点；不做主菜单自动打开；fail-closed + 失败即停，避免误操作。
- **docs 提交每批 ≤1 个**、`BATCHES` 只追加：控制文档反客为主。
- **B 队文件 A 队只读**（`AUDIT.md`/`AUDIT_LOG.md`/`docs/audit/**`），跨队改动经统筹主持转达独立督导。
- **§五.4 一次性授权留痕**（2026-11-13）：授权人＝统筹主持；范围＝`docs/roles/b/*.md` 仅旧路径引用同步（未改正文/职责，3 文件 4 行）+ 根 `README.md`/`AGENTS.md` 路径引用（仅路径）。`roles/b` 改动经 `git show HEAD -- docs/roles/b/` 核对为纯路径；待督导确认，转达由统筹主持后续执行。

## 下一步建议（给新统筹主持）

1. 先叫考官做**轻量复核**（纯文档批 ≤5 行：引用 / 一致性 / 索引），再过推前门禁；**推送由统筹主持拍板**（本批未 push）。
2. 下一批候选：**M6** 审查件归并 `docs/audit/`（督导同意已拿到，单开批）；或 F2 遗留收尾。
3. 新批必写一条 `docs/BATCHES.md` 记录（只追加）。

## 不要做什么（最值钱）

- **不要在本会话继续干活**（已交接结束，新会话重建后再做）。
- **不要改 `docs/history/**` 正文**（历史不回改）；生成物（`docs/generated/FILES.md`、`docs/generated/METRICS.md`）只重跑脚本，不手改。
- 不要重排已完成的**存档 3 槽 / 队伍详情 / 地图交互**（用户 11-12 决定：地图只修 bug、不加交互控件）。
- 不要用空提交触发构建；不要 amend / force push 已推送提交。
- 不要碰 keystore / token（签名固定，轮换会导致已装 App 无法覆盖升级；口令/密钥不进仓库、文档、聊天）。
- 不要把批次 A–E 旧包写成「已真机验证」（没有独立证据；只有当前包 `build-9c2fc63` 的功能点抽查）。
- 不要改 `docs/audit/**` 与 `AUDIT.md`/`AUDIT_LOG.md`（A 队只读；需统筹主持转达独立督导）。
- 不要伪造门禁/测试数字：以 `tools/test_results.json`、`git`、CI run 为准。
- 不要在 `HANDOFF` 堆积历史长文：上一版见 `git show 35b8fc7:docs/HANDOFF.md`。
