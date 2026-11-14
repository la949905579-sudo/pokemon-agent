# HANDOFF（换会话先读这个）

- **状态**（2026-11-14 20:5x）：**模式已固化**（单会话 + 本地循环）；HEAD=`d7740d6`＝origin/master；工作树空；未推送 0；无进行中任务。
- **最新发布**：Release `build-1f305ad…`（含自动战斗，已 OTA 装机）；CI run `43595142649` success。
- **结构**：`native-emu/` = Android App（Kotlin + Compose + mGBA C/C++ 核心）；`pyplatform/` = Python 旧自动化（冻结）；数据 `games/pokemon_firered/{maps,battles,dialogs,data/moves.json}`；`tests/` = 31 个 Python 离线测试；根 `run_tests.py` = 测试入口；`tools/` = `emu_probe.py` / `gen_moves_data.py`。
- **构建/验证**：Kotlin 单测本机可跑（aapt2 走 qemu wrapper，命令见 `AGENTS.md`）；**APK/NDK 必须走 CI**（push 触发）；Python 旧层 `python3 run_tests.py`。
- **规则/文档**：`AGENTS.md`（循环 / 验证 / 红线 / 交接）｜`docs/TASKS.md`（任务/验收）｜`docs/ARCH.md`（架构/语言）｜`docs/CHANGELOG.md`（每发布 3–5 行）；历史 `docs/archive/2026-11/`（只读）。
- **已完成（本模式）**：工作流重设计、M4/M5 迁移、**名表 354**、**自动战斗**（真机实测通过）。
- **未做/暂缓**：**横屏 + 触屏所见即所得**（需求已定，只差设置面板形态＝覆盖层/全屏页）、**联机**（调研）、结构债（随手做）；**地图相关全部暂缓**。
- **接手 5 分钟**：
  1. `git status --short`（期望空）、`git rev-list --count origin/master..HEAD`（期望 0）
  2. 读 `docs/TASKS.md`（任务与验收）→ 用户点名任务后按 `AGENTS.md` 循环开工
  3. 快速验证：`python3 run_tests.py`（≈31/31）、Kotlin 单测命令见 `AGENTS.md`
- **环境**：手机 Android proot Ubuntu；真机自测用手机工具（OTA 安装 / 点击 / 截图）；证据 `/sdcard/Download/DSH-Go/`；应用日志 `/sdcard/Download/emu_native.log`。
- **不要**：恢复 A/B 合同、审计督导、成本快照、BATCHES/考官/总线/`.pilot`（旧体系已归档，如需查历史见 `docs/archive/2026-11/`）。
