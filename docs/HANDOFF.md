# 交接文档（HANDOFF）

> 2026-11-13 14:5x · 批次 5 / A-19 规范批收口交接（本会话批次结束，交接新会话）
> 给新会话（新统筹主持）：先读本文件 + `docs/TEAM.md`（§二 重建步骤）+ `docs/HANDOVER.md` + `docs/NATIVE_EMU_TODO.md`。
> **本文件是交接唯一真源，聊天记录不算。** 历史长文已迁出：上一版交接（F2/A–E 真机记录、T5 豁免对账）见 `git show 35b8fc7:docs/HANDOFF.md`。

## 交接（2026-11-13 14:5x）

- **事实快照**：`origin/master` = `8365526`（批次5 收尾已推）；本 **A-19 规范批 + 交接材料** 为 amend 后单条 docs（`git log --oneline -1` 可查；其前端 tools 条 `2e70a67` 同批待推）。推送后 `origin/master..HEAD` = 0（远端为真源）。批次 1–5 全部在 origin/master。
- **当前目标**：本会话批次工作结束 → **交接**：新会话按 `docs/TEAM.md` §二 + `docs/HANDOVER.md` §二 重建（读本文件/TEAM/HANDOVER → 跑 `run_tests` + `session_health` → spawn 助理/工匠，考官按批叫）。
- **审查状态 / 豁免凭据**：2026-11-13 提前审（B 队 `docs/audit/REPORT-20261113.md`，窗口 `3decf36..ac26275`）＝**有条件通过**；整改状态——A-18（push 考官门禁）/A-22（T4 窗口口径）/A-23（A-10 误报）已落地（`26fcef4`/`2e70a67`/`6fdf29e`）；A-2/A-3 已改「以 `tools/test_results.json` 为准」；A-10 已扩并修误报；A-19 本条落地（`TEAM` §一 ↔ `write_scopes` 一致）；A-20 部分（HANDOVER 模板行）；A-21 部分（复盘件已落，8 项度量实现留新会话）；A-5 待下轮 REQUEST。T5 交接豁免见 `docs/audit/AUDIT_LOG.md`。
- **已完成（批次 1–5，全部在 origin/master，提交号/CI/Release/真机）**：
  - 批次1（M1）：`95b861b` docs 分区 `history/`+`generated/`；考官可发布（0 阻断）。
  - 批次2（M6）：`ab402fa` 审查件归并 `docs/audit/`；考官可发布。
  - 批次3（F2 遗留）：`97bb03c`（结构债/取消轮询/单测）、`8b38330`（A-10/A-15）、`ff93b78`（CI 证据）、`e22328f`/`401ebfa`（docs）；CI `43321435153`/`43322690329` success；Release `build-ff93b78…`；真机 06:55–06:58（3 招点击/切页不卡键）。
  - 批次4（MainActivity 拆分 + A-16）：`6ec7350`（≈710→311 + 4 新 ui + `StatusParserTest`）、`8b99815`（A-16）、`8435b37`/`112817b`（docs）；CI `43366232788` success；Release `build-112817b…`；真机 12:49–12:53。
  - 批次5（审查整改 + A* 跨图）：`3ba213d`（A-10/A-17/A-18）、`067a230`（A* 跨图）、`afef639`/`26fcef4`/`6fdf29e`/`8365526`（收尾与修复）；CI `43375557906` success；Release `build-5bbe4f4…`（APK 11,592,027B，digest `sha256:bd88f0cb…`；tag 实际指向 `e54b240`）；真机 14:0x（OTA/地图/Tab/行走/野生战/战斗页/火花）。
  - 规范批：`1926b17` 策略顾问角色卡；**A-19 规范批** `2e70a67`（tools）+ 本 docs 条（`TEAM` §一/§七/§八、`PLAN-20261113-5`/`-6` 原样、`BATCHES`/`HANDOFF`、`FILES` 255 文件、0 未描述、`NATIVE_EMU_TODO` 同步、`CHANGELOG` v2026.11.13-2/-3/-4）。
- **批次 A–E 真机补验（build `5bbe4f4`，2026-11-13）**：
  - **A**：常驻状态行「TCP :55401 · ROM名 · map/FPS」正常；设置页「重置/退出」整行按钮正常。
  - **B**：非战斗为常驻地图页；战斗中**自动切换**到战斗页（关按键面板后即显示敌方 16 / 16、我方 22 / 25、招式格）——自动切换确认。
  - **C**：Tab 点两次关闭（队伍→地图页）；地图 Tab 对应整张城镇图。
  - **D**：队伍详情完整（属性 火 / 等级 8 / HP 22 / 25 / 经验 393 / 419（差 26 升级）/ 4 招式 + PP）；地图页「点格子预览路线（不会立刻走）」提示在（canvas 点击因帧比对无法自动化，未实测）。
  - **E**：非战斗常驻页直接整张城镇图、地图 Tab 置灰（点不动）。
  - 另：野生战触发正常（波波 Lv3）。**A\* 跨图本构建无 UI 入口，未覆盖**（仅库+单测/CI）。
- **未完成 / 待办**：
  - **A-21（新会话）**：按 `docs/org/PLAN-20261113-6.md` 实现 8 项度量（docs 占比 / 打回率 / 转达失真 / 超线会话等）+ METRICS 模板「指标/值/类型（自动·人工·无数据）/阈值/判定」；无数据不默认。
  - **A-5**：下轮 `REQUEST` 补「T4 结果」必填段，窗口起点先 `git cat-file` 验真。
  - **A\* 6 图补采**：缺 assets 的 6 张图补采 `map_links.json` 条目；无高度层；`side` 语义待真机；需 UI 入口才能真机验证。
  - **结构债剩余**：`MainActivity` 拆分后 311 行（达标）；`EmuView`/`WalkControl` 等仍有零散逻辑可继续迁出；UI 回归已冒烟。
  - **tag 指向瑕疵**：`build-5bbe4f4` tag 实际指向 `e54b240`（target_commitish 默认；构建覆盖仍含 `5bbe4f4`）。
  - **APK 大小 nit 已解**：Release API 403 期间用下载 HEAD 核得 11,592,027B / digest `bd88f0cb…`。
- **关键决策（为什么）**：M1 物理分区、M6 审查件归并（只移动+同批改引用）；docs 每批 ≤3、同会话 ≤1、来源标注；A-10/A-17/A-18 机械化闸门；A-22 T4 改「窗口内新增复发>0」；A\* 小步可验证（先 5 图连通域，缺 assets/高度层后补）；B 队 M1/M6 授权已确认（`9f35637`）；F2 最小范围 fail-closed。
- **规则**：docs ≤3 条/批（同一会话 ≤1）；不同来源同批须标注来源；无写权限来源由助理代提交；docs 占比 >50% 触发复盘；A-22 新 T4 口径 2026-11-19 前生效。
- **下一步（新会话）**：① 按 `TEAM` §二 重建（先跑 `run_tests` + `session_health`）；② 第一批候选：A-21 8 项度量（PLAN-6）、A\* 6 图补采 + UI 入口、A-5 REQUEST 必填、代码迁移 M3/M4/M5（等 F 批发布）；③ 新批必写 `BATCHES` 一条。
- **不要做什么（最值钱）**：
  - **共享工作树并发 push 风险**：本会话 2 次被其他会话连带推送（`5bbe4f4` 带 code/tools、`290ee1a` 带 `afef639`/`26fcef4`）；提交/推送前必 `git fetch` + `git log origin/master..HEAD` 对齐，发现分叉先同步再推。
  - **push 需考官结论（A-18）**：带 `EXAMINER_OK`/`--examiner-ok` 并在输出留痕；**不 amend / force push 已推送提交**。
  - **不改 `docs/history/` 旧文正文**（历史不回改，新复盘按日期单开）；生成物（`FILES`/`METRICS`）只重跑脚本。
  - **不手改 A-10 豁免范围**；新过期文案改源头文档。
  - **不碰 `docs/audit/**` 规则正文**（B 队只读；跨队改动经主持转达独立督导）；不碰 `docs/roles/b/**`。
  - **不碰 keystore / token**（签名固定，轮换会导致已装 App 无法覆盖升级）。
  - **不用空提交触发构建**；不伪造门禁/测试数字（以 `tools/test_results.json`、`git`、CI run 为准）。
  - **A-22 口径**：T4 用「窗口内新增复发>0」，不要再用累计复发判红。
  - **不要囤长文**：HANDOFF 只留最近 2–3 批摘要，历史见 `git show 35b8fc7:docs/HANDOFF.md`。

## 交接前置检查（HANDOVER §二，2026-11-13 14:5x 实测）

| # | 项 | 结果 |
|---|---|---|
| 1 | `git status` 干净 | ✅ 本 docs 条提交后为空 |
| 2 | 提交状态 | 批次1–5 已推（`origin/master`=`8365526`）；本 A-19 2 条（`2e70a67`+docs）待推送，推送后 `origin/master..HEAD` = 0 |
| 3 | CI 绿 | ✅ 最近 master run `43375557906` success；Release `build-5bbe4f4…` 已发 |
| 4 | `python3 run_tests.py` | ✅ 通过（数量以 `tools/test_results.json` 为准：python 29） |
| 5 | TODO/CHANGELOG 与代码同步 | ✅ `NATIVE_EMU_TODO` 已同步 F2 遗留；`CHANGELOG` 已追加 v2026.11.13-2/-3/-4 |
| 6 | `gen_files_index.py` 重生成 + `--check` | ✅ 重生成后 `--check` exit 0（255 文件/0 未描述，收录 PLAN-20261113-5 与 -6） |
| 7 | 本文件更新（当前状态/阻塞/下一步/不要做什么） | ✅ 本提交（按 HANDOVER §三 模板重写） |
| 8 | 无未结束后台任务/子代理 | ✅ 无 |
| 9 | `precommit_check.sh --scope docs/ tools/` | ✅ 通过（A-17 对组织规划 3 文件仅告警＝代提交预期） |
| 10 | `check_ui_state.py` | ✅ 通过（34 个 Kotlin 文件读写配对） |
| 11 | `session_health.mjs` / `token_report.mjs --json` | ✅ 已跑，摘要见交接回执（`b3505b33` 142 轮已交接；成本按新职位归因） |
| 12 | 交接预告 | ✅ 用户 2026-11-13 14:3x 决定本批后交接；新会话按 `TEAM` §二 重建；A-21 留新会话 |

- **Kotlin 单测**：以 `tools/test_results.json` 为准（当前 kotlin 101；批次5 新增 12 条已由 CI `43375557906` 构建步骤覆盖，`test_results` 待新会话更新至 113）。
- **接手 5 分钟**（HANDOVER §五）：
  ```bash
  cd /root/workspace
  git status --short                                   # 期望空（队友未提交文件除外，不要 add -A）
  git log -3 --oneline                                 # 期望含 A-19 tools/docs
  git rev-list --count origin/master..HEAD             # 推送后期望 0
  python3 run_tests.py                                 # 数量以 tools/test_results.json 为准
  python3 tools/gen_files_index.py --check             # 期望 0
  ```

## 构建 / 发布现状

- **最新构建 / 发布 = `build-5bbe4f4fc8312a16f76cf8b89ee276d7059a161e`**（批次5；master CI run `43375557906` success，`publish release` success；APK `app-debug.apk` 11,592,027B，digest `sha256:bd88f0cb…`；tag 实际指向 `e54b240`）。
- 真机：批次5 回归冒烟（build `5bbe4f4` OTA）+ 批次 A–E 补验 + F2/批次4 回归，详见上「真机记录」。
- 上一版 `build-112817b…`（批次4）、`build-ff93b78…`（批次3）保留；判构建覆盖看 `docs/generated/METRICS.md` 的 tag→提交映射；CI 仅在推送含 `native-emu/**` 时构建（按推送 tip 打 tag）。

## 旧路径豁免清单（grep 口径，B 队已确认）

(a) `docs/history/` 内正文；(b) `git show <旧提交>:<旧路径>` 历史引用；(c) `docs/org/PLAN-*` 等已定稿旧记录；(d) 历史台账正文不回改：`docs/audit/AUDIT_LOG.md` 3 处、`docs/audit/REPORT-20261112.md` 1 处。工作树**活体**文档/工具/脚本旧路径 = 0。

## 不要做什么（补充，最值钱）

- **不要在本会话继续干活**（已交接）；A-21 由新会话按 `PLAN-20261113-6` 做。
- 不要在 `HANDOFF` 堆积历史长文：上一版见 `git show 35b8fc7:docs/HANDOFF.md`。
