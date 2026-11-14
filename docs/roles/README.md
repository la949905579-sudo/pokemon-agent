# docs/roles/ 角色卡索引

> 命名规则：**文件名 = 英文实例名小写**；卡内职位名一律用中文。
> 旧名 `builder` / `verifier` / `steward` 永久禁用；历史文档不回改。

| 队 | 职位 | 实例名 | 角色卡 |
|---|---|---|---|
| B 成员（承包商 spawn） | **助理** | `assistant` | `docs/roles/a/assistant.md` |
| B 成员（承包商 spawn） | **工匠** | `artisan` | `docs/roles/a/artisan.md` |
| B 成员（承包商 spawn） | **考官** | `examiner` | `docs/roles/a/examiner.md` |
| A 队 | **代理人** | `proxy` | `docs/roles/a/proxy.md` |
| A 队 | **承包商** | `contractor` | `docs/roles/a/contractor.md` |
| A 队（A 派发） | **真机执行** | `device` | `docs/roles/a/realdevice.md` |
| A 队 | **审计督导**（子会话） | `supervisor` | `docs/roles/a/supervisor.md` |
| B 队（停设） | **独立督导** | `audit-lead` | 停设（B 队旧编制），职责转 A 队 → `docs/roles/a/supervisor.md` |
| B 队（停设） | **审查员** | `auditor` | 停设（B 队旧编制），职责转 A 队 → `docs/roles/a/supervisor.md` |
| B 队（停设） | **成本管理员** | `audit-cost` | 停设（B 队旧编制），职责转 A 队 → `docs/roles/a/supervisor.md` |
| A 队（A 按需发起） | **组织规划** | `architect` | `docs/roles/org/architect.md` |
| 用户侧（**停用**） | **策略顾问** | `advisor` | `docs/roles/org/advisor.md`（停用说明） |

- B 队三张卡（`6841960` 迁入）自 2026-11-14 **停设**（B 队旧编制），职责转 A 队；审计 / 督导改由代理人按需 spawn 一次性审计督导子会话（`docs/roles/a/supervisor.md`）。
- **代理人 / 承包商均为用户开的独立主会话**（A 不 spawn B）；承包商按卡 spawn 助理 / 工匠 / 考官，审计督导由 A spawn，真机执行由 A 派发，组织规划由 A 按需发起（分工 / 结构规划员随之一并 spawn）；**子代理不能再 spawn**。
- **策略顾问（`advisor`）已停用**（2026-11-14 16:4x 用户拍板）；卡仅历史存档、只读。
- 代理人角色卡见 `docs/roles/a/proxy.md`（重建口径按 `docs/TEAM.md` §二）；其余职位按上表。
