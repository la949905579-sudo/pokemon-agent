# NativeEmu 待办

> 更新：2026-11-12 05:20（与 `git log` / `CHANGELOG v2026.11.12-1` 对齐）
> 状态判断以代码为准：勾选过的项都在 `native-emu/` 里有实现。

## 当前阻塞（2026-11-12 05:35 已全部解除）

- [x] CI 编译失败：缺 `detectTapGestures` import + `KeyPadArea` 残留重复布局块（多一个 `}`）
- [x] Release 旧包：已删 `build-c7996e9`，新发 `build-cc9d0ad`（CI run 43103245820 的产物）

## 已完成

### P0 平台
- [x] 双屏 / ROM 加载 / 渲染 / 触屏按键 / 60fps
- [x] 存档读档（内存缓冲 + 文件，当前单槽 `state1.sav`）
- [x] ROM 列表（canonical 去重）、载入 ROM 移到设置页
- [x] 多指按键（pointerId 跟踪 + 真实坐标命中）
- [x] 后台常驻（前台服务 + WakeLock + 电池无限制）
- [x] TCP 桥 :55401（read/write/press/frame/status）
- [x] Python 客户端 `emu_bridge` + `memory/ra` 的 `EMU_BACKEND=native` 切换
- [x] 固定签名 + App 内 OTA（MENU → 更新）
- [x] 更新页显示版本号 / 构建时间 / 更新内容
- [x] OTA 下载校验（UA + APK 头）+ 进度条 + 安装未知应用引导
- [x] 加载失败重试（`mCoreFind` 竞态，4 次）
- [x] 重新加载 ROM（`if (core_) return true` 已去掉）

### 下屏
- [x] 布局改为「左侧内容 + 右侧竖排 Tab」：地图/队伍/背包/名字/图鉴/存档/设置/按键
- [x] 小地图面板（缺字段时沿用上次推送值；Kotlin 侧解析 `maps/*.json` 仍未做）
- [x] 战斗页（自动切换 + 双方血条 + 中文招式名），`battle_anim` + 4 秒滞回
- [x] 队伍列表显示宝可梦中文名（关东 151 名表 + PartyCrypto 解密）
- [x] 队伍详情内嵌内容区（不弹窗遮挡）
- [x] 敌方等级 / HP / 最大 HP（`GameState.enemyInfo()`）
- [x] 按键布局 A（L/R 肩键 + 方向键 + A/B + Start/Select 重排）
- [x] 加速 1x / 2x / 4x
- [x] **点击小地图前往**：Kotlin `MapWalker` 同图 BFS + 真按键（180ms/步），带单测
- [x] 后台推送常驻脚本 `start_push.sh`

### 架构
- [x] P1 插件化（`framework/GamePlugin` + `games/pokemon_firered` + `run_game.py` + 28 项离线测试）
- [x] B 方案数据/决策层 Kotlin 化（`native-emu/.../game/`：GameState / BattleDecider / SwitchDecider / MapWalker）
- [x] CI 跑 `:app:testDebugUnitTest`（Kotlin 单测 3 个文件）

## 2026-11-12 下屏重构（已完成）

- [x] A 按键改成底边常驻折叠条，战斗中也能开；`closeKeys()` 统一清掩码（`7a722ad`）
- [x] E OTA 更新说明保留换行、最多 8 行可滚动（`ad32231`）
- [x] B 常驻「当前地图」页 + 13 张地图打包进 assets + 战斗/地图自动切换（`37e6abd`）
- [x] C Tab 点两次关闭；「地图」Tab 换成整张城镇图（`6c824b8`）
- [x] D 队伍详情经验/升级阈值/进度条，成长类型从 ROM BaseStats 读（`0ac6009`）
- [x] 电池存档落盘（`mCoreAutoloadSave`，落 ROM 同目录）—— **2026-11-12 实机验证通过**

## 待办（按优先级）

### P1 · 下屏
- [ ] **存档卡槽**（方案已定，未做）：3 个槽位，显示保存时间 + 存档/读档/删除；文件 `state1-3.sav`；点存档直接写当前槽
- [x] **队伍详情字段补全**：属性、4 招式 + PP、经验与升级进度（`0ac6009`）
- [ ] **行走路径提示**：点地图先画路线（黄线 + 终点）+ 显示步数 +「开始走」按钮，替代现在点了就走

### P1 · 战斗
- [ ] **招式点击施放**（风险最高，方案已定）：
      `MOVE_CURSOR`(0x02023FFC，0左上/1右上/2左下/3右下) → 方向键序列 → 回读光标确认
      防护：执行前二次确认（`TURN_FLAG==2` 且光标读数一致），不一致就停

### P1 · 可观测性（按 docs/OBSERVABILITY.md 落地）
- [x] OTA 结构化日志（检查/下载进度/校验/安装，写 `/sdcard/Download/ota.log`）—— `aa126e0`
- [x] 安装结果回调日志（`PACKAGE_ADDED` / `REPLACED`，超时/失败也记）
- [x] 日志写入改异步（单线程队列，失败降级 logcat）
- [ ] 桥（connect/cmd 失败）与帧循环异常按规范补日志

### P2 · 寻路
- [ ] **A* 跨图移植**：`nav/pathfind` 的跨图逻辑搬到 Kotlin（同图 BFS 已完成）
- [ ] **实机对照**：Kotlin 决策 vs Python 版行为一致

### P3 · 长期
- [ ] 招式名补全（现在 55 条，完整 354 条缺数据源）
- [ ] 自动化开关（工具页，需决策层接入）
- [ ] 联机支持（GBA link cable，方案待调研）

## 结构债（考官 2026-11-12 发现）

- [ ] `state.py:269` 函数内 `import bdata` ↔ `bdata.py:4 from state import ...` —— 循环依赖，
      STRUCTURE §三 判定违规；现在靠延迟导入不炸，重构时必须拆（把共享常量提到 `platform/`）
- [ ] `MainActivity.kt` **963 行**（B/C/D 已完成，必须拆了）：拆成
      `ui/KeyPad.kt`、`ui/BattlePage.kt`、`ui/MapPage.kt`、`ui/SideTabs.kt`（P2）
- [ ] 按键状态清理统一走一个函数（`keysOpen=false` 时必须同时 `keys=0; EmuCore.setKeys(0)`），
      已在 A 提交里发现 Tab 路径漏清 → 见 INC-005

## 已清理（2026-11-12 05:35）

- [x] `MainActivity.kt` 补上 `androidx.compose.foundation.gestures.detectTapGestures` 的 import
- [x] 删掉 `GameState.kt` 末尾 `// build trigger 2026-11-12` 临时注释
- [x] `map_cache.txt` 移出版本库（已加 `.gitignore`，仍保留在本地）
- 空提交 `ff2cd3e`（chore 触发构建）还在历史里，不影响功能，不必处理
