# 团队手册（TEAM）

> 团队是**会话级**的：`builder` / `verifier` 挂在发起它们的那个会话上，换会话不会继承。
> 新会话要做的不是“加入”，而是“按本手册重建”。

## 一、编制（3 + 1）

| 成员 | 中文名 | 职责 | 写入范围 |
|---|---|---|---|
| `lead` | 主持 | 派活、最终审查、推送、发布、写 `docs/` | 全部 |
| `artisan` | 工匠 | 实现与修复（**带 shell**） | `native-emu/**`、根目录 `test_*.py` |
| `examiner` | 考官 | 只读复核，出结论（**带 shell**） | 无（不写文件） |
| （按需）`auditor` | 督导 | 流程审查，一次性会话 | 无 |

`auditor` 不常驻——按里程碑/事故另开新会话，提示词见 `docs/roles/auditor.md`。

> **2026-11-12 重建记录**：原 `builder` / `verifier` 诞生于 `workspace-write` 策略下，
> 本机没有沙箱后端 → 它们的 bash 全被拒，只能改文件、不能提交/跑测试。
> 会话策略改为 `danger-full-access` 后，**只有新建成员才继承新策略**，所以重建为
> `artisan` / `examiner`。旧的 `builder` / `verifier` 留在原地、不再派活。

## 二、重建步骤（新会话，3 分钟）

1. 读 `docs/HANDOFF.md` → 了解当前状态；读 `docs/roles/builder.md`、`docs/roles/verifier.md`。
2. 各 spawn 一个，**名字固定**：
   - `builder`（prompt = builder.md 里的代码块）
   - `verifier`（prompt = verifier.md 里的代码块）
3. 让 `verifier` 先做一次基线核查（测试 + CI + 文档一致性），再从 `NATIVE_EMU_TODO.md` 派第一个任务给 `builder`。

**为什么名字必须固定**：`STRUCTURE.md`、任务派发、`FILES.md` 里都按名字引用，改名会让文档全部失效。

## 三、任务流转

```
Lead 建任务（目标 + 验收标准 + 写入范围）
   → builder 认领、实现、commit（不 push）
   → verifier 复核，给「可发布 / 不可发布」+ 证据
   → Lead 审 diff、跑测试、push、观察 CI
   → 需要时发布 Release、更新 HANDOFF
```

规则：
- 同一文件同时只允许一个写入者。
- `verifier` 的结论必须带证据（行号 / run 链接），否则 Lead 不采信。
- 任务被打回两次，换任务而不是硬催——通常是上下文已经污染。

## 四、度量（每里程碑由 `verifier` 算一次）

记在 `docs/METRICS.md`（没有就新建），只记能自动算的：

| 指标 | 定义 |
|---|---|
| CI 首次通过率 | 每个提交第一次构建是否绿 |
| 打回率 | verifier 判「不可发布」的次数 / 复核次数 |
| 复发率 | `INCIDENTS.md` 已固化的问题再次出现次数 |
| 上手时间 | 新会话从开工到第一个有效提交 |
| 交接次数 | 因上下文退化被迫换会话的次数 |

**复发率是唯一硬指标**，其余用来解释原因。

## 五、失败模式（已知）

| 现象 | 处理 |
|---|---|
| 成员跑不了 `bash` | 让它只出判断，命令由 Lead 代跑，并在结论里注明。**实测（2026-11-12）：builder 与 verifier 在本会话都无法执行 bash**（无沙箱后端，升级被拒），所以：builder 的 commit 由 Lead 代打，verifier 的测试由 Lead 代跑——这会让「独立验证」打折，结论必须标注「编译结论来自 CI / 测试由 Lead 代跑」 |
| 两个会话同时改同一仓库 | 交接前旧会话必须停手；推送前先 `git pull --rebase` |
| 长会话空回复 | 见 `docs/HANDOVER.md` 的交接阈值，到点就换 |
| 团队重建后行为漂移 | 说明提示词没覆盖到，把这次的教训补进 `docs/roles/*.md` 并升版本号 |
