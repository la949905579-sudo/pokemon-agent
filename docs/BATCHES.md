# 批次台账（BATCHES）

> 归属：A 队 ｜ 生命周期：活 ｜ 维护者：助理
> **只追加**，不改历史条目；`HANDOFF.md` 只保留最近 2–3 批摘要。
> 门禁与流程见 `docs/TEAM.md` §三·五；门禁「四连」验收见 `docs/STRUCTURE.md` §五。

## 模板

| 批次 | 日期 | 内容 | 提交号 | 考官结论 | 门禁 | 备注 |
|---|---|---|---|---|---|---|
| <编号> | YYYY-MM-DD | <一句话> | `<hash>` | 可发布 / 不可发布 | 提交前 ✅ 推送前 ✅ | <坑 / 请示> |

## 记录

| 批次 | 日期 | 内容 | 提交号 | 考官结论 | 门禁 | 备注 |
|---|---|---|---|---|---|---|
| 重建-20261113 | 2026-11-13 | 项目重建 P0/P1：重写 `TEAM`/`HANDOVER`、角色卡按队拆（a/、org/）、`docs/README`、新建 `BATCHES`；规则依据用户逐项核对（人员 10 项 / 流程 6 项 / 文件 6 项） | `4378149` | 未叫考官（用户指定本轮只做三件事后交接；规则由用户逐项核对定稿） | 提交前 ✅ 推送前 ✅ | 17 文件（6 改 4 删 7 新增，含 `FILES` 重生成）；doc-only 不触发 CI；B 队卡与 `history/`、`generated/` 迁移待后续 |
| 批次1-M1 | 2026-11-13 | docs 分区迁移 M1：`FILES`/`METRICS` → `docs/generated/`，`CHANGELOG`/`INCIDENTS`/`RETROSPECTIVE`/`NOTES`/`ARCHITECTURE` → `docs/history/`（7 文件 `git mv`，history 正文不改）；工具/活文档路径同步 + 索引与 `METRICS` 重生成 | 本批唯一提交（`git log --oneline -1` 可查） | 待考官轻量复核（doc-only） | 提交前 ✅ 推送前 ⏳（未 push，等统筹主持拍板） | **docs 提交每批 ≤1 个：本批仅 1 条**；旧路径豁免：`history/` 正文、git 历史引用、`docs/org/PLAN-*` 旧记录、B 队只读（`AUDIT.md`/`AUDIT_LOG.md`/`docs/audit/**`，待督导跟进）；根 `README.md`/`AGENTS.md` 旧路径本批已同步。**§五.4 一次性授权留痕**：2026-11-13 ｜ 授权人：统筹主持 ｜ 范围：`docs/roles/b/*.md` 仅旧路径引用同步（未改正文/职责，3 文件 4 行）+ 根 `README.md`/`AGENTS.md` 路径引用（仅路径）；待督导确认（转达由统筹主持执行） |
| 批次2-M6 | 2026-11-13 | M6 审查件归并：审查件 `AUDIT`/`AUDIT_LOG` 由 `docs/` 顶层 `git mv` 入 `docs/audit/`（2 文件）；活体引用同步（TEAM/README/HANDOFF/roles a+b/audit 活体互引/org/README/tools/metrics.py）；`AUDIT_LOG` 保持 R100 纯 rename、历史台账正文不回改；同批顺带 README:19 中性表述、BATCHES 追记、HANDOFF 更新 | 本批唯一提交（`git log --oneline -1` 可查） | 待考官轻量复核（doc-only） | 提交前 ✅ 推送前 ⏳（未 push，等拍板） | **docs 提交每批 ≤1 个：本批仅 1 条**；M6 同意依据=`6841960`；**§五.4 一次性授权留痕**：2026-11-13 ｜ 授权人：统筹主持 ｜ 范围：AUDIT/AUDIT_LOG 搬入 `docs/audit/` + B 队文件（`docs/audit/**`、`docs/roles/b/**`）仅路径引用（未改职责/规则正文）；待督导确认；旧路径豁免（待督导确认）：`docs/audit/AUDIT_LOG.md` 3 处（`docs/AUDIT.md`×1 + `docs/METRICS.md`×2）、`REPORT-20261112.md` 1 处（`docs/AUDIT.md`×1）、`docs/org/PLAN-*` 旧记录（AUDIT/AUDIT_LOG 18 + M1 路径 16）、`docs/history/` 正文 1、git 历史引用 |
| 批次3-F2 | 2026-11-13 | F2 遗留收尾（非代码部分）：① 方案箱落地——组织规划 5 文件原样提交（PLAN-4 §九 / org/README「方案箱」/ TEAM 三·八 / docs/README §二 / roles/org/architect）② 台账/交接修正 + 授权闭环（B 队 `c599b72` 回执）③ A-10 文档过期检查 + A-15 巡检兼容（tools 条） | docs=`本提交`（`git log --oneline -1`）；tools=`chore(tools)`（`git log --oneline -2`） | 待考官轻量复核 | 提交前 ✅ 推送前 ⏳（待本批统一推送） | docs 每批 ≤1：本批 docs 1 + tools 1；A-10 顺带修 `TOOLS.md` 过期测试数（28→29）；代码部分（结构债/单测/cancelled）由工匠负责；§五.4 授权闭环见 HANDOFF |
| 批次4 | 2026-11-13 | 批次4：MainActivity 拆分（≈710→311 行）+ 4 个新 ui 文件（EmuView / StatusParser / WalkControl / LocalStatus）+ 1 个新测试（StatusParserTest 6 例）；A-16 工具链中文职位名/成本归因修复 | code=`6ec7350`；tools=`8b99815`；docs=本条 | **待 CI/考官/真机**（收尾追记见下批 docs） | 本批 docs ≤3、本条 #1；code `check_ui_state` 过（34 文件全配对）；A-16 未知职位 4 会话/59,666,019 token→0；Kotlin 静态 101 条待 CI 复跑 |
| 规范-docs-20261113 | 2026-11-13 | 规范 docs 批：策略顾问角色卡（`docs/roles/org/advisor.md` 新）+ `TEAM` §1.1/§二/三·九 + `docs/roles/README` + `docs/README` §三/§四 扩写；来源＝组织规划正文 + 统筹主持 `REQUEST`（助理代提交） | docs=本提交（`git log --oneline -1`） | 待轻量复核 | 提交前 ✅ 推送前 ⏳（待拍板） | docs 本批 1 条 ≤1（按用户口径规范批）；用户 13:0x 确认「已落盘」；提纲环节由用户直接确认（组织规划未另出提纲文件）；不卷批次4 已提交内容 |
| 批次5 | 2026-11-13 | 批次5：B 队提前审整改 + A* 跨图移植——tools A-10/A-17/A-18 整改；code CrossMap（MapLinks/CrossMapPathfinder/CrossMapWalker + map_links.json + 12 测试）；docs 收尾 A-2/A-3/A-20/A-21 | tools=`3ba213d`；code=`067a230`；docs=本条 | **待 CI/考官/真机**（收尾追记见下批 docs） | 本批 docs ≤3、本条 #1；A* 限制：6 图缺 assets→5 图连通域、无高度层、side 语义待真机；A-10 扩模式 + WORKPLAN 修复、A-17 写入范围、A-18 推送门禁已落 |

> 追记：批次1 考官结论 = **可发布**（`95b861b`，0 阻断；nit＝`docs/README.md:19` 措辞已在批次2 处理）。
> 追记：批次1 已推送 origin/master=`95b861b`；考官=可发布（0 阻断）。
> 追记：批次2 已推送 origin/master=`ab402fa`；考官=可发布（0 阻断）。
> 追记：A-10（precommit 过期文案检查 + metrics --check 窗口验真）、A-15（session_health --all 兼容无数据）已在批次3 tools 提交落地。
> 收尾追记（批次1）：已推送 origin/master=`95b861b`；考官=可发布。
> 收尾追记（批次2）：已推送 origin/master=`ab402fa`；考官=可发布（0 阻断）。
> 收尾追记（批次3）：提交 docs `e22328f` + 代码 `97bb03c`（F2 结构债/取消轮询/单测 +13）+ tools `8b38330`（A-10/A-15）+ `ff93b78`（CI 证据）+ 本收尾 docs 条；CI `43321435153`（验证分支，绿）与 `43322690329`（master，绿，Release `build-ff93b78…`，APK 11,575,075B）；考官 task-9 = **可发布**（Kotlin 95/95 双证）。
> 真机记录（2026-11-13 06:55–06:58，`build-ff93b78` OTA）：加载 ROM / 继续冒险正常；2 场野生战；战斗页血条正确；「抓 / 叫声 / 火花」3 招点击施放成功、回合推进；招式菜单打开时切页未误按键 / 未卡键；第 4 格空（Lv7 仅 3 招）；「施放瞬间切页」未掐点触发，仍只有单测覆盖。
> 收尾追记（批次3·B 队回执 `9f35637`）：M1/M6 一次性授权**确认有效**（`AUDIT_LOG` 授权确认节）；A-7 交接登记；A-10/A-15 核销「已落地」；新增 A-16（助理待办：工具链旧名/成本归因）；元审查一条不追改。
> 规则追记（2026-11-13 用户拍板）：docs 提交每批 ≤1 → **≤3 条（同一会话 ≤1 条）**；不同来源可同批、须标注来源；无写权限来源由助理代提交；占比 >50% 触发复盘，超 3 条只复盘不阻断。本批 docs=2 ≤3。
> 收尾追记（批次4）：CI `43366232788`（master，**success**，`build`/`upload-artifact`/`publish release` 全 success，Release `build-112817b27fcc599e49248a5f11380aab3c2a1e1f`，APK 11,575,075B）；考官 task-15 = **可合 master**（0 阻断）；已合入 master（`401ebfa..112817b`）。
> 真机记录（2026-11-13 12:49–12:53，`build-112817b` OTA）：版本/构建更新成功、游戏继续；Tab 队伍/背包/名字/图鉴/存档/设置均可切（存档 Tab 双击回地图页）、地图页渲染（「点格子预览路线」提示在）；按键行走正常；2 场野生战正常；战斗页双方等级/HP/招式正确；火花 16→0、抓 14→5 施放成功、回合推进；招式菜单打开时切页→不误按键/不卡键、返回后仍可施放。**未覆盖**：「施放瞬间切页」施放太快未掐到（单测覆盖）；地图点格子预览因截图/帧比对无法自动化（页面渲染已确认）。
> 收尾修正（批次4 nit）：① A-16 归因写「实测快照 12:16：4 会话 / 59,666,019（7.6%）；考官同口径复算 74,297,991（9.1%），差异＝助理会话 cacheRead 增长/快照时刻，非归因错误」；② Kotlin=**101/101**；③ 批4 行「5 个新 ui」已校正为「4 新 ui + 1 测试」。本批 docs=2 ≤3。
