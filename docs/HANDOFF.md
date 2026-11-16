# HANDOFF（换会话先读这个）

- **状态**（2026-11-16 10:3x，本轮收工、准备交接）：模式已固化（单会话 + 本地循环）；HEAD＝origin/master=`89b328d`（代码/发布提交 `44e9b60`，其后仅文档）；工作树干净、未推送 0；无进行中任务、无后台任务；**Kotlin 172/172、Python 33/33（交接前刚复跑绿）**。
- **最新发布**：Release `build-44e9b60…` 已装机（App 内版本 0.2 (44e9b60)）；内容 = 地图 M1（`assets/maps` 345 个 ROM 地址 + `map_links.json` 2769 出口、`MapData` 懒加载）。App 内 OTA 仍 0% 失败，装包走 Via + 本机 HTTP 兜底（见下）。
- **手机状态**：用户当前在 DSH Go；NativeEmu 后台运行（游戏为读档态、未写盘）；存档槽 1/2/3 本轮只读未写。
- **结构**：`native-emu/` = Android App（Kotlin + Compose + mGBA 核心）；`pyplatform/` = Python 旧层（冻结）；数据 `games/pokemon_firered/{maps,maps_decomp,battles,dialogs,data/*}`（`maps_decomp` 425 张=解包可走格+行为网格 3.2MB；`data/` 有 moves / metatile_behaviors / encounters_leafgreen）；App 资产 `native-emu/app/src/main/assets/maps`（345 + `map_links.json`）；Python 测试 33 个；工具 `tools/{emu_probe,gen_moves_data,gen_maps_data,gen_map_assets}.py`。
- **上游参考（本机，不在仓库）**：`/root/refs/pokefirered`（pret/pokefirered 浅克隆 ~78MB，只读）：查窗口模板/ListMenu/结构体/战斗与地图逻辑；**它是汉化改版基础，地址/文本/数据表可能偏移，坐标与内存一律以真机标定为准**；不把其代码/资源拷进仓库。
- **地图关键内存事实**：`gMapHeader` 结构在 `0x02036DFC`（首字段 = 当前 mapLayout 指针）；layout+0/+4 = 宽高、+8 = border 指针、+0xC = blockdata ROM 地址（App 资产 key，`map_<addr>.json`；tiles 存碰撞位 1=挡）。
- **已知内存地址**：`sMenu`=0x0203ADE4、`gWindows`=0x020204B4、`E83`=0x02023E83（!=0 真战斗菜单、==0 战斗内是/否框）；背包 `gBagMenuState`=0x0203ACFC（pocket=+6、可视行=+8+2p、滚动偏移=+14+2p）、队伍 slotId=0x0203B0A9（7=取消）。
- **已完成**：工作流重设计、M4/M5 迁移、名表 354、自动战斗、横屏纯画面 + WYSIWYG（对话选项/战斗菜单/子菜单取消）、横屏战斗背包/队伍子菜单点选（含 >6 件道具滚动修复）、**离线地图数据**（425 张碰撞位+行为网格、行为名表、叶绿遭遇表；真机交叉校验 11/11 diff=0）、**地图 M1**（345 资产 + 2769 出口，真机 `map.assets indexed=345`、新会话 0 fallback）。
- **未做（todo 1 = 地图 M2，用户 2026-11-16 拍板合并、暂不开工）**：① 水面/地形识别接入（assets 加 behaviors，步行时水面/瀑布/深水不可走，地图页可标）② 跨图寻路 UI 入口（`CrossMapWalker` 未接线）③ 门/楼梯坐标口径校准（解包 warp 与实测差 1 格）④ 遭遇展示（`encounters_leafgreen.json`）⑤ 27 个 struct-multi 布局地址消歧。其余 todo：非标准 3+ 选项框、镜头贴边锚点、联机调研、结构债（WYSIWYG 3 条）。
- **图片证据**：`/sdcard/Download/DSH-Go/`：`wysiwyg-*.jpg`（横屏基础）、`wysiwyg2-*.jpg`（背包/队伍子菜单、滚动）、`map-assets-newsession-20261116.jpg`（新包地图页、0 fallback）。
- **接手 5 分钟**：① `git status --short` 空、`git rev-list --count origin/master..HEAD`=0；② 读 `AGENTS.md` + `docs/TASKS.md`；③ `python3 run_tests.py`（33/33）；④ Kotlin：先 `ln -sfn /root/workspace/native-emu/tools/aapt2-wrapper /root/android-emu-local/aapt2`，再 `cd native-emu && /opt/gradle-8.9/bin/gradle :app:testDebugUnitTest --no-daemon --console=plain -Pandroid.aapt2FromMavenOverride=/root/android-emu-local/aapt2`（172/172）。
- **环境**：Android proot Ubuntu（无沙箱后端，bash 直接跑）；日志 `/sdcard/Download/emu_native.log`；TCP 桥 `127.0.0.1:55401`（read/press/frame）；**APK/NDK 只能 CI**（push 出 Release），本地只跑单测。
- **真机限制（重要）**：`tap_xy` 坐标手势被安全策略拒绝 → 横屏画面/系统页点击用 `handoff` 让用户点；元素 `tap id` 正常；`android_shell`（Shizuku）未开启。
- **OTA 兜底安装（GitHub CDN 抖动时）**：proot `cd /sdcard/Download/DSH-Go && python3 -m http.server 8765 --bind 127.0.0.1` → 手机 Via 打开 `http://127.0.0.1:8765/<apk>` → 下载后 handoff 让用户点「安装 / 继续安装 / 仍然安装」。
- **不要**：恢复 A/B 合同/审计/台账（归档 `docs/archive/2026-11/` 只读）；不碰 keystore/口令；不伪造测试/构建/真机结论；不 `--no-verify`、不 force push、不 amend 已推提交。
