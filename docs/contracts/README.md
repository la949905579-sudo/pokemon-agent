# 合同制目录（docs/contracts）

> 归属：A 队 ｜ 生命周期：活 ｜ 维护者：代理人（`proxy`）
> 2026-11-14 转常设（试点 C1/C2 已 accepted）；规则唯一真源见 `docs/TEAM.md` §三·十，本文件只写目录约定与校验用法。

## 用途

合同制常设：A（`proxy`，代理人）写合同与验收，B（`contractor`，承包商）只读合同执行。

- **编号**：试点 C1/C2 标「样本」（保留、不回改）；正式合同从 **C3** 起递增。
- **粒度**：一个合同可含 ≤3 批（每批 ≤1 天），验收按批分列；>3 批拆合同。
- **并发**：同一时间只允许 **1 个 open 合同**（A 负责检查）。
- **寿命**：A >50 轮或压缩 ≥1 交接、完成合同段即关；B 默认每合同新开，同合同段复用 ≤3 合同或 >30 轮即轮换，accepted 且推送后关闭。

## 目录约定

- 合同 spec 入仓库：`docs/contracts/C<编号>-<slug>.md`（只读口径，B 按合同执行）。
- 运行态不入库：`.pilot/<id>/`（`status.json`、`result.md`、成本快照），已在 `.gitignore` 忽略。
- 命名：`C<编号>-<slug>.md`；编号从 C3 起递增（C1/C2 为试点样本），slug 用英文短横线词。
- 归档：合同文件平铺保留，按 docs 归档规则（30 天 / 同主题 3 份）盘点，不单独建子目录。
- `CONTRACT-TEMPLATE.md` 模板；`PILOT.md` 为试点记录（保留，不再作为现行规则）。

## 状态机

`open → claimed → green | blocked → accepted`，每次流转写 `.pilot/<id>/status.json`：
`{"id":"C3","state":"claimed","by":"B","base":"<git rev-parse HEAD>","claimedAt":"...","attempts":1,"commit":"...","session":"...","accepted":{...}}`。
必填：`base`（开工前 HEAD）、`claimedAt`、`commit`、`session`；accepted 时加 `accepted`（验收记录，**必含 `by` / `verdict`**，`at` 建议）。
**attempts**：B 首次回执写 `attempts:1`，每次返工 +1；有该字段时须为 ≥1 的整数（缺省按 1 计，兼容 C1/C2 样本）。

## 校验（提交前）

```bash
python3 tools/contract_check.py --contract docs/contracts/C1-tests-consolidation.md --status .pilot/C1/status.json
```

校验：必填标题、合同 ≤60 行、status 字段 / 状态机、`base` 是合法提交、`attempts`（有则须 ≥1 整数；accepted 缺省给警告）、`result.md` ≤10 行、accepted 记录须含 `by` / `verdict`、accepted 时 `BATCHES` 含 `合同:<id>` 且 `git diff --name-only <base>..<commit>` 落在合同 §8 写入范围（豁免 `.pilot/**`）；`cost.json` 存在时字段须齐（`windowTotal` / `baselinePerBatch` / `delta` / `perBatch` / `threshold`）；全部通过 exit 0（警告不阻断）。

暂存 `docs/contracts/C<id>-*.md` 时，`tools/precommit_check.sh` 要求 `.pilot/<id>/status.json` 存在且上条校验通过，否则拒绝提交（提示扩合同 / 补运行态）。

## 谁写什么

| 角色 | 写什么 | 不写什么 |
|---|---|---|
| A（`proxy`，代理人） | 合同 spec、验收结论 | 实现、回执正文 |
| B（`contractor`，承包商） | `.pilot/<id>/result.md` 回执（含证据路径）、`status.json` | 合同口径 / 写入范围 |
| B 侧助理 | 机械门禁与提交、`BATCHES` 行、`test_results`、`FILES` | 不判定质量 |

- 回执 ≤10 行：状态 / 提交号 / 产物路径 / 门禁 / 风险 / 待确认；首行附 session id（成本归因）。
- 每批必带：`BATCHES` 行（备注 `合同:<id>`）+ `test_results` 同步 + `FILES` 重生成；`HANDOFF` 在批次收尾 / 交接前更新，不要求每批改。
- 合同只约束本批；变更须 A 书面同意并留痕。
- **成本判据（双判据，唯一口径）**：每批增量 ≤ 基线×0.85 **且** ≤30M/批；`cost-after` 在 accepted 后取；成本快照存 `.pilot/<id>/cost.json`（`{windowTotal,baselinePerBatch,delta,perBatch,threshold}`），无快照按「无数据」处理、不默认 0/红。
- **成本快照工具（v1.3）**：`python3 tools/cost_snapshot.py --contract <id>` 读 `tools/token_report.mjs --json`，生成上述 5 字段 + `byRole`；`perBatch` 按 `BATCHES` 里 `合同:<id>` 行数折算；accepted 后取。
- **开工前成本基线（v1.4）**：A open 后跑 `python3 tools/cost_snapshot.py --before <id>` 落 `.pilot/<id>/cost-before.json`（`windowTotal` / `batches` / `baselinePerBatch` / `threshold`）；`--contract` 缺省优先读它作基线。claimed 态缺该文件 `contract_check` 记警告，**C5 起改阻断**。
- **合同收尾（v1.4）**：A 置 accepted 后跑 `python3 tools/contract_close.py <id>`，强校验 accepted / `contract_check` / `BATCHES` / cost 双判据（缺项 exit 1），并打印 BATCHES 追记行草稿 + HANDOFF 摘要行 + METRICS 重生成提示；**未 accepted（open/claimed/green）记 SKIP 且 exit 0**（提交前预跑只看预览草稿，A 置 accepted 后重跑才做正式校验）；**只打印不改台账**。
- **真机项执行（v1.3）**：真机项交「真机执行」（实例 `device`，fresh 会话）按合同 §7.3 跑 `python3 tools/emu_probe.py --check-move <id>`；**`emu_probe` 工具只读 TCP :55401、不写文件也不截屏**，截图由执行者用手机截并存 `/sdcard/Download/DSH-Go/probe-<id>-<ts>.jpg`；回执 `PASS/FAIL <id> <name>` + 截图路径，A/B 只记结果、不代跑。
- **启动提示词（v1.4）**：A open 后按 `CONTRACT-TEMPLATE.md` §12 骨架产出承包商启动提示词（角色卡 + 合同 + TEAM → `batch_facts` → 写 status → 执行 → 回执），与合同一并交给 B。
- **v1.3 预算规则**：裁决会话 0 截图 / 0 长文、证据只给路径、零轮询（单次等待 ≤20min）、A ≤5M/批目标，见 `docs/TEAM.md` §三·十二。
- **度量 2 项（同口径）**：合同一次通过率＝首轮 accepted 占比（分母=accepted 合同；<70%→复盘）；每合同成本＝accepted 合同 perBatch 均值（超 30M 或基线×0.85 记超）；数据源 `.pilot/*/status.json`、`.pilot/*/cost.json`。
