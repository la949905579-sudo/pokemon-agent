# NativeEmu 待办

> 更新：2026-11-12 05:20（与 `git log` / `CHANGELOG v2026.11.12-1` 对齐）
> 状态判断以代码为准：勾选过的项都在 `native-emu/` 里有实现。

## 当前阻塞（交接第一件事）

- [ ] **CI 编译红**：`MainActivity.kt:358` 用了 `detectTapGestures`，但 import 区没有
      `androidx.compose.foundation.gestures.detectTapGestures`。
      补上这一行再推；如果还红，按日志 `e: file:///home/runner/…` 继续找（可能不止一处）。
- [ ] **Release 是旧包**：`build-d0bd1c3` 里的 APK 实际是 11-11 19:21 的成功产物（11,486,833 B），
      标签和内容不符。等 CI 绿了重发，别用 App 内 OTA。

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
- [x] 小地图面板（数据缓存，推送不再卡）
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

## 待办（按优先级）

### P1 · 下屏
- [ ] **存档卡槽**（方案已定）：3 个槽位，显示保存时间 + 存档/读档/删除；文件 `state1-3.sav`；点存档直接写当前槽
- [ ] **队伍详情字段补全**：属性（`SPECIES_TYPES` 生成到 Kotlin）、4 招式 + PP、经验
- [ ] **行走路径提示**：点地图先画路线（黄线 + 终点）+ 显示步数 +「开始走」按钮，替代现在点了就走

### P1 · 战斗
- [ ] **招式点击施放**（风险最高，方案已定）：
      `MOVE_CURSOR`(0x02023FFC，0左上/1右上/2左下/3右下) → 方向键序列 → 回读光标确认
      防护：执行前二次确认（`TURN_FLAG==2` 且光标读数一致），不一致就停

### P2 · 寻路
- [ ] **A* 跨图移植**：`nav/pathfind` 的跨图逻辑搬到 Kotlin（同图 BFS 已完成）
- [ ] **实机对照**：Kotlin 决策 vs Python 版行为一致

### P3 · 长期
- [ ] 招式名补全（现在 55 条，完整 354 条缺数据源）
- [ ] 自动化开关（工具页，需决策层接入）
- [ ] 联机支持（GBA link cable，方案待调研）

## 已知脏点（可顺手清）

- `native-emu/.../game/GameState.kt` 末尾有 `// build trigger 2026-11-12` 的临时注释（22f6ded 留下的）
- `map_cache.txt` 被纳入了版本库，每次推送都在变，属于运行缓存
- 空提交 `87c3323`（chore 触发构建）在历史里，不影响功能
