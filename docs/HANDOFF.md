# 交接文档（HANDOFF）

> 2026-11-13 05:2x · 项目重建 P0 提交后交接（本会话结束）
> 给新会话（新统筹主持）：先读本文件 + `docs/TEAM.md`（§二 重建步骤）+ `docs/HANDOVER.md` + `docs/NATIVE_EMU_TODO.md`。
> **本文件是交接唯一真源，聊天记录不算。** 历史长文已迁出：上一版交接（F2/A–E 真机记录、T5 豁免对账）见 `git show 35b8fc7:docs/HANDOFF.md`。

## 交接（2026-11-13 05:2x）

- **当前目标**：项目重建 P1「会话重建」——新统筹主持按 `docs/TEAM.md` §二 spawn 助理 + 工匠，开始重建后的第一批功能/迁移批次。
- **已完成**（带提交号，远端 `origin/master` 即真源）：
  - `4378149` 项目重建 P0（本批，17 文件 +514/−513）：重写 `TEAM`/`HANDOVER`/`README`/`STRUCTURE`/`org/README`；角色卡按队拆（`docs/roles/a/{assistant,artisan,examiner}.md`、`docs/roles/org/architect.md`、`docs/roles/README.md`）；删旧 `docs/roles/{steward,artisan,examiner,architect}.md`；新建批次台账 `docs/BATCHES.md`；重建总方案 `docs/org/PLAN-20261113-4.md`；`docs/FILES.md` 重生成（233 文件/0 未描述）。
  - `9c2fc63` F2 招式点击施放（下屏战斗页 4 招点击施放，1 提交 1 构建；真机 4 招全过）。
  - `35b8fc7` F2 状态同步（CHANGELOG v2026.11.13-1、TODO、HANDOFF 旧版、NOTES、FILES、`tools/test_results.json` 82/29）。
  - `08a0d74` F1 后 HANDOFF 补录（T5 口径定稿 + 真机字段 + 不要做什么）。
- **未完成 / 卡住**：
  - F2 遗留：拒绝路径（未开菜单/回读不一致）与切页·收面板中断**仅单测覆盖、未真机触发**；`ui/BattleMoveAction.kt` 直接读内存的结构债；`MainActivity.kt` 710 行 > 500 上限；A 后轮询未查 cancelled；P3 名表 `id=232` 缺口（界面显示 `#232`）。均记于 `docs/NATIVE_EMU_TODO.md`「批次 F2 遗留」。
  - 批次 A–E 旧包无独立真机证据（历史日志早于批次 C、OTA 下载失败）；只有 `build-9c2fc63` 上的 A–E 功能点抽查（旧 HANDOFF §二·七，见 `git show 35b8fc7:docs/HANDOFF.md`）。
  - docs 迁移未做：M1 `history/`+`generated/`、M2 B 队卡迁 `roles/b/`、M6 审查件归并（待独立督导同意）——见 `docs/org/PLAN-20261113-4.md` §六 P2。
  - 旧 B 队整改 A-10～A-13 是否仍适用，需按新流程复核（新规则：整改并入下一功能批，只有 P0 单开）。

## 交接前置检查（HANDOVER §二，2026-11-13 05:2x 实测）

| # | 项 | 结果 |
|---|---|---|
| 1 | `git status` 干净 | ✅ 空 |
| 2 | 提交已推远端 | ✅ `origin/master` = HEAD = `4378149`，`origin/master..HEAD` = 0 |
| 3 | CI 绿 | ✅ 最近构建 run `43266619857`（`build-9c2fc63`，attempt=1，success）；其后提交均 docs-only，pre-push 判定不触发构建 |
| 4 | `python3 run_tests.py` | ✅ 29/29 通过（数字以 `tools/test_results.json` 为准） |
| 5 | TODO/CHANGELOG 与代码同步 | ✅ F2 已于 `35b8fc7` 同步；P0 只改 docs |
| 6 | `gen_files_index.py` 重生成 + `--check` | ✅ 已重生成（233/0），`--check` exit 0 |
| 7 | 本文件更新（当前状态/阻塞/下一步/不要做什么） | ✅ 本提交 |
| 8 | 无未结束后台任务/子代理 | ✅ 旧队三名成员均 inactive；job 仅历史完成/已杀任务 |
| 9 | `precommit_check.sh --push` | ✅ 推送后复跑通过（见本提交前门禁输出） |
| 10 | `check_ui_state.py`（有 Kotlin UI 改动） | ✅ 通过，无只写不读 |
| 11 | 机械闸门已装 | ✅ `.git/hooks/pre-commit`（159B）、`pre-push`（105B）均在 |

- **交接触发**：用户判定本会话已超 100 轮阈值（HANDOVER §一 硬指标）并要求「只做三件事后交接」。`node tools/session_health.mjs` 对当前会话文件显示健康（轮次 2 / 压缩 0 / 空回合 0，exit 0）——脚本按当前会话文件计数，以用户裁定为准执行交接。
- **Kotlin 单测**：最近实跑 82/82（`9c2fc63`，MoveCasterTest 11/11）；此后无 Kotlin 改动，见 `tools/test_results.json`。
- **接手 5 分钟**（HANDOVER §五）：
  ```bash
  cd /root/workspace
  git status --short                                   # 期望空
  git log -1 --pretty='%h %s'                          # 期望 4378149
  git rev-list --count origin/master..HEAD             # 期望 0
  python3 run_tests.py                                 # 期望全过
  python3 tools/gen_files_index.py --check             # 期望 0
  ```

## 构建 / 发布现状

- **最新构建 = `build-9c2fc63`**（CI run `43266619857`，success，唯一 1 次构建；Release 自动发布，APK 11,575,075B）。
- 该构建已装到手机并完成 F2 真机验证（版本 `0.2 (9c2fc63) / 构建 11-13 01:11`）；APK 也在 `/sdcard/Download/DSH-Go/native-emu-9c2fc63.apk`。
- 判构建覆盖看 `docs/METRICS.md` 的 tag→提交映射；CI 仅在推送含 `native-emu/**` 时构建（按推送 tip 打 tag）。

## 关键决策（为什么）

- **规则文档重写 + 角色卡按队拆**：落实「单会话单身份」；助理每批新开，保护统筹主持寿命；旧名 `builder`/`verifier`/`steward` 永久禁用。
- **F2 最小范围**：仅招式菜单已展开（`TURN_FLAG==2` 且 `MAIN_CURSOR==0`）时可点；不做主菜单自动打开；fail-closed + 失败即停，避免误操作。
- **docs 提交每批 ≤1 个**、`BATCHES` 只追加：控制文档反客为主。
- **B 队文件 A 队只读**（`AUDIT.md`/`AUDIT_LOG.md`/`docs/audit/**`），跨队改动经统筹主持转达独立督导。
- **本批 P0 未单独叫考官**：按用户指示「本轮只做三件事后交接」；重建规则本身由用户 03:00–05:30 逐项核对定稿（见 PLAN §五）。台账备注同此。

## 下一步建议（给新统筹主持）

1. 按 `docs/TEAM.md` §二 重建：读 `HANDOFF`/`TEAM`/`HANDOVER` → 跑 `run_tests.py` + `session_health.mjs` → spawn `assistant` + `artisan`（考官按批叫）。第一批任务从本文件与 `docs/NATIVE_EMU_TODO.md` 取。
2. 接手验收过了，再与用户确认下一批。候选：
   - F2 遗留收尾（异常路径真机 + 结构债）；
   - 批次 A–E 真机补验，或由用户明确接受「只验当前包」；
   - P2 迁移 M1/M2/M6（每个迁移单独一批，验收四连）。
3. 新批必写一条 `docs/BATCHES.md` 记录（只追加）。

## 不要做什么（最值钱）

- **不要在本会话继续干活**（已交接结束，新会话重建后再做）。
- 不要重排已完成的**存档 3 槽 / 队伍详情 / 地图交互**（用户 11-12 决定：地图只修 bug、不加交互控件）。
- 不要用空提交触发构建；不要 amend / force push 已推送提交。
- 不要碰 keystore / token（签名固定，轮换会导致已装 App 无法覆盖升级；口令/密钥不进仓库、文档、聊天）。
- 不要把批次 A–E 旧包写成「已真机验证」（没有独立证据；只有当前包 `build-9c2fc63` 的功能点抽查）。
- 不要改 `docs/audit/**` 与 `AUDIT_LOG.md`（A 队只读；需统筹主持转达独立督导）。
- 不要伪造门禁/测试数字：以 `tools/test_results.json`、`git`、CI run 为准。
- 不要在 `HANDOFF` 堆积历史长文：上一版见 `git show 35b8fc7:docs/HANDOFF.md`。
