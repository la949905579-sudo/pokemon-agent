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

> 追记：批次1 考官结论 = **可发布**（`95b861b`，0 阻断；nit＝`docs/README.md:19` 措辞已在批次2 处理）。
> 追记：批次1 已推送 origin/master=`95b861b`；考官=可发布（0 阻断）。
> 追记：批次2 已推送 origin/master=`ab402fa`；考官=可发布（0 阻断）。
> 追记：A-10（precommit 过期文案检查 + metrics --check 窗口验真）、A-15（session_health --all 兼容无数据）已在批次3 tools 提交落地。
