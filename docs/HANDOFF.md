# HANDOFF（≤20 行，换会话先读这个）

- **状态**（2026-11-14 20:0x）：工作流重设计已完成；HEAD=迁移提交；工作树空；无进行中任务（等用户点名）。
- **结构**：`native-emu/` = Android App（Kotlin + Compose + mGBA C/C++ 核心）；根目录 `.py` = Python 旧自动化（冻结）；`tests/` = Python 离线测试；`tools/` 仅 `run_tests.py` / `emu_probe.py`。
- **构建**：Kotlin 单测本机可跑（`/opt/gradle-8.9/bin/gradle :app:testDebugUnitTest --no-daemon --console=plain -Pandroid.aapt2FromMavenOverride=/root/android-emu-local/aapt2`，wrapper `native-emu/tools/aapt2-wrapper`）；**APK/NDK 必须走 CI**；签名口令 `app/keystore-info.txt`（gitignore）。
- **测试**：Kotlin 单测在 `native-emu/app/src/test`；Python 旧层 `python3 run_tests.py`（冻结期只保证不坏）。
- **发布**：push 到 master 且改动 `native-emu/**` → GitHub Actions 出 `build-<sha>` Release → App 内 OTA。
- **规则**：`AGENTS.md`（循环 / 验证 / 红线）；架构：`docs/ARCH.md`；任务：`docs/TASKS.md`；历史：`docs/archive/2026-11/`。
- **下一步**：等用户讨论后定任务（候选见 `docs/TASKS.md`）。
- **环境要点**：手机 = Android proot Ubuntu；真机自测用手机工具（安装 / 点击 / 截图）；证据存 `/sdcard/Download/DSH-Go/`。
