# NativeEmu 待办

> 更新：2026-11-11 17:10

## 已完成
- [x] P0 双屏 / ROM 加载 / 渲染 / 触屏按键 / 60fps
- [x] 存档读档（内存缓冲 + 文件）
- [x] ROM 列表（canonical 去重）
- [x] 多指按键（pointerId 跟踪 + 真实坐标命中）
- [x] 后台常驻（前台服务 + WakeLock + 电池无限制）
- [x] TCP 桥 :55401（read/write/press/frame/status）
- [x] Python 客户端 emu_bridge + memory/ra 的 EMU_BACKEND=native 切换
- [x] 下屏面板（小地图 / 菜单网格 / 日志 / 按键页）
- [x] 固定签名 + App 内 OTA（MENU → 更新）
- [x] 重新加载 ROM（`if (core_) return true` 导致，已去掉，commit 60ea7ea）
- [x] ROM 列表打开时底部 Tab 无法切换（showRoms 未清）
- [x] 加载失败重试（mCoreFind 竞态，4 次）
- [x] 更新页显示版本号 / 构建时间 / 更新内容（81a8cea）
- [x] OTA 下载校验（UA + APK 头，9ea1b11）
- [x] 战斗页（自动切换 + 双方血条 + 中文招式名）
- [x] 加速 1x/2x/4x
- [x] 后台推送常驻脚本 start_push.sh
- [x] P1 插件化（GamePlugin + Pokemon 插件 + runner + 实跑）

## 待办（按优先级）

### P0 · 下屏打磨（近期，可直接做）
- [ ] **敌方血量**：战斗结构偏移还没搬（`EN_BATTLE` 的 hp/mhp），纯数据
- [ ] **队伍名字**：species → 中文名表（151 只），显示在队伍列表
- [ ] **队伍详情**：点队伍里的精灵 → 卡片页（等级/HP/属性/招式）
- [ ] **小地图**：Kotlin 读 `maps/*.json` 并解析 tiles（现在本地状态没生成 minimap）
- [ ] **OTA 首次安装引导**：提示「安装未知应用」权限

### P1 · 战斗页增强（风险中等）
- [ ] **招式点击施放**：点招式名 → 读 `MOVE_CURSOR` → 计算方向键序列 → 发 press
  - 风险：光标读错会点错招，需先做实机验证
  - 过渡方案：先保留按键区，点击只做提示

### P2 · B 方案收尾（Kotlin 重写）
- [ ] **寻路/地图决策**：A*（nav/pathfind）移植到 Kotlin
- [ ] **实机对照**：Kotlin 决策 vs Python 版行为一致

### P3 · 长期
- [ ] 招式名补全（现在 55 条，完整 354 条缺数据源）
- [ ] 自动化开关（工具页，需决策层接入）
- [ ] 联机支持（GBA link cable，方案待调研）
