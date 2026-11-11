# 文件索引

> 由 `tools/gen_files_index.py` 生成，**不要手改**。新增/删除文件后重跑：
> `python3 tools/gen_files_index.py`；CI 或交接前用 `--check` 确认没有未描述的文件。


## 其他

| 文件 | 用途 | 状态 |
|---|---|---|
| `web/index.html` | 网页入口（状态面板，用途待确认） | 保留 |

## 内核

| 文件 | 用途 | 状态 |
|---|---|---|
| `native-emu/app/src/main/cpp/emu_core.cpp` | mGBA 生命周期：init/runFrame/save/load/内存 | 保留 |
| `native-emu/app/src/main/cpp/emu_core.h` | 内核 C 接口声明（emu_core.cpp 的头文件） | 保留 |
| `native-emu/app/src/main/cpp/emu_jni.cpp` | JNI 胶水 + RGB565→ARGB 像素转换 | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/EmuCore.kt` | JNI 声明与按键位掩码 | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/EmuService.kt` | 前台服务 + WakeLock 保活 | 保留 |

## 平台

| 文件 | 用途 | 状态 |
|---|---|---|
| `action.py` | 只负责按方向键/确认键的执行层，不含决策 | 保留 |
| `addresses.py` | 火红内存地址表（唯一真源，别在别处硬编码地址） | 保留 |
| `ai_agent.py` | 外部 AI 接入口（实验） | 保留 |
| `api_server.py` | HTTP 指令接口：/api/intent 等 | 保留 |
| `auto_battle.py` | 战斗门面：拆分为 switch / watchdog / battle_loop，这里统一导出。 | 保留 |
| `battle_loop.py` | 战斗主循环：读状态→决策→按键→回写日志 | 保留 |
| `bdata.py` | 战斗数据解码（双方精灵、招式、血量） | 保留 |
| `bridge.py` | 注册制中间层（未接入主链路） | 保留 |
| `changelog.py` | 从 git log 生成 CHANGELOG 草稿（按 commit 前缀归类）。 | 保留 |
| `decision.py` | 决策层门面：按场景拆分到子模块，这里统一导出（保持旧接口兼容）。 | 保留 |
| `decision_battle.py` | 战斗决策模块（纯逻辑）。 | 保留 |
| `decision_map.py` | 地图决策模块（纯逻辑）。 | 保留 |
| `emu_bridge.py` | NativeEmu TCP 桥客户端（rd/wr/press/frame） | 保留 |
| `encounter.py` | 遇敌：判断在草地、走回最近草地、九宫格朝草移动。 | 保留 |
| `farm.py` | 自动练级：遇敌 -> battle_loop -> 记录，达到目标等级/场数/时间就停。 | 保留 |
| `framework/__init__.py` | 平台框架：与具体游戏无关的通用能力（插件接口、主循环、桥适配）。 | 保留 |
| `framework/game_plugin.py` | 游戏插件接口（契约）。 | 保留 |
| `framework/loader.py` | 按 game_id 加载游戏插件（约定：games/<id>/plugin.py 里叫 Plugin 或唯一插件类）。 | 保留 |
| `framework/runner.py` | 通用主循环：读状态 → 决策 → 执行 → 推送状态。 | 保留 |
| `games/__init__.py` | 游戏插件集合：每个游戏一个子目录。 | 保留 |
| `games/_template/plugin.py` | 新游戏插件模板：复制这个目录，改 game_id / 内存读取 / 决策。 | 保留 |
| `games/pokemon_firered/plugin.py` | 口袋妖怪 火红 插件：包装现有 info/state 模块，不改动它们。 | 保留 |
| `handlers.py` | 注册制中间层（未接入主链路） | 保留 |
| `info.py` | 信息获取层：只读内存，回答「现在是什么场景」。 | 保留 |
| `intent.py` | 指令层（intent）：AI/用户下「目标」，决策层决定「怎么做」。 | 保留 |
| `intent_demo.py` | 实机演示：遇敌后注入指令，观察决策变化（默认 3 回合）。 | 保留 |
| `learn.py` | 学招处理：升级学招/「忘记哪个招式」界面（属于决策，不属于执行层）。 | 保留 |
| `legacy/train_probe.py` | 练级 + 出招采样：记录每回合「决策 idx / 实际招式 / PP 变化 / 敌方出招」。 | 保留 |
| `log.py` | 统一日志：JSONL 单一流（机器）+ 控制台文本（人）。 | 保留 |
| `logq.py` | 查询统一日志 logs/run-*.jsonl。 | 保留 |
| `map_coords.py` | 全局地图坐标系：把每张地图的局部坐标（0..w, 0..h）映射到统一坐标系。 | 保留 |
| `map_links.py` | 地图间连接表：记录每张地图的出口坐标和通向哪里。 | 保留 |
| `map_links_vis.py` | 把 map_links.json 画成地图连接图（节点 + 箭头）。 | 保留 |
| `map_route.py` | 跨图寻路：在连接表上做 A*，输出逐段路线并执行。 | 保留 |
| `mapdraw.py` | 把当前地图画成 PNG：碰撞/草/NPC/玩家/规划路径，带中文图例和网格线。只读。 | 保留 |
| `memory.py` | 内存读写的统一入口（按 EMU_BACKEND 分派 RetroArch / NativeEmu） | 保留 |
| `move_probe.py` | 战斗出招采集器（只读）。 | 保留 |
| `native-emu/tools/bridge_client.py` | NativeEmu TCP 桥的 Python 客户端（默认 127.0.0.1:55401）。 | 保留 |
| `native-emu/tools/patch_mgba.py` | CI 用：给 mGBA 的 _GBACoreInit 插调试日志（崩在 core->init 时定位用）。 | 保留 |
| `nav.py` | 自适应导航：BFS + 卡住就把那一格当障碍，重新规划。 | 保留 |
| `pathfind.py` | 快速寻路：BFS 出路径后按同方向段长按连续走。 | 保留 |
| `probe.py` | 战斗回合观测：订阅 battle_loop(on_round=...) 写 JSONL，并汇总一致性。 | 保留 |
| `probe_enemy.py` | 定向采集：连续使用非攻击招（聚气），逼敌方出招，抓 D4C 序列与敌方招式表。 | 保留 |
| `push_status.py` | 把状态推给模拟器下屏（:55401 status 命令） | 保留 |
| `ra.py` | RetroArch UDP 通道（读内存 :55355、按键 :55400） | 保留 |
| `run_game.py` | 插件化入口：EMU_BACKEND=native python3 run_game.py <game_id> | 保留 |
| `start_push.sh` | 后台常驻的状态推送脚本（setsid，支持 stop） | 保留 |
| `state.py` | 实时读游戏状态：角色坐标 + 队伍。 | 保留 |
| `state_server.py` | 本地状态服务：给网页「下屏」提供数据与动作接口。 | 保留 |
| `switch.py` | 换人模块：战斗内部队伍顺序 + 换人动作。 | 保留 |
| `terrain.py` | 地图通行性：定位地图结构、读取地块、输出九宫格。 | 保留 |
| `tools/gen_files_index.py` | 生成 docs/FILES.md：仓库里每个被跟踪文件的用途索引。 | 保留 |
| `track_route.py` | 后台记录用户操作时的坐标轨迹（带地图 ID，能分辨换图）。 | 保留 |
| `train.py` | 练级 + 回合观测：走 battle_loop 的 on_round 回调，不再 monkeypatch。 | 保留 |
| `watchdog.py` | 健壮性：看门狗 + 等回合完成。 | 保留 |

## 插件

| 文件 | 用途 | 状态 |
|---|---|---|
| `games/_template/__init__.py` | 新游戏插件模板包 | 保留 |
| `games/pokemon_firered/__init__.py` | 火红插件包入口 | 保留 |

## 数据

| 文件 | 用途 | 状态 |
|---|---|---|
| `battles/battle1.json` | 数据/样例文件 | 保留 |
| `battles/battle1_start.bin` | 数据/样例文件 | 保留 |
| `battles/battle2.json` | 数据/样例文件 | 保留 |
| `battles/battle2_start.bin` | 数据/样例文件 | 保留 |
| `dialogs/nurse_welcome.bin` | 数据/样例文件 | 保留 |
| `map_links.json` | 数据/样例文件 | 保留 |
| `maps/map_82d5844.json` | 数据/样例文件 | 保留 |
| `maps/map_82df30c.json` | 数据/样例文件 | 保留 |
| `maps/map_82e0614.json` | 数据/样例文件 | 保留 |
| `maps/map_82e833c.json` | 数据/样例文件 | 保留 |
| `maps/map_82e9260.json` | 数据/样例文件 | 保留 |
| `maps/map_82ec3d4.json` | 数据/样例文件 | 保留 |
| `maps/map_83192f0.json` | 数据/样例文件 | 保留 |
| `maps/map_831a3a0.json` | 数据/样例文件 | 保留 |
| `maps/map_831e8d8.json` | 数据/样例文件 | 保留 |
| `maps/map_831eb98.json` | 数据/样例文件 | 保留 |
| `maps/map_8320d18.json` | 数据/样例文件 | 保留 |
| `maps/override_82de3e8.json` | 数据/样例文件 | 保留 |
| `maps/override_82fc730.json` | 数据/样例文件 | 保留 |

## 文档

| 文件 | 用途 | 状态 |
|---|---|---|
| `AGENTS.md` | 工作守则 | 保留 |
| `README.md` | 项目总览 | 保留 |
| `docs/ARCHITECTURE.md` | 架构与执行流程（2026-11-09 23:30 快照） | 保留 |
| `docs/CHANGELOG.md` | CHANGELOG | 保留 |
| `docs/FAQ.md` | FAQ · 常见问题 | 保留 |
| `docs/HANDOFF.md` | 交接文档（2026-11-12 05:25） | 保留 |
| `docs/INCIDENTS.md` | 事故复盘库（现象/根因/固化改动） | 保留 |
| `docs/NATIVE_EMU.md` | 原生双屏 GBA 模拟器 · 项目规划（NATIVE_EMU） | 保留 |
| `docs/NATIVE_EMU_TODO.md` | NativeEmu 待办 | 保留 |
| `docs/NOTES.md` | 叶绿内存（实测） | 保留 |
| `docs/OBSERVABILITY.md` | 可观测性规范（OBSERVABILITY） | 保留 |
| `docs/PORTING.md` | 移植指南：换一个宝可梦游戏怎么改 | 保留 |
| `docs/PROJECT_PLAN.md` | 项目规划：从「一个游戏的自动化」到「一个模拟器平台 + 多个游戏插件」 | 保留 |
| `docs/RETROSPECTIVE.md` | 复盘：2026-11-09 ~ 11-10 | 保留 |
| `docs/STRUCTURE.md` | 项目结构规范（STRUCTURE） | 保留 |
| `docs/TOOLS.md` | 工具使用手册（TOOLS） | 保留 |
| `docs/WORKPLAN.md` | 工作计划（2026-11-10 起） | 保留 |
| `docs/roles/auditor.md` | 督导（auditor）提示词 | 保留 |
| `native-emu/README.md` | NativeEmu（Android 工程） | 保留 |

## 构建

| 文件 | 用途 | 状态 |
|---|---|---|
| `.github/workflows/build-native-emu.yml` | CI / 工具配置 | 保留 |
| `.gitignore` | 忽略规则：缓存、构建产物、运行日志 | 保留 |
| `native-emu/.gitignore` | 忽略 third_party 与构建产物 | 保留 |
| `native-emu/app/build.gradle.kts` | Android 模块构建：固定签名 + BuildConfig(GIT_SHA/BUILD_TIME) | 保留 |
| `native-emu/app/keystore.jks` | 固定签名私钥库（⚠ 已在公开仓库暴露，见 HANDOFF 安全债） | 保留 |
| `native-emu/app/src/main/AndroidManifest.xml` | 权限（存储/前台服务/安装包）与组件声明 | 保留 |
| `native-emu/app/src/main/cpp/CMakeLists.txt` | mGBA 子目录 + 编译宏（必须与 libmgba 完全一致） | 保留 |
| `native-emu/app/src/main/res/xml/file_paths.xml` | FileProvider 路径（OTA 安装 APK 用） | 保留 |
| `native-emu/build.gradle.kts` | Gradle 根构建脚本 | 保留 |
| `native-emu/gradle.properties` | Gradle 参数（JVM 内存等） | 保留 |
| `native-emu/settings.gradle.kts` | 模块声明（:app） | 保留 |
| `native-emu/tools/aapt2-wrapper` | aapt2 包装脚本（arm64 主机上的 x86_64 工具链绕行） | 保留 |
| `native-emu/tools/aapt2_wrapper.c` | aapt2 包装器源码 | 保留 |
| `native-emu/tools/build.sh` | 本地构建脚本（本机必然失败，仅作记录） | 保留 |
| `native-emu/tools/cmake_wrapper.c` | CMake 包装器源码 | 保留 |
| `native-emu/tools/setup-sdk.sh` | 安装 Android SDK / NDK / Gradle | 保留 |
| `publish_release.py` | 把 CI 产物发布到 GitHub Release（OTA 更新源） | 保留 |

## 桥

| 文件 | 用途 | 状态 |
|---|---|---|
| `native-emu/app/src/main/java/com/dsh/emu/BridgeServer.kt` | TCP :55401 服务端（read/write/press/frame/status） | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/Updater.kt` | GitHub Releases OTA：检查、下载、校验、拉起安装器 | 保留 |

## 残留

| 文件 | 用途 | 状态 |
|---|---|---|
| `battle_collect.log` | 调试日志/转储，建议清理 | 待清理 |
| `battle_sample.log` | 调试日志/转储，建议清理 | 待清理 |
| `faint2.txt` | 调试日志/转储，建议清理 | 待清理 |
| `faint3.txt` | 调试日志/转储，建议清理 | 待清理 |
| `faint4.txt` | 调试日志/转储，建议清理 | 待清理 |
| `faint_dump.txt` | 调试日志/转储，建议清理 | 待清理 |
| `flag_sample.log` | 调试日志/转储，建议清理 | 待清理 |
| `mapcap.log` | 调试日志/转储，建议清理 | 待清理 |
| `mapcap2.log` | 调试日志/转储，建议清理 | 待清理 |
| `route_log.txt` | 调试日志/转储，建议清理 | 待清理 |
| `sample.log` | 调试日志/转储，建议清理 | 待清理 |

## 测试

| 文件 | 用途 | 状态 |
|---|---|---|
| `run_tests.py` | 一键跑全部离线测试（按 test_*.py 文件计数） | 保留 |
| `test_action.py` | 离线测试：action | 保留 |
| `test_avoid_grass.py` | 离线测试：avoid_grass | 保留 |
| `test_battle_loop.py` | 离线测试：battle_loop | 保留 |
| `test_bridge.py` | 离线测试：bridge | 保留 |
| `test_cursor.py` | 离线测试：cursor | 保留 |
| `test_decision.py` | 离线测试：decision | 保留 |
| `test_emu_bridge.py` | 离线测试：emu_bridge | 保留 |
| `test_extension.py` | 离线测试：extension | 保留 |
| `test_game_plugin.py` | 离线测试：game_plugin | 保留 |
| `test_guard.py` | 离线测试：guard | 保留 |
| `test_info.py` | 离线测试：info | 保留 |
| `test_intent.py` | 离线测试：intent | 保留 |
| `test_lead.py` | 离线测试：lead | 保留 |
| `test_learn.py` | 离线测试：learn | 保留 |
| `test_log.py` | 离线测试：log | 保留 |
| `test_loop.py` | 离线测试：loop | 保留 |
| `test_map_route.py` | 离线测试：map_route | 保留 |
| `test_moves.py` | 离线测试：moves | 保留 |
| `test_pathfind.py` | 离线测试：pathfind | 保留 |
| `test_pokemon_plugin.py` | 离线测试：pokemon_plugin | 保留 |
| `test_probe.py` | 离线测试：probe | 保留 |
| `test_runlen.py` | 离线测试：runlen | 保留 |
| `test_runner.py` | 离线测试：runner | 保留 |
| `test_switch.py` | 离线测试：switch | 保留 |
| `test_switch2.py` | 离线测试：switch2 | 保留 |
| `test_travel.py` | 离线测试：travel | 保留 |
| `test_turn.py` | 离线测试：turn | 保留 |
| `test_turns.py` | 离线测试：turns | 保留 |

## 游戏

| 文件 | 用途 | 状态 |
|---|---|---|
| `native-emu/app/src/main/java/com/dsh/emu/game/Addresses.kt` | Kotlin 侧地址表（对应 addresses.py） | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/game/BattleDecider.kt` | 战斗决策（选招/换人评分） | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/game/GameData.kt` | 静态数据：属性表、招式表 | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/game/GameState.kt` | 读内存解码场景/坐标/队伍/敌方信息（Kotlin 版） | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/game/MapWalker.kt` | 同图 BFS 寻路，输出方向序列 | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/game/Memo.kt` | 内存读取的小封装（u8/u16/块读） | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/game/PartyCrypto.kt` | 队伍数据解密（PortablePokemon） | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/game/Species.kt` | 关东 1-151 中文名表 | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/game/SwitchDecider.kt` | 换人决策 | 保留 |
| `native-emu/app/src/test/java/com/dsh/emu/game/BattleDeciderTest.kt` | class BattleDeciderTest | 保留 |
| `native-emu/app/src/test/java/com/dsh/emu/game/GameStateTest.kt` | 离线单测：用内存镜像替换 JNI 读取。 | 保留 |
| `native-emu/app/src/test/java/com/dsh/emu/game/SwitchDeciderTest.kt` | class SwitchDeciderTest | 保留 |

## 界面

| 文件 | 用途 | 状态 |
|---|---|---|
| `native-emu/app/src/main/java/com/dsh/emu/MainActivity.kt` | Compose 主界面：双屏、Tab、按键页、小地图（已超 500 行，待拆） | 保留 |
| `native-emu/app/src/main/java/com/dsh/emu/UiState.kt` | 下屏状态模型（Python 推送的 JSON 落到这里） | 保留 |

> 共 174 个文件（不含 `native-emu/third_party/` 第三方源码）。
