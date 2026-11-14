# NativeEmu 待办

> 更新：2026-11-13（F2 招式点击施放已实现 `9c2fc63`、待真机结果；最近代码批次 A `8082f89`–E `188bbe9` + F2；见 `CHANGELOG v2026.11.12-4/-8`、`v2026.11.13-1`）
> 状态判断以代码为准：勾选过的项都在 `native-emu/` 里有实现。

## 当前阻塞（2026-11-12 05:35 已全部解除）

- [x] CI 编译失败：缺 `detectTapGestures` import + `KeyPadArea` 残留重复布局块（多一个 `}`）
- [x] Release 旧包：已删 `build-c7996e9`，新发 `build-cc9d0ad`（CI run 43103245820 的产物）

## 已完成

### P0 平台
- [x] 双屏 / ROM 加载 / 渲染 / 触屏按键 / 60fps
- [x] 存档读档（内存缓冲 + 文件；现为 **3 槽** `state1-3.sav`，见下屏「存档卡槽」）
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
- [x] P1 插件化（`framework/GamePlugin` + `games/pokemon_firered` + `run_game.py`；离线测试数量/结果见 `tools/test_results.json`）
- [x] B 方案数据/决策层 Kotlin 化（`native-emu/.../game/`：GameState / BattleDecider / SwitchDecider / MapWalker）
- [x] CI 跑 `:app:testDebugUnitTest`（Kotlin 单测 **10 个文件**；用例数与结果见 `tools/test_results.json`）

## 2026-11-12 下屏重构（已完成）

- [x] A 按键改成底边常驻折叠条，战斗中也能开；`closeKeys()` 统一清掩码（`7a722ad`）
- [x] E OTA 更新说明保留换行、最多 8 行可滚动（`ad32231`）
- [x] B 常驻「当前地图」页 + 13 张地图打包进 assets + 战斗/地图自动切换（`37e6abd`）
- [x] C Tab 点两次关闭；「地图」Tab 换成整张城镇图（`6c824b8`）
- [x] D 队伍详情经验/升级阈值/进度条，成长类型从 ROM BaseStats 读（`0ac6009`）
- [x] 电池存档落盘（`mCoreAutoloadSave`，落 ROM 同目录）—— **2026-11-12 实机验证通过**
- [x] 设置页「重置」（软复位）与「退出」（停服务 + 刷电池存档 + 退进程）—— `9cfd5d0`

## 待办（按优先级）

### P1 · 下屏
- [x] **存档卡槽**：3 个槽位（`state1-3.sav`），显示时间，存档/读取/删除，覆盖·读取·删除均二次确认
- [x] **队伍详情字段补全**：属性、4 招式 + PP、经验与升级进度（`0ac6009`）
- [x] **行走路径提示**：点格子先预览（黄线 + 终点 + 步数）+「开始走/取消」—— `ea576e9`（批次 D）；
      批次 E 起非战斗常驻页直接是整张城镇图、地图 Tab 置灰（`188bbe9`）；「停止条」用户决定不做

### P1 · 交互细节
- [x] 状态通道拆分：常驻状态（TCP/ROM 名）走 `statusBarState`，临时操作提示走 `statusText`（2.8 秒后消失），启动不再闪临时行 —— `8082f89`
- [x] 设置页「重置/退出」小屏可读性：改成整行按钮（沿用 BarButton）—— `8082f89`

### P1 · 战斗
- [x] **招式点击施放**（风险最高）：`MOVE_CURSOR`(0x02023FFC，0左上/1右上/2左下/3右下) → 方向键序列
      → 每步回读 + 二次确认 → 按 A；防护 fail-closed（`TURN_FLAG==2` 且 `MAIN_CURSOR==0`，任一不满足
      不按键；按 A 后回合未推进即停不重试）—— `9c2fc63`（F2）；限制：**需先按 A 展开招式菜单再点**
      （不做自动开菜单，主持 2026-11-13 拍板）；真机见 `HANDOFF.md` §二·七

### P1 · 可观测性（按 docs/OBSERVABILITY.md 落地）
- [x] OTA 结构化日志（检查/下载进度/校验/安装，写 `/sdcard/Download/ota.log`）—— `aa126e0`
- [x] 安装结果回调日志（`PACKAGE_ADDED` / `REPLACED`，超时/失败也记）
- [x] 日志写入改异步（单线程队列，失败降级 logcat）
- [x] 桥（connect/cmd 失败）与帧循环异常按规范补日志（`Nlog`，写 `emu_native.log`）—— `8082f89`

### P2 · 寻路
> **2026-11-14 17:3x 用户拍板：地图相关功能全部暂缓**（含下列两项；已实现的地图功能保持现状，不再加新交互控件 / 补采 / 对照）。
- [ ] **A* 跨图移植**（暂缓）：`nav/pathfind` 的跨图逻辑搬到 Kotlin（同图 BFS 已完成）
- [ ] **实机对照**（暂缓）：Kotlin 决策 vs Python 版行为一致

### P3 · 长期
- [ ] 招式名补全（现在 55 条，完整 354 条缺数据源）
- [ ] 自动化开关（工具页，需决策层接入）
- [ ] 联机支持（GBA link cable，方案待调研）

## 批次 A 遗留（2026-11-12，`8082f89` 合并时约定：不单独开构建，并入下一批）

- [x] `statusBarState` 拆成 bridge / rom 两个状态：桥失败不再被 ROM 名覆盖 —— `fdbf448`（批次 B）
- [x] `Nlog.throttlePass` 的 get→put 非原子 → 改 `ConcurrentHashMap.compute`，补并发单测 —— `fdbf448`
- [x] `emu.frame.stall` 的 recover 未节流 → enter/recover 共用 10s 窗口 —— `fdbf448`
- [x] 帧循环 `catch (Throwable)` → `catch (Exception)`，不吞 OOM —— `fdbf448`
- [x] **统一日志格式**：`Growth`/`MapData` 旧式行已改 `Nlog` event+k=v；`OBSERVABILITY.md` §五/§六
      已同步（`bridge.log` 停用说明）—— `2a0fbc7`（批次 C）

## 批次 B 遗留（2026-11-12，`fdbf448` 合并时约定：轻，并入下一批）

- [x] `emu.frame.stall` enter/recover 拆两个 key，各自 10s —— `2a0fbc7`（批次 C）
- [x] 并发单测 `join` 后补 `assertFalse(t.isAlive)` —— `2a0fbc7`
- [x] `lockCanvas`/`lockHardwareCanvas` 的 `catch (Throwable)` 收窄为 `Exception` —— `2a0fbc7`

## 批次 C 遗留（2026-11-12，`2a0fbc7`/`81cfb2b` 合并时约定：轻，并入下一批）

> 主持裁定：以下 3 条**不单开批次**，已并入批次 D 的第一个提交（同一次构建）——`cbbd1f9`。

- [x] `map.fallback ok=false` 限流：两条都改 `Nlog.warnThrottled`，key 分 `:ok`/`:fail` —— `cbbd1f9`
- [x] `map.fallback ok=true`、`growth.rom locate ok=true` 恢复 `WARN` 级 —— `cbbd1f9`
- [x] `Updater.kt` 旧式 `"WARN  "` 手拼串 → `Nlog.buildLine`（只 logcat）—— `cbbd1f9`

## 地图功能约束（2026-11-12 / 2026-11-14 用户决定）

> **2026-11-14 17:3x 用户拍板：地图相关功能全部暂缓**——包括 A\* 跨图补采 / UI 入口 / 实机对照、新交互控件、地图数据与可视化改进；已实现功能（小地图、点击前往、13 图 assets）**保持现状、不删不改**，除非用户另行点名。
> 此前（2026-11-12）：地图相关功能计划大改；在此之前只修 bug，不加新的交互控件（如行走停止条、路线编辑）。

## 批次 D 遗留（2026-11-12，`cbbd1f9`/`ea576e9` 合并时约定：1/3/4 并入下一批首提交；2 已由用户否掉）

- [x] `currentMapId()=="?"` 时拒绝「开始走」并提示「等地图数据」 —— `b6e8db3`（批次 E）
- [x] ~~点「开始走」后无「停止」入口~~ → **用户决定不做**（见上方「地图功能约束」：地图要大改，只修 bug）
      ~~可保留「停止」条…~~
- [x] 换图但没离开界面时旧预览不再预渲染（渲染前比对地图身份）—— `b6e8db3`
- [x] 提交措辞：改为「主源码无旧式 WARN 硬编码」—— `b6e8db3`

## 批次 E 遗留（2026-11-12，`b6e8db3`/`188bbe9`；主持裁定：1/3 并入下一批首提交，2 挂起等真机，4 仅记录）

- [ ] `tabPage == Page.MAP` 分支现已不可达（Tab 置灰、tabPage 只能由点击设置）→ 加「当前不可达，留待重做」
      注释，防后人误以为还在用（暂不删，地图要大改）
- [ ] ~~整图重绘性能~~ **挂起，等真机验证**：常驻页最多 ~2880 格、每 500ms 重绘，静态分析判不了；
      装机后看「地图页停着时 FPS 是否掉、滑动是否跟手」，掉了再优化（缓存底图、只画 overlay）
- [ ] 常驻页与 MAP Tab 两处 TownMapPage 参数块重复约 6 行 → 抽小组件减少漂移
- [x] ~~`TabsTest` 只覆盖 `isPageTabEnabled`~~ → 无 Compose 测试环境，接受；仅记录（主持裁定）

## 批次 F2 遗留（2026-11-13，`9c2fc63`；批次3 收尾 `97bb03c` 已清大部分）

- [x] 结构债（中）：`ui/BattleMoveAction.kt` 直接 `Memo.u8` 读内存 → 已下沉到 `game/` 适配层（`game/BattleMoveMenu.kt`），ui 只调用；新增离线单测
- [x] 单测缺口（中）：MoveCaster 复核 + 线程层清键/取消单测已补（Kotlin 单测 95→101→113）
- [x] `MainActivity.kt` 710 行超限 → 批次4 拆分至 **311 行**（拆出 `ui/EmuView`/`StatusParser`/`WalkControl`/`LocalStatus`）
- [x] 轻：A 后轮询未查 cancelled → 已加取消检查（取消即退出，不再空转记 WARN）
- [x] 轻：`MoveCaster.kt` 注释「MAIN_CURSOR 0=招式」与 `addresses.py` 措辞 → 已统一
- [x] 招式名表 56 条（含 232 金属爪，2026-11-14 补全并脚本重生成；原缺 232 显示 `#232` 的问题已修）
- [ ] **仍遗留（A* 跨图）**：6 图缺 assets → 当前 5 图连通域可用；无高度层；`side` 语义待真机；本构建无 UI 入口，真机未覆盖（仅库+单测/CI）
- 真机：F2 `build-9c2fc63` 2026-11-13 通过（2 场野生战 4 招）；MainActivity 拆分后 `build-5bbe4f4` 2026-11-13 14:0x UI 冒烟通过；批次 A–E 回归记录见 `HANDOFF.md` / `BATCHES.md`

## 结构债（考官 2026-11-12 发现）

- [x] `state.py:269` 函数内 `import bdata` ↔ `bdata.py:4` 循环依赖 → 抽出 `bdata_shared.py`
      （纯解码 `mon_from_bytes`/`party_species`，地址只从 `addresses.py` 取）；`state`/`bdata` 都不再互相 import，
      新增 `test_bdata_shared.py`，Python 测试 29/29 —— `81cfb2b`（批次 C）
- [x] `MainActivity.kt` 拆分：963 → **536 行**，已拆出 `ui/KeyPad`、`ui/BattlePage`、`ui/MapPage`、`ui/Tabs`、`ui/Theme`、`ui/Pages`、`ui/SaveSlots`
      （剩 `EmuView`/`parseStatus`/`walkTo` 可继续迁，未做；**F2 后现 710 行，仍超 500 行上限**，见上「批次 F2 遗留」）
- [x] 按键状态清理统一走 `closeKeys()`（`keysOpen=false` 同时 `keys=0; EmuCore.setKeys(0)` 并取消
      `WalkControl` 代际）：点 Tab / 载入 ROM / 收按键面板三条路径都已走它（MainActivity.kt:392/424/453）

## 已清理（2026-11-12 05:35）

- [x] `MainActivity.kt` 补上 `androidx.compose.foundation.gestures.detectTapGestures` 的 import
- [x] 删掉 `GameState.kt` 末尾 `// build trigger 2026-11-12` 临时注释
- [x] `map_cache.txt` 移出版本库（已加 `.gitignore`，仍保留在本地）
- 空提交 `ff2cd3e`（chore 触发构建）还在历史里，不影响功能，不必处理
