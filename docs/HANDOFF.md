# HANDOFF（换会话先读这个）

- **状态**（2026-11-16 09:4x，本轮收工）：**模式已固化**（单会话 + 本地循环）；HEAD＝origin/master（代码/发布提交 `44e9b60`，其后仅文档收口）；工作树干净；未推送 0；无进行中任务；新包 `build-44e9b60` 已装机（App 内版本 0.2 (44e9b60)）；手机竖屏、App 运行中、游戏在读档后的 24×40 地图（tile 16,8）上、地图页已渲染当前图。存档槽只读取过、未写。
- **最新发布**：Release `build-44e9b60…`（地图接入 M1：assets/maps 全量 345 个 ROM 地址 + map_links 2769 出口，MapData 懒加载；真机 `map.assets indexed=345`、0 fallback、地图页渲染正常；截图 `map-assets-newsession-20261116.jpg`）。
- **结构**：`native-emu/` = Android App（Kotlin + Compose + mGBA C/C++ 核心）；`pyplatform/` = Python 旧自动化（冻结）；数据 `games/pokemon_firered/{maps,maps_decomp,battles,dialogs,data/*}`（`maps_decomp` 425 张解包可走格+行为网格 3.2MB；`data/` 有 `moves.json`、`metatile_behaviors.json`、`encounters_leafgreen.json`；`tools/gen_maps_data.py` 生成/校验）；`tests/` = 33 个 Python 离线测试；入口 `run_tests.py`；`tools/` = `emu_probe.py` / `gen_moves_data.py` / `gen_maps_data.py` / `gen_map_assets.py`（ROM 反查地址→App assets + 连接表）。
- **上游参考（本机，不在仓库）**：`/root/refs/pokefirered`（pret/pokefirered 浅克隆，2026-11-16 拉取，~78MB，只读）：查窗口模板 / ListMenu 行高与滚动 / `BagStruct`·`PartyMenu` 字段 / 战斗与地图逻辑用；**它是汉化改版的基础，地址、文本、数据表都可能偏移，坐标与内存一律以真机标定为准**；不把其代码/资源拷进本仓库（许可证与资源版权单独确认）。
- **构建/验证**：Kotlin 单测本机可跑（aapt2 走 qemu wrapper，命令见 `AGENTS.md`）；**APK/NDK 必须走 CI**（push 触发）；Python 旧层 `python3 run_tests.py`。
- **规则/文档**：`AGENTS.md`（循环 / 验证 / 红线 / 交接）｜`docs/TASKS.md`（任务/验收）｜`docs/ARCH.md`（架构/语言）｜`docs/CHANGELOG.md`（每发布 3–5 行）；历史 `docs/archive/2026-11/`（只读）。
- **已完成（本模式）**：工作流重设计、M4/M5 迁移、**名表 354**、**自动战斗**、**横屏纯画面 + WYSIWYG**（对话选项/战斗菜单/子菜单取消；复核 3 轮通过）、**横屏战斗背包/队伍子菜单点选**（翻口袋/道具行+取消行/滚动箭头/底部条按图标态区分/队伍大框+5 行/取消按钮；真机日志+截图通过）、**地图接入 M1**（解包数据→全量 assets + 连接表；真机 0 fallback）。
- **未做**：地图 M2（跨图寻路 UI 入口、门/楼梯坐标口径、行为/遭遇展示、struct-multi 地址消歧）；横屏后续（非标准 3+ 选项框、镜头贴边锚点）；联机调研；结构债（WYSIWYG 3 条）；已记：有效队伍换人、双打布局未真机验。
- **图片证据**：`/sdcard/Download/DSH-Go/wysiwyg-*.jpg`（8 张：横屏纯画面 / 面板 / 战斗菜单 / 背包 / 点地图走位 / 竖屏前后）+ `wysiwyg2-*.jpg`（bag-close / bag-item / party / landscape-moves / landscape-bag）。
- **内存地址（实测）**：`sMenu`=0x0203ADE4、`gWindows`=0x020204B4、`BATTLE_MENU_FLAG(E83)`=0x02023E83（E83!=0 才是真战斗菜单，==0 是战斗内是/否选项框）；背包 `gBagMenuState`=0x0203ACFC（pocket=+6=0x0203AD02、各口袋光标=0x0203AD04+2*pocket）、队伍 slotId=0x0203B0A9（7=取消）。
- **接手 5 分钟**：① `git status --short` 期望空、`git rev-list --count origin/master..HEAD` 期望 0；② 读 `docs/TASKS.md`（todo 列表）→ 用户点名任务后按 `AGENTS.md` 循环开工；③ 快速验证 `python3 run_tests.py`（33/33）+ Kotlin 单测（命令见 `AGENTS.md`）。
- **环境**：手机 Android proot Ubuntu；真机自测用手机工具（OTA / 点击 / 截图）；证据 `/sdcard/Download/DSH-Go/`；日志 `/sdcard/Download/emu_native.log`；游戏内存/按键可用 localhost TCP 桥（`read/press/frame`，端口 55401）做标定取证。
- **真机点击限制（重要）**：本会话 `tap_xy` 坐标手势被安全策略拒绝（报「没有已通过本次过滤的截图」），真机坐标点击只能 `handoff` 让用户点；元素点击（`tap id`）正常。`android_shell`（需 Shizuku/自连 ADB）可跑 `input tap`，但本会话未开启。
- **OTA 兜底安装（GitHub CDN 抖动时；2026-11-15 再次实测 App 内下载 0% 失败，用此兜底装 e3be008）**：proot 里 `cd /sdcard/Download/DSH-Go && python3 -m http.server 8765 --bind 127.0.0.1` → 手机 Via 打开 `http://127.0.0.1:8765/<apk>` → 下载后 `handoff` 让用户点「安装 / 继续安装」（可能还有 ICP 提示）。
- **不要**：恢复 A/B 合同、审计督导、成本快照、BATCHES/考官/总线/`.pilot`（旧体系已归档，如需查历史见 `docs/archive/2026-11/`）。
