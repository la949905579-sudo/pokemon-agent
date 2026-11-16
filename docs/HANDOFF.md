# HANDOFF（换会话先读这个）

- **状态**（2026-11-16 12:0x，本轮收工）：模式已固化（单会话 + 本地循环）；HEAD=文档收口提交（代码提交 `5931f4a`）；工作树干净；无进行中任务；**Kotlin 186/186、Python 33/33**。
- **最新发布**：Release `build-5931f4a` 已装机（App 0.2 / versionCode 182）；内容 = 地图 M1（345 资产 + 2769 出口）+ **M2-A（地形行为着色 + 地图页遭遇）**。
- **手机状态**：用户当前在 DSH Go；NativeEmu 在**后台屏（不打扰模式）**运行，读档槽 3（地图 Route1 (10,10)，竖屏地图页）；槽 1/2 为战斗态存档（只读未写）；自动战斗关。
- **结构**：`native-emu/` = Android App（Kotlin + Compose + mGBA 核心）；`pyplatform/` = Python 旧层（冻结）；数据 `games/pokemon_firered/{maps,maps_decomp,battles,dialogs,data/*}`；App 资产 `native-emu/app/src/main/assets/maps`（345 图 + `map_links.json` + `encounters_leafgreen.json`）；工具 `tools/{emu_probe,gen_moves_data,gen_maps_data,gen_map_assets}.py`。
- **地图资产 schema（M2-A）**：`map_<addr>.json` = addr/w/h/tiles（碰撞位 0=可走、1=挡）/behaviors（2 hex/格，行为 id）/maps（地图 id 列表）；App 解析后 tiles =「步行可走」（水面按引擎 `sBehaviorSurfable` 表判挡），terrain 分类供着色；遭遇由 `Encounters.summary` 按 maps 查 `encounters_leafgreen.json`。
- **地图关键内存事实**：`gMapHeader` 在 `0x02036DFC`（首字段 = 当前 mapLayout 指针）；layout+0/+4 = 宽高、+8 = border 指针、+0xC = blockdata ROM 地址（App 资产 key，`map_<addr>.json`）；坐标 `X_ADDR=0x02036E48` / `Y_ADDR=0x02036E4A`（tile = 原始 -7）。
- **已知内存地址**：`sMenu`=0x0203ADE4、`gWindows`=0x020204B4、`E83`=0x02023E83（!=0 真战斗菜单）；背包 `gBagMenuState`=0x0203ACFC（pocket=+6、可视行=+8+2p、滚动=+14+2p）、队伍 slotId=0x0203B0A9（7=取消）。
- **已完成**：工作流重设计、M4/M5 迁移、名表 354、自动战斗、横屏纯画面 + WYSIWYG、横屏战斗背包/队伍子菜单点选、离线地图数据（425 张）、地图 M1（345 资产 + 2769 出口、0 fallback）、**地图 M2-A（行为地形 + 遭遇展示）**。
- **未做（todo 1 = 地图 M2 剩余）**：② 跨图寻路 UI 入口（`CrossMapWalker` 未接线）③ 门/楼梯坐标口径校准（解包 warp 与实测差 1 格）⑤ 27 个 struct-multi 布局地址消歧。其余 todo：非标准 3+ 选项框、镜头贴边锚点、联机调研、结构债（WYSIWYG 3 条）。
- **图片/日志证据**：`/sdcard/Download/DSH-Go/`：`map-m2a-20261116.jpg`（M2-A 地图页着色+遭遇）、`map-m2a-log-20261116.txt`、`map-assets-newsession-20261116.jpg`（M1）、`wysiwyg*.jpg`。
- **接手 5 分钟**：① `git status --short` 空、`git rev-list --count origin/master..HEAD`=0；② 读 `AGENTS.md` + `docs/TASKS.md`；③ `python3 run_tests.py`（33/33）；④ Kotlin：`ln -sfn /root/workspace/native-emu/tools/aapt2-wrapper /root/android-emu-local/aapt2` 后 `cd native-emu && /opt/gradle-8.9/bin/gradle :app:testDebugUnitTest --no-daemon --console=plain -Pandroid.aapt2FromMavenOverride=/root/android-emu-local/aapt2`（186/186）。
- **环境**：Android proot Ubuntu（无沙箱后端，bash 直接跑）；APK/NDK 只能 CI（push `native-emu/**` → Release `build-<sha>`）；本地只跑 Kotlin 单测。
- **真机自测（更新）**：模拟器测试用**免打扰模式**（`open {background:true}` 开在后台屏，不切主屏）；`android_shell` 已可用（Shizuku、uid shell，**每条命令原生授权、不能免**）；TCP 桥 `127.0.0.1:55401` 从 proot 可连（read/press/frame）；日志 `/sdcard/Download/emu_native.log`；`tap_xy` 坐标手势仍被安全策略拒绝 → 画布/系统页用 handoff 让用户点，元素 tap id 正常；装包：CI 包落到 /sdcard 后**需用户手动安装**（`pm install` 被 shell 工具拒绝 → handoff）。
- **不要**：恢复 A/B 合同/审计/台账（归档 `docs/archive/2026-11/` 只读）；不碰 keystore/口令；不伪造测试/构建/真机结论；不 `--no-verify`、不 force push、不 amend 已推提交。
