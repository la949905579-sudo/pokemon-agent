# C1 测试收拢（tests/ 迁移）

> 归属：A 队 ｜ 生命周期：活（试点期） ｜ 维护者：A（代理人）
> 状态机：`open → claimed → green|blocked → accepted`，运行态见 `.pilot/C1/status.json`。

## 1–2 合同号 / 类型：C1 ｜ 机械型（本批 1 批，全部机械验收）

## 3 事实快照（2026-11-13 17:3x 实测）
- HEAD：`b647270`；`git status --short` 空；`origin/master..HEAD` = 0
- 根目录 `test_*.py`：29 个（`git ls-files | grep -c '^test_.*\.py$'` = 29）；`tests/` 目录不存在
- 测试入口：`run_tests.py`（glob 根目录 `test_*.py`）；结果台账 `tools/test_results.json`（python 29）
- Kotlin 单测在 `native-emu/app/src/test`，**本批不碰**；`.github/workflows/build-native-emu.yml` 无 Python 测试引用

## 4 基线提交（B 开工前记录）
- B 开工前 `git rev-parse HEAD` 写入 `.pilot/C1/status.json` 的 `base` 字段；本批所有「改动」判据用 `<base>..HEAD`，**不用 `HEAD~1`**（一批常含多个提交）。

## 5 背景与目标
M3 结构债：根目录测试文件平铺，违反 `docs/STRUCTURE.md` §五 P1「`test_*.py` 全收进 `tests/`」。
目标：只搬不改，`tests/` 收拢后离线测试全绿、测试入口与索引同步。

## 6 任务清单（WBS）
- ① 盘点根 `test_*.py` 与现有测试入口（`run_tests.py`、`tools/test_results.json`），列迁入清单。
- ② `git mv` 逐个迁入 `tests/`（保留历史；禁止 rm 后重新 add）。
- ③ 修 import / `sys.path` / 相对路径与 `ROOT` 引用，保持**完全离线**（不读实机状态、不写业务文件；需落盘写临时目录）。
- ④ 同步引用：`run_tests.py`（glob 改 `tests/test_*.py`）、`docs/STRUCTURE.md`、`docs/README.md`（若有引用）、`.github/`（若有引用，实测无）。
- ⑤ 重生成 `docs/generated/FILES.md`；由 B 侧助理更新 `tools/test_results.json`（记录实际通过数）。

## 7 验收
### 7.1 机械项（命令 + 期望输出/退出码）
| # | 命令 | 期望 |
|---|---|---|
| M1 | `python3 run_tests.py` | exit 0，且通过数 ≥29（与 `tools/test_results.json` 一致） |
| M2 | `git ls-files \| grep -c '^test_.*\.py$'` | 输出 `0` |
| M3 | `git ls-files tests/ \| wc -l` | ≥ 29 |
| M4 | `python3 tools/gen_files_index.py --check` | exit 0 |
| M5 | `git diff --name-only <base>..HEAD -- native-emu/` | 输出为空（用 `<base>`，不用 `HEAD~1`） |

- 判断项：无（机械型全项可脚本判定）；回执须写 M1 实际通过数与 M2/M3 实际输出。`tools/test_results.json` 由 **B 侧助理**更新，C1 验收只核 `run_tests.py` 输出与该文件一致，不要求 B 改测试结果口径。

## 8 写入范围
- 允许：`tests/**`、`run_tests.py`、`docs/STRUCTURE.md`、`docs/README.md`、`docs/generated/FILES.md`、`tools/`（仅 `tools/test_results.json` 更新 + 路径引用）。
- 不允许：`native-emu/**`、`docs/history/**`、`docs/audit/**`、`docs/roles/**`、`docs/contracts/**`。

## 9 禁止项
- 不改测试语义、不删测试、不合并测试、不改断言；不夹带行为变更；不留半搬半留的过渡态。
- 不碰 B 队文件（`docs/audit/**`、`docs/roles/b/**`）、不碰 `native-emu/**`；不改 `docs/history/` 正文；`docs/generated/**` 只经脚本。
- 禁止 force push、空提交、伪造门禁数字。

## 10 变更规则
- B 可改实现路径（如批量迁移方式）；不可改验收口径、写入范围、目标。
- 不可行：1 轮内写 `.pilot/C1/status.json` 置 `blocked` + 回执 ≤3 行原因，停手等 A 裁定。

## 11 回执
- 位置：`.pilot/C1/result.md`（≤10 行，首行 `session: <id> ｜ 状态: green|blocked`）。
- 必含：提交号 / 产物路径 / M1–M5 结果 / 风险 / 待确认。
