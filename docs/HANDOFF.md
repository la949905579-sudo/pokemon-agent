# 交接文档（2026-11-12 05:25）

> 给下一个会话：先读本文件 + `README.md` + `PROJECT_PLAN.md` + `NATIVE_EMU_TODO.md`。

## 一、项目是什么

两个部分，一条 TCP 桥连接：

1. **NativeEmu**（`native-emu/`）：自研 Android 双屏 GBA 模拟器（mGBA 内核 + Kotlin/Compose + NDK），上屏游戏，下屏控制台，TCP 桥 `127.0.0.1:55401`
2. **Pokemon 自动化**（根目录 `*.py`）：火红中文版的读内存/决策/自动化，通过 `EMU_BACKEND=native` 切到 NativeEmu（否则走 RetroArch UDP）

仓库：`https://github.com/la949905579-sudo/pokemon-agent`（master）

## 二、当前进度

- **P0 平台**：完成（双屏/渲染/60fps/存档/多指按键/后台保活/固定签名/OTA）
- **P1 插件化**：完成（`framework/` + `games/pokemon_firered/` + `run_game.py`，28 项 Python 测试）
- **B 方案（Kotlin 重写）**：数据层 + 决策层 + UI 集成完成（`native-emu/.../game/`），CI 含 Kotlin 单测
- **下屏**：左侧内容 + 右侧竖排 Tab（地图/队伍/背包/名字/图鉴/存档/设置/按键）

## 二·五、构建与发布现状（2026-11-12 05:20 实测，必读）

- HEAD = `81c2f5c`；**CI 自 03:51 起没成功过**：7 次构建失败 + 2 次 startup_failure，
  另有一次排队 25 分钟没跑起来（`22f6ded`）。最后一次失败 05:05。
- 已修（2026-11-12 05:35）：`MainActivity.kt` 补上
  `androidx.compose.foundation.gestures.detectTapGestures` 的 import。
  推送后若 CI 还红，按日志 `e: file:///home/runner/…` 继续定位（可能不止一处）。
- **最新 Release `build-d0bd1c3` 是旧包**：APK 11,486,833 B，与 11-11 19:21 的成功构建完全一致；
  标签与内容不符。CI 绿之前**不要走 App 内 OTA**。
- 反复用空提交触发构建是无效的（`87c3323`、`22f6ded`），必须改代码。
- Python 测试：`python3 run_tests.py` → **28/28 通过**（05:07 实测）。
- 工作区干净；`map_cache.txt` 等运行缓存已移出版本库（`.gitignore`）。

## 三、下一批待办（已和用户确认过方案）

1. **存档卡槽**：3 槽，显示保存时间 + 存档/读档/删除（`state1-3.sav`）
2. **队伍详情字段**：属性 / 4 招式 + PP / 经验
3. **行走路径提示**：点地图先画路线 + 步数 + 「开始走」
4. **招式点击施放**：读 `MOVE_CURSOR`(0x02023FFC) → 方向键序列 → 回读确认（风险最高，需防护）

详见 `NATIVE_EMU_TODO.md`。

## 四、关键命令

```bash
# Python 测试（28 项）
python3 run_tests.py

# 状态推送（下屏数据）
bash /root/workspace/start_push.sh     # 启动常驻（setsid）
bash /root/workspace/start_push.sh stop

# 构建：推送即触发 CI（.github/workflows/build-native-emu.yml）
git push

# 下载 + 发布（会检查构建是否成功）
GITHUB_TOKEN=xxx python3 publish_release.py build-<sha>
```

## 五、环境与坑

- 手机：Android 16，arm64；本机无法完整编译（NDK 是 x86_64），**一律用 GitHub Actions 构建**
- 构建产物下载到 `/sdcard/Download/DSH-Go/app-debug.apk`
- 签名固定：`native-emu/app/keystore.jks`（口令 emu123456）→ 可覆盖安装
- **mGBA 集成坑**（详见 `native-emu/README.md`）：emµ 与 libmgba 编译宏必须一致、初始化顺序、skipBios、RGB565、存档 API、mCoreFind 竞态
- 下屏数据：**本地 Kotlin GameState 优先**，Python 推送兜底；地图（minimap）仍靠推送
- 用户偏好：中文、简洁；**每次构建前先列改动清单确认**（commit message 即 OTA 更新日志）；构建放后台别阻塞

## 六、GitHub token

当前 token 的明文不写进仓库（GitHub Push Protection 会阻止）。需要时向物主索取。
旧 token 已全部删除；新 token 有 repo + workflow 权限，2026-12-11 到期。
到期后重新生成：设置 → Developer settings → Personal access tokens (classic)。

## 七、注意

- `BATTLE_FLAG` 战斗中可能短暂为 0（动画/结算），已用 `battle_anim` + 4 秒滞回处理
- 点击地图前往会**真按方向键**（180ms/步），误触会移动角色
- 用户手机开着 VPN 时 GitHub API 可能连不上

## 八、文档地图（按阅读顺序）

| 文档 | 作用 | 什么时候读 |
|---|---|---|
| `README.md` | 项目总览 + 模块速查 | 第一次接手 |
| `docs/PROJECT_PLAN.md` | 平台/插件分层与路线图 | 想知道「为什么这么设计」 |
| `docs/TOOLS.md` | 每个 Python 模块 + NativeEmu 桥/构建/日志 | 动手写代码前 |
| `docs/NATIVE_EMU_TODO.md` | 模拟器**唯一**的进度与待办真源 | 每次开工先看 |
| `docs/NATIVE_EMU.md` | 模拟器立项计划（含历史验收标准） | 想回看设计决策 |
| `docs/NOTES.md` | 内存地址与实测结论（游戏侧） | 改自动化逻辑时 |
| `docs/ARCHITECTURE.md` | Python 分层与 import 关系 | 重构前 |
| `docs/CHANGELOG.md` | 行为/接口变更记录 | 发版、写 OTA 说明 |
| `docs/FAQ.md` | 用户侧常见问题（安装/黑屏/OTA） | 处理实机问题 |
| `docs/WORKPLAN.md` | 11-10 的工作计划（部分已被 P1 取代） | 仅追溯历史 |

**冲突时以代码为准**：`CHANGELOG` 记行为、`NATIVE_EMU_TODO` 记进度，两边不一致先看 `git log`。
