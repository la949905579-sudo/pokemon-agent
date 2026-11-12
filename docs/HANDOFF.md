# 交接文档（2026-11-12 19:20 整改后）

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
- **地图 Tab**：两步式——点格子只预览（黄线/终点/N 步），「开始走」才移动；常驻「当前地图」页只读（批次 D）

## 二·五、构建与发布现状（2026-11-12 19:50 实测）

- **HEAD 以 `git log -1` 为准**（本文件之后仍有 docs/tools 提交，写死 hash 会立刻过期）。
  最后一次**代码**提交是 `ea576e9`（批次 D 行走预览）；Python 侧最后代码提交 `81cfb2b`
  （循环依赖修复），都在最新构建覆盖内（见下）。
  Python 测试 **29/29**；Kotlin 单测 **70/70**（考官本机实跑 + CI 构建含单测；见 `docs/METRICS.md`）。
- **最新构建 = 推送 tip `401aeaa`（批次 D）**：CI 成功，Release tag
  `build-401aeaa5bc39…`（2026-11-12 20:33 发布）；覆盖 `cbbd1f9`（C 遗留）、
  `ea576e9`（行走预览）与 `401aeaa`（文档）。
  此前：`build-ccc9bff…`（20:14，批次 C）、`build-930fe29…`（20:06，批次 B）、
  `build-8082f89…`（19:48，批次 A）、`build-2c237da…`（17:43，覆盖 `c13ee2e` /
  `9cfd5d0`（重置/退出）/ `2c237da`）。
- 当前 HEAD 已包含批次 A/B/C/D 的 `native-emu/**` 改动（`8082f89`、`fdbf448`、`2a0fbc7`、`ea576e9`），APK 由 CI 构建；之后再有 docs/tools/py 提交不影响构建。**判构建覆盖看 `docs/METRICS.md` 的 tag→提交映射，不要看「每个提交是否都有 tag」。**
- CI 触发条件：推送里**包含 `native-emu/**`** 才构建；按推送 tip 打 tag，因此一个 tag 可能
  覆盖多个提交（2026-11-12 首次审查的误判就出在这里，见 `docs/AUDIT_LOG.md`）。
- 历史失败（03:51–05:26）的两层原因已修掉，留作教训：
  1. `MainActivity.kt` 缺 `androidx.compose.foundation.gestures.detectTapGestures` 的 import
  2. `KeyPadArea` 里残留了一段重复的旧按键布局块，多出一个右花括号 → 528 行
     `Expecting a top level declaration`（插入新布局时没删旧块）
- Release 由 CI 自动发布：每次构建成功就发 `build-<sha>`；构建失败不会发（旧错包 `build-c7996e9` 已删）。
- 工作区干净；`map_cache.txt` 等运行缓存已移出版本库（`.gitignore`）。
- 教训：本机编不了 Kotlin，改完先做两件小事——grep import、数花括号（`python3 - <<` 小脚本），
  比反复推空提交省时间。

## 三、下一批待办（已和用户确认过方案）

1. **存档卡槽**：3 槽，显示保存时间 + 存档/读档/删除（`state1-3.sav`）
2. **队伍详情字段**：属性 / 4 招式 + PP / 经验
3. **行走路径提示**：点地图先画路线 + 步数 + 「开始走」
4. **招式点击施放**：读 `MOVE_CURSOR`(0x02023FFC) → 方向键序列 → 回读确认（风险最高，需防护）

详见 `NATIVE_EMU_TODO.md`。

## 四、关键命令（本机可跑 Kotlin 单测，APK 仍走 CI）

```bash
# Kotlin 单测（57 个，2026-11-12 19:19 本机实跑通过 44s；APK 仍走 CI）
ln -sfn /root/workspace/native-emu/tools/aapt2-wrapper /root/android-emu-local/aapt2
cd native-emu && PATH=/opt/gradle-8.9/bin:$PATH gradle :app:testDebugUnitTest --no-daemon \
  -Pandroid.aapt2FromMavenOverride=/root/android-emu-local/aapt2
```

## 四·一、关键命令

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
- 签名固定：`native-emu/app/keystore.jks`（**口令见 `native-emu/app/keystore-info.txt`，不进仓库**）
- **mGBA 集成坑**（详见 `native-emu/README.md`）：emµ 与 libmgba 编译宏必须一致、初始化顺序、skipBios、RGB565、存档 API、mCoreFind 竞态
- 下屏数据：**本地 Kotlin GameState 优先**，Python 推送兜底；地图（minimap）仍靠推送
- 用户偏好：中文、简洁；**每次构建前先列改动清单确认**（commit message 即 OTA 更新日志）；构建放后台别阻塞

## 六、推送凭据（已改为 SSH，2026-11-12）

- 远端已从 HTTPS 改为 `git@github.com:la949905579-sudo/pokemon-agent.git`。
- 手机上有 ed25519 密钥：`~/.ssh/github_ed25519`（私钥，600），公钥已加到 GitHub 账号，
  备注 `dsh-phone`；`~/.ssh/config` 里指定了 `IdentityFile`。
- **git push 不需要 token**：SSH 直接可用。账号里的旧 token `native-emu-push` 已于 2026-11-12 删除，
  现在没有任何经典 token。
- **发 Release 也不需要 token 了**：CI 构建成功后用仓库自带的 `GITHUB_TOKEN` 自动发
  `build-<sha>`（workflow 里 `permissions: contents: write`），失败不会发（不会出现旧包）。
- 换设备/换容器时：生成本机密钥 → 把公钥加到 GitHub → 改 remote 为 SSH，
  不要在聊天或文档里贴私钥。

## 六·五、签名与安全债（2026-11-12 已处置）

- **签名已轮换**：旧 `keystore.jks` 曾随公开仓库泄露，已从版本库移除并换新密钥。
- 新密钥只存在于两处：GitHub Actions secret（`ANDROID_KEYSTORE_B64` / `STORE_PASSWORD` /
  `KEY_PASSWORD`，别名 `emu`）和本机 `native-emu/app/`（`keystore.jks` + `keystore-info.txt`，
  权限 600、均已被 `.gitignore` 忽略）。**不进仓库。**
- ⚠️ 本机这两份文件是**唯一可恢复副本**：GitHub secret 只写不读。丢了就只能换密钥 → 再卸载重装一次。
  建议尽快把口令抄进密码管理器，并把 `keystore.jks` 另存一份。
- **旧包签名不兼容**：换新签名后（2026-11-12 起）出的包都是新签名，升级必须卸载重装（旧 `state1.sav` 会丢）。
  历史重写后旧 tag 名（如 `build-fab1535`）已不指向现存提交，不要再引用。
- 构建成功自动发 Release，不会再把失败构建的旧包发出去。
- 仍然成立的老规矩：凭据/私钥不进仓库、不进文档、不进聊天。

## 六·五·补：2026-11-12 重写过一次历史

- 原因：旧签名私钥 `native-emu/app/keystore.jks` 曾进过公开仓库，已用 `git filter-repo` 从**全部历史**中删除，
  并强推、删除了指向旧提交的 21 个 `build-*` tag。
- **副作用：所有 commit hash 变了**，文档里的 hash 已按映射批量替换；如果你在别处有克隆，必须重新拉。
- 重写前的完整备份：`/root/backups/pokemon-agent-preclean-1112-0944.bundle`（仅在手机上）。
- 未被清理的：GitHub 上旧的 Release 对象可能仍指向已删 tag（网页上还能点到），需要时可手动删。

## 六·六、GitHub 资源 CDN 在手机上不通

- 现象：App 内 OTA 下载卡 0%，Release 附件直连 `objects.githubusercontent.com` 经常 SSL EOF。
- 可用做法：走 API 端点 `repos/<o>/<r>/releases/assets/<id>`（带 `Accept: application/octet-stream`）
  下载，或用文件管理器/代理下好后手动安装。
- 已知未修：App 的 OTA 没有重试与错误码外显（日志已加，见 `ota.log`）。

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
| `docs/STRUCTURE.md` | 目标目录结构、依赖规则、迁移分期 | 动文件位置/拆分模块前 |
| `docs/OBSERVABILITY.md` | 日志格式与关键节点清单 | 加日志、排查问题时 |
| `docs/FILES.md` | **每个文件**的用途与状态（自动生成） | 找不到某个文件干嘛用 |
| `docs/TEAM.md` | 团队编制与重建步骤 | 新会话第一件事 |
| `docs/HANDOVER.md` | 交接阈值、前置检查、反模式 | 想换会话之前 |
| `docs/roles/*.md` | 四个角色的提示词（执行主管/工匠/考官/督导） | 重建团队时复制 |
| `docs/INCIDENTS.md` | 事故复盘：现象/根因/固化 | 出事后 24 小时内写一条 |
| `docs/AUDIT.md` | 第三方审查的触发条件与判据 | 到触发条件时 |
| `docs/METRICS.md` | 构建覆盖 + CI 首过率（脚本生成） | 判 T4 / 查某个提交有没有构建 |
| `docs/WORKPLAN.md` | 11-10 的工作计划（部分已被 P1 取代） | 仅追溯历史 |

**冲突时以代码为准**：`CHANGELOG` 记行为、`NATIVE_EMU_TODO` 记进度，两边不一致先看 `git log`。
