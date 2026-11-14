# HANDOFF（换会话先读这个）

- **状态**（2026-11-15 01:4x，**本轮已收工、准备交接**）：**模式已固化**（单会话 + 本地循环）；HEAD＝origin/master（最新**代码/发布**提交 `d67eab1`，其后只有文档收口提交）；工作树空；未推送 0；无进行中任务；手机竖屏 App 运行中、游戏停在 `(38,11)`（存档槽 1 = 用户 00:31 存档，测试只读未写）。
- **最新发布**：Release `build-d67eab1…`（横屏纯画面 + WYSIWYG：对话选项 / 战斗菜单背包·宝可梦·逃跑 / 子菜单取消条；已装机并真机验收；fresh 复核 3 轮通过，结论「可上线」、无必修）。
- **结构**：`native-emu/` = Android App（Kotlin + Compose + mGBA C/C++ 核心）；`pyplatform/` = Python 旧自动化（冻结）；数据 `games/pokemon_firered/{maps,battles,dialogs,data/moves.json}`；`tests/` = 31 个 Python 离线测试；入口 `run_tests.py`；`tools/` = `emu_probe.py` / `gen_moves_data.py`。
- **构建/验证**：Kotlin 单测本机可跑（aapt2 走 qemu wrapper，命令见 `AGENTS.md`）；**APK/NDK 必须走 CI**（push 触发）；Python 旧层 `python3 run_tests.py`。
- **规则/文档**：`AGENTS.md`（循环 / 验证 / 红线 / 交接）｜`docs/TASKS.md`（任务/验收）｜`docs/ARCH.md`（架构/语言）｜`docs/CHANGELOG.md`（每发布 3–5 行）；历史 `docs/archive/2026-11/`（只读）。
- **已完成（本模式）**：工作流重设计、M4/M5 迁移、**名表 354**、**自动战斗**、**横屏纯画面 + WYSIWYG**（对话选项/战斗菜单/子菜单取消，均真机实测通过；复核 3 轮通过）。
- **未做/暂缓**：横屏后续（背包道具行/队伍格子点选、3+ 选项框、镜头贴边标定）、**联机**（调研）、结构债（含 WYSIWYG 3 条非阻塞清理）；**地图相关全部暂缓**。
- **图片证据**：`/sdcard/Download/DSH-Go/wysiwyg-*.jpg`（8 张：横屏纯画面 / 面板 / 战斗菜单 / 背包 / 点地图走位 / 竖屏前后）。
- **内存地址（实测）**：`sMenu`=0x0203ADE4、`gWindows`=0x020204B4、`BATTLE_MENU_FLAG(E83)`=0x02023E83（E83!=0 才是真战斗菜单，==0 是战斗内是/否选项框）。
- **接手 5 分钟**：① `git status --short` 期望空、`git rev-list --count origin/master..HEAD` 期望 0；② 读 `docs/TASKS.md`（todo 列表）→ 用户点名任务后按 `AGENTS.md` 循环开工；③ 快速验证 `python3 run_tests.py`（31/31）+ Kotlin 单测（命令见 `AGENTS.md`）。
- **环境**：手机 Android proot Ubuntu；真机自测用手机工具（OTA / 点击 / 截图）；证据 `/sdcard/Download/DSH-Go/`；日志 `/sdcard/Download/emu_native.log`；游戏内存/按键可用 localhost TCP 桥（`read/press/frame`，端口 55401）做标定取证。
- **真机点击限制（重要）**：本会话 `tap_xy` 坐标手势被安全策略拒绝（报「没有已通过本次过滤的截图」），真机坐标点击只能 `handoff` 让用户点；元素点击（`tap id`）正常。`android_shell`（需 Shizuku/自连 ADB）可跑 `input tap`，但本会话未开启。
- **OTA 兜底安装（GitHub CDN 抖动时）**：proot 里 `cd /sdcard/Download/DSH-Go && python3 -m http.server 8765 --bind 127.0.0.1` → 手机 Via 打开 `http://127.0.0.1:8765/<apk>` → 下载后 `handoff` 让用户点「安装 / 继续安装」（可能还有 ICP 提示）。
- **不要**：恢复 A/B 合同、审计督导、成本快照、BATCHES/考官/总线/`.pilot`（旧体系已归档，如需查历史见 `docs/archive/2026-11/`）。
