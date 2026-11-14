# 组织规划请求 2026-11-13（第 2 号：策略顾问角色卡 + TEAM 扩写）

> 代理人（A 队）写给组织规划（architect）。按方案箱接口**五字段**填写；事实快照以 2026-11-13 12:1x 实测为准。
> 组织规划**只写不提交**；提交与推送归助理（规范 docs 批，`docs` 提交每批 ≤1 条）。

## 一、窗口

2026-11-13 12:1x 起，**一个规范 docs 批**：只做「策略顾问角色卡 + TEAM/roles README 扩写」。
**不与批次 3 的 `e22328f`（及其收尾 `401ebfa`）合并**；本批 `docs` 提交 ≤1 条。

## 二、关注点

1. **新建角色卡**：按 `/sdcard/Download/DSH-Go/advisor-role-card.md` 的草案，新建 `docs/roles/org/advisor.md`（实例名 `advisor`；照抄草案内容，只做最小格式/路径一致性调整，不新增职责）。
2. **扩写 `docs/TEAM.md`**（按 `/sdcard/Download/DSH-Go/advisor-team-patch.md` 的补丁）：
   - §一 1.1 编制表：「策略顾问」行改为——`advisor`／用户点名开（单次 ≤10 轮）／参谋：理需求、挑毛病、核对回执、给选项、压口径；不代拍板／**写入范围：无（只读）**；
   - §二 重建步骤末尾追加「策略顾问」重建段（读 HANDOFF/TEAM/角色卡、只读、≤10 行汇报、>10 轮或完成即关）；
   - 新增「**三·九、策略顾问接口**」摘要小节（触发/输入/产出/边界/落盘），只写摘要并**指向角色卡**，避免双份真源。
3. **扩写 `docs/roles/README.md`**：表格新增一行「用户侧 ｜ 策略顾问 ｜ `advisor` ｜ `docs/roles/org/advisor.md`」；末行注改为「代理人角色卡见 `docs/roles/a/proxy.md`（重建口径按 `docs/TEAM.md` §二）；其余职位按上表」。

## 三、已知争议

**顾问写入范围「无（只读）」与 `docs/org/PLAN-20261113-3.md` §3.1「意见进 `docs/org/`」冲突。**
裁定：采用「**只读 + 由用户或代理人落盘**」；需要留痕时由用户/代理人写 `docs/org/PLAN-<日期>-advisor.md` 或 REQUEST 附录，顾问不直接写仓库。草案（角色卡「接口」节）已按此写。

## 四、事实快照（2026-11-13 12:1x 实测）

- HEAD：`401ebfa docs(批次3收尾): 方案箱规则调整(组织规划) + 批次台账/交接收尾(助理) + METRICS 重生成`
- `origin/master`：`401ebfa`；`origin/master..HEAD` = 0（写请求时）
- `git status --short`（批次 4 进行中，非空属预期；读请求时 HEAD 可能已变，请以 `git log -1` / `git status` 复查后按当时事实执行）：

```
 M native-emu/app/build.gradle.kts
 M native-emu/app/src/main/java/com/dsh/emu/MainActivity.kt
 M native-emu/app/src/main/java/com/dsh/emu/ui/BattlePage.kt
 M native-emu/app/src/main/java/com/dsh/emu/ui/MapPage.kt
 M native-emu/app/src/main/java/com/dsh/emu/ui/Pages.kt
 M tools/metrics.py
 M tools/test_results.json
 M tools/token_baseline.json
 M tools/token_report.mjs
?? native-emu/app/src/main/java/com/dsh/emu/ui/EmuView.kt
?? native-emu/app/src/main/java/com/dsh/emu/ui/LocalStatus.kt
?? native-emu/app/src/main/java/com/dsh/emu/ui/StatusParser.kt
?? native-emu/app/src/main/java/com/dsh/emu/ui/WalkControl.kt
?? native-emu/app/src/test/java/com/dsh/emu/ui/StatusParserTest.kt
```

- 关联草案原文（只读，不在仓库内）：
  - `/sdcard/Download/DSH-Go/advisor-role-card.md`
  - `/sdcard/Download/DSH-Go/advisor-team-patch.md`
- 参考：`docs/org/PLAN-20261113-3.md` §3.1（争议来源）；`docs/roles/README.md`（现有索引表）。

## 五、期望产物

1. **先出提纲**（≤15 行：新建/修改文件清单、关键措辞、影响面、待确认点）交代理人转用户确认；**用户确认后再落盘**（提纲未确认不得细化）。
   > 本批按用户 2026-11-13 13:0x 直接确认落盘执行（未另出提纲文件）。
2. 落盘范围**仅限**：`docs/roles/org/advisor.md`（新建）、`docs/TEAM.md`、`docs/roles/README.md`；经用户确认追加 `docs/README.md` §三/§四（元数据四选一 + `PLAN-<日期>-advisor.md` 命名）；不改其他文件。
3. 组织规划**只写不提交**；提交归助理（规范 docs 批，`docs` 每批 ≤1 条，不与批次 3 合并）。
4. 回执 ≤10 行：结论 / 产物路径:行号 / 待确认 / 风险；**不要复述过程**。

## 六、T4 结果（后续请求必填；A-5）

> 2026-11-13 起，每次跨会话请求（`REQUEST.md`）必须包含本节三字段；缺一不可。
> A-5 助理侧部分：本节模板已落；脚本侧窗口验真由 `python3 tools/metrics.py --check --window <rev>` 支持。
> 归属待审计督导确认（A-5 原始要求：`REQUEST` 增必填「T4 结果」+ 窗口起点先 `git cat-file` 验 + 写实际提交数）。

- **T4 结果**：<未触发 / 触发（原因）/ 无数据>（取 `docs/generated/METRICS.md` §〇 第 4 项或 `metrics.py --check`）
- **窗口起点**：`<rev>`（先 `git cat-file -e <rev>^{commit}` 验真；窗口＝上次完整审查之后）
- **实际提交数**：`git rev-list --count <rev>..HEAD` = <N>（写请求时实测）

> 参考示例（2026-11-13 15:5x 实测）：T4 **未触发**（窗口 `2026-11-13` 内新增复发 0）；窗口起点 `5bbe4f4`（`git cat-file` ✓）；`5bbe4f4..HEAD` 实际 **10** 个提交（写请求时）。
