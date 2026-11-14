# 工作守则（2026-11-14 重设计版）

> 仓库内唯一流程规则。旧 A/B 合同制、审计、成本快照已停用；历史文档在 `docs/archive/2026-11/`（只读）。

## 角色
- **用户**：需求 / 验收 / 拍板。
- **代理（你）**：需求对接、设计、实现、本地构建、真机自测、提交推送。**单会话，不分 A/B，不写合同。**
- **子代理**：只用于 ①独立模块并行 ②高风险改动的 fresh 复核。简报 ≤15 行，回执 ≤10 行。

## 开发循环（每任务 15–60 分钟）
1. 任务卡 3 行（目标 / 验收 / 范围）写 `docs/TASKS.md`，再开工。
2. 实现，小步提交（1 任务 = 1 提交）。
3. 本地验证（日志只回 `tail`/`grep`，不灌全量）：
   - **Kotlin 单测本机可跑**（aapt2 走 qemu wrapper，首次约 2 分钟）：
     `ln -sfn /root/workspace/native-emu/tools/aapt2-wrapper /root/android-emu-local/aapt2`
     `cd native-emu && /opt/gradle-8.9/bin/gradle :app:testDebugUnitTest --no-daemon --console=plain -Pandroid.aapt2FromMavenOverride=/root/android-emu-local/aapt2 2>&1 | tail -30`
   - **APK / NDK 编译必须走 CI**（NDK clang 是 x86_64，proot 下无法本地执行）：commit + push 即触发。
   - 签名：`native-emu/app/keystore-info.txt`（gitignore，不碰内容）
4. 真机自测：装 CI 产出的 APK（Release / App OTA）→ 截图 / 读状态取证，证据存 `/sdcard/Download/DSH-Go/`。
5. 失败最多修 3 轮；超了回设计。
6. 每 1–3 个任务 push（CI 构建 Release）；用户试玩验收。

## 验证（只 3 条）
1. 编译 + 单测绿；2. 真机可运行且附证据；3. 任务卡验收点通过。
危险区（FFI / 内存地址 / 签名 / OTA / 删除 / 迁移）加 1 次 fresh 复核。

## 红线
- 不碰 `native-emu/app/keystore*`（签名 / 口令）；不伪造测试 / 构建 / 真机结论。
- 不 `--no-verify`、不 force push、不 amend 已推提交。
- 一次只做一个任务；范围外改动先说清。
- 日志只 grep/tail；截图每任务 ≤2 张；不读长文档、不整文件通读。

## 文档
- `docs/TASKS.md`（任务 / 验收）｜`docs/HANDOFF.md`（≤20 行现状，换会话先读）｜`docs/ARCH.md`（架构 / 语言 / 构建）｜`docs/CHANGELOG.md`（每发布 3–5 行）。

## 会话交接（换会话时）
1. 先读 `docs/HANDOFF.md` + `docs/TASKS.md`（各 1 分钟）。
2. 开工自检：`git status` 空、`git rev-list --count origin/master..HEAD`=0、单测绿；任一红先修再开工。
3. 本模式已定型（2026-11-14）：单会话、任务卡驱动、CI 出包、真机自测；**不要**恢复 A/B 合同 / 审计 / 台账（历史在 `docs/archive/2026-11/`）。
