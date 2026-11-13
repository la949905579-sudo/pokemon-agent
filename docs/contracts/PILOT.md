# 合同制试点操作手册（PILOT）

> 归属：A 队 ｜ 生命周期：活（试点期） ｜ 维护者：助理
> 试点：2026-11-13 用户确认（A=代理人 / B=承包主持，2 个合同 C1/C2）；授权范围见 `docs/BATCHES.md` 试点落盘行。
> 本文件自包含：重建 A/B 会话时复制对应口令即可，不必再读长文档。

## 一、用户转达句（复制发 B）

「B，C1 合同已就绪，按 docs/contracts/C1-tests-consolidation.md 执行。」

（C2 就绪后由 A 创建 `.pilot/C2/inbox.ready`，并把同一句里的 `C1` 换成 `C2`。）

## 二、A 口令（代理人，复制即用）

```text
你是 A（代理人）。先读 docs/contracts/PILOT.md、docs/TEAM.md §三·七、docs/contracts/C1-tests-consolidation.md。
只读需求 + 合同 + B 的回执；不读 diff、不读构建日志、不读长文档（要证据就让 B 给路径）。
本轮只做三件：① 确认 C1 口径（口头一句）→ ② 让用户把 B 口令发给 B → ③ 等回执。
收到回执后验收：只抽查 1 条机械验收（任选 M1–M5 之一，命令 + 期望各一行）；判断项看回执里的来源与依据。
产出：≤10 行回执（首行 session id、状态、提交号、门禁、风险、待确认）；不派活、不改合同、不碰实现。
```

## 三、B 口令（承包主持，复制即用）

```text
你是 B（承包主持）。先读 docs/contracts/PILOT.md、docs/contracts/C1-tests-consolidation.md、docs/TEAM.md。
按合同执行 C1：开工前把 git rev-parse HEAD 写入 .pilot/C1/status.json 的 base 字段；spawn 助理（只做机械门禁 + 提交，不 push）与工匠（只改写入范围）；每批叫考官复核，考官「可发布」后才推送。
回执写 .pilot/C1/result.md，≤10 行，首行 session: <id> ｜ 状态: green|blocked；写提交号、产物路径、门禁、判断项依据、风险、待确认。
C1 收尾后：若 .pilot/C2/inbox.ready 不存在，挂后台 job 等唤醒——
  while [ ! -f .pilot/C2/inbox.ready ]; do sleep 5; done; echo C2_READY
（存在则直接继续 C2，读 docs/contracts/C2-move-name-232.md。）
```

## 四、watcher（B 侧等待 C2 的唯一方式）

```bash
while [ ! -f .pilot/C2/inbox.ready ]; do sleep 5; done; echo C2_READY
```

- 由 A 在 C2 合同就绪后创建：`touch .pilot/C2/inbox.ready`（`.pilot/` 已 gitignore，不入库）。
- 唤醒后 B 读 C2 合同开工；不重复轮询、不自行改等文件位置。

## 五、判定表（试点成功/失败）

| 指标 | 阈值 | 判定方式 |
|---|---|---|
| 全量 token 增量/批 | ≤ 基线×0.85（基线＝开工前当日窗口实测、不含本试点落盘行，见第六节；不写死） | 第六节测量法：窗口增量 ÷ 2 批 |
| 首次回执一次过 | 至少 1 个（C1、C2 中）首轮回执直接验收 | A 验收记录 |
| 转达失真 | 0 | 回执事实 vs 仓库实测（HEAD/提交/路径）逐条核对 |
| 单批周期 | ≤ 1 天（`docs/TEAM.md` §三：一批 = 可验收最小功能集合） | 合同 open → accepted 的墙钟时间 |
| 回执/合同行数 | 回执 ≤10 行；合同 ≤60 行 | `wc -l .pilot/<id>/result.md` |
| docs 提交 | ≤3 条/批（同一会话 ≤1 条） | `git log` |

## 六、成本测量法（开工前定基线，验收后算增量）

```bash
# 开工前：当日窗口（日期＝试点开工日；开工日=2026-11-13 就填此日期，跨日替换）
mkdir -p .pilot
node tools/token_report.mjs --json --since <试点开工日> > .pilot/cost-before.json
# 基线 = days[].totalTokens 之和 ÷ 窗口内 BATCHES 批次记录数（不含本试点落盘行：现 10 行 → 用 9）
node -e 'const fs=require("fs"),f=JSON.parse(fs.readFileSync(".pilot/cost-before.json"));const n=Number(process.argv[1]);const t=f.days.reduce((s,d)=>s+d.totalTokens,0);f.pilotBaseline={windowTotal:t,batches:n,baselinePerBatch:Math.round(t/n)};fs.writeFileSync(".pilot/cost-before.json",JSON.stringify(f,null,2));console.log(f.pilotBaseline)' 9
# 验收后：同一 since → cost-after.json
node tools/token_report.mjs --json --since <试点开工日> > .pilot/cost-after.json
node -e 'const fs=require("fs"),b=JSON.parse(fs.readFileSync(".pilot/cost-before.json")),a=JSON.parse(fs.readFileSync(".pilot/cost-after.json"));const dl=a.days.reduce((s,d)=>s+d.totalTokens,0)-b.pilotBaseline.windowTotal;const per=dl/2;const lim=b.pilotBaseline.baselinePerBatch*0.85;console.log(`试点增量=${dl} ｜ 每批=${per} ｜ 阈值=${Math.round(lim)} ｜ ${per<=lim?"OK":"超"}`)'
```

- 口径：**全量 token 增量 = 窗口内所有会话 total 之和的增量**（after 与 before 的 `days[].totalTokens` 合计之差）；试点共 2 批 → 每批 = 增量 ÷ 2，判定 **每批 ≤ 基线×0.85**。
- 基线不写死：B 在试点开工前跑上面命令实测，并把结果写入 `.pilot/cost-before.json` 的 `pilotBaseline` 字段（参考核对：2026-11-13 17:5x 当日窗口约 6.000 亿 ÷ 9 条批次记录〔不含本试点落盘行〕≈ 66.7M/批，数字会涨）。
- A/B 各自把 session id 写进 `result.md` 首行，仅作归因，不改变上式口径。

## 七、回滚步骤（试点结束）

1. 先 `git revert <C1 批次提交>`、`git revert <C2 批次提交>`（若已合并；此序避免 revert 试点提交时 `docs/BATCHES.md`/`docs/generated/FILES.md` 出现 UU 冲突）。
2. 再 `git revert <试点落盘提交>`：一次恢复 `docs/BATCHES.md`、`.gitignore`、`docs/generated/FILES.md` 并删除 `docs/contracts/`；**不要先 `git rm`**（工作区不干净会让 revert 失败，已实测）。
3. 最后 `rm -rf .pilot/`（已在 `.gitignore`，工作树不受影响）。
