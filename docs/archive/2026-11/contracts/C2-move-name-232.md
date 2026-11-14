# C2 招式名表 232（功能型）

> 归属：A 队 ｜ 生命周期：活（试点期） ｜ 维护者：A（代理人）
> 状态机：`open → claimed → green|blocked → accepted`，运行态见 `.pilot/C2/status.json`。
> 状态：accepted（试点样本，2026-11-14 转常设后保留）

## 1–2 合同号 / 类型：C2 ｜ 功能型（含判断项 + 真机项；本批 1 批）

## 3 事实快照（2026-11-13 17:3x 实测）
- HEAD：`b647270`；`git status --short` 空；`origin/master..HEAD` = 0
- 名表：`native-emu/app/src/main/java/com/dsh/emu/game/GameData.kt` 的 `moves`，共 55 条；文件头注释写「从 Python 的 bdata.py 生成，勿手改」
- 数据源：`bdata.py` 的 `MOVES`——字面量 59 条 / 唯一键 55 条（40、41、42 重复同值；58 重复且值不同，后者生效）→ 生成须按 Python dict 语义，**条数校验用去重后条数**
- `grep -n '232' GameData.kt bdata.py`：0 命中（232 未收录）
- 生成脚本：仓库内**未找到**「bdata.py → GameData.kt」的生成脚本（B 须先核实/重建生成链路）
- 缺陷台账：`docs/NATIVE_EMU_TODO.md:138`（P3 名表 232 未收录，战斗页显示 `#232`）
- Kotlin 单测目录：`native-emu/app/src/test/java/com/dsh/emu/game/**`

## 4 基线提交（B 开工前记录）
- B 开工前 `git rev-parse HEAD` 写入 `.pilot/C2/status.json` 的 `base` 字段；本批所有「改动」判据用 `<base>..HEAD`，**不用 `HEAD~1`**（一批常含多个提交）。

## 5 背景与目标
战斗页第 4 招 id=232 显示 `#232` 而非中文名，原因是名表少条导致显示映射漏项。
目标：从**数据源**补名表并重生成 Kotlin 生成表（禁止手改生成表）；补离线单测；给出真机确认步骤。

## 6 任务清单（WBS）
- ① 找名表数据源与生成链路（`bdata.py` `MOVES` ↔ `GameData.kt`），确认 232 及同批缺失项；生成链路若不存在，先补链路（脚本放 `native-emu/tools/`，属本批写入范围），不得凭记忆手写生成表。
- ② 在数据源补 232（同批缺失项逐条列出并注明来源），重生成 `GameData.kt`（diff 必须同时出现数据源与生成表改动）。
- ③ 补 ≥1 条离线单测：名表查找 / 显示映射（Python 断言 `MOVES[232]` 存在；Kotlin 断言名字非空且非 `#232`）。
- ④ 真机确认按 7.3 步骤由用户执行，结果回给 A。

## 7 验收
### 7.1 机械项（命令 + 期望输出/退出码）
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 run_tests.py` | exit 0，且输出含新增测试文件名 `PASS` 行（runner 格式 `PASS  <name>`，末行 `N/M 通过`）；不能只看总数或 exit 0 |
| M2 | CI run（`:app:testDebugUnitTest`） | 该 step success 且 run conclusion=success；回执写 run id 留证 |
| M3 | `grep -c 'to Triple' native-emu/app/src/main/java/com/dsh/emu/game/GameData.kt` | **去重后条数** = 55 + 新增条数（回执写实际值与去重依据） |
| M4 | `git diff --name-only <base>..HEAD` | 同时含数据源（`bdata.py`/生成脚本）与 `GameData.kt` |

### 7.2 判断项（说明）
- 名表来源可信度：回执必须写出来源与依据（官方招式表 / ROM 数据 / 交叉验证），A 验收时看证据；**不得自拟中文名、不得只写「已补」**。

### 7.3 真机项（用户执行，具体步骤）
- ① 用含本批的 build/OTA 更新并进入游戏；② 触发一场野生战（战斗页自动切换）；③ 看战斗页第 4 招格是否显示中文名（非 `#232`）；④ 回 A 一句「第 4 招显示：<名字>」。

## 8 写入范围
- 允许：`native-emu/**`、`tests/**`、`bdata.py`（若数据源在此）、`docs/NATIVE_EMU_TODO.md`（勾选该条）。
- 不允许：手改 `GameData.kt`（只能经生成链路产出）、keystore/签名、`docs/audit/**`、`docs/roles/**`。

## 9 禁止项
- 不伪造名表、不写来源；不手改 Kotlin 生成表；不碰 keystore；不空提交；不 force push。
- 不改验收口径或写入范围；不顺手改无关招式数据。

## 10 变更规则
- B 可改实现路径（数据源位置、生成脚本实现）；不可改验收口径、写入范围、目标。
- 不可行（如生成链路无法重建 / 名表来源无法核实）：1 轮内写 `.pilot/C2/status.json` 置 `blocked` + 回执 ≤3 行原因，停手等 A 裁定。

## 11 回执
- 位置：`.pilot/C2/result.md`（≤10 行，首行 `session: <id> ｜ 状态: green|blocked`）。
- 必含：提交号 / 产物路径 / 机械项结果 / 名表来源与依据 / 真机步骤 / 风险 / 待确认。
