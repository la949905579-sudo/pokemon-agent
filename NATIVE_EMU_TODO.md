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

## 待办
- [ ] 战斗页：检测到战斗自动切下屏（4 招式 + 换人/背包/逃跑）
- [ ] 队伍名字：补 species → 中文名对照表
- [ ] 小地图美化：按真实地图排列（现在是 6 个占位方块）
- [ ] OTA 首次安装需允许「安装未知应用」的引导提示
- [ ] 加速功能（1x/2x/4x）
- [ ] 自动化开关（工具页，需要 Python 端配合）
